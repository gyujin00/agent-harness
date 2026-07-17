from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Protocol, Sequence
from uuid import uuid4

from .context_pack import ContextPack, build_context_pack
from .contracts import TaskContract, load_task_contract
from .gates import GateResult, run_gates
from .policy import LockedSurfaceViolation, PathPolicyViolation, validate_changed_paths
from .providers.base import (
    AgentIssue,
    AgentRequest,
    AgentResult,
    AgentRole,
    Provider,
    ProviderError,
)
from .recorder import RunRecorder
from .state import RunStatus, next_status
from .worktree import Worktree, WorktreeError, WorktreeManager


GateRunner = Callable[
    [Sequence[str], Path, int],
    tuple[GateResult, ...],
]


class WorkspaceManager(Protocol):
    def create(self, contract: TaskContract, run_id: str) -> Worktree: ...

    def changed_files(self, worktree: Worktree) -> tuple[str, ...]: ...

    def diff_summary(self, worktree: Worktree) -> str: ...


class PullRequestService(Protocol):
    def create_draft(
        self,
        worktree: Worktree,
        contract: TaskContract,
        evidence_dir: Path,
    ) -> str: ...


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    status: RunStatus
    attempts: int
    evidence_dir: Path
    worktree: Worktree
    pr_url: str | None = None


def _new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid4().hex[:8]}"


def _issue_dict(issue: AgentIssue) -> dict[str, object]:
    return issue.as_dict()


def _feedback_from_result(result: AgentResult, gate: str) -> tuple[dict[str, object], ...]:
    if result.issues:
        return tuple(_issue_dict(issue) for issue in result.issues)
    return (
        {
            "gate": gate,
            "evidence": list(result.evidence) or [result.summary],
            "required_correction": result.summary,
            "files": [],
        },
    )


def _gate_feedback(results: Sequence[GateResult]) -> tuple[dict[str, object], ...]:
    failed = next(result for result in results if not result.passed)
    evidence = []
    if failed.timed_out:
        evidence.append("verification command timed out")
    if failed.stdout.strip():
        evidence.append(failed.stdout.strip()[-2000:])
    if failed.stderr.strip():
        evidence.append(failed.stderr.strip()[-2000:])
    return (
        {
            "gate": "deterministic",
            "evidence": evidence or [f"exit code: {failed.exit_code}"],
            "required_correction": (
                "Make the locked verification command pass without changing "
                "the evaluator or Task Contract."
            ),
            "files": [],
        },
    )


class LoopRunner:
    def __init__(
        self,
        root: Path,
        worker_provider: Provider,
        verifier_provider: Provider,
        *,
        workspace_manager: WorkspaceManager | None = None,
        gate_runner: GateRunner = run_gates,
        worker_budget_usd: float | None = None,
        verifier_budget_usd: float | None = None,
        pull_request_manager: PullRequestService | None = None,
    ) -> None:
        self.root = root.resolve()
        self.worker_provider = worker_provider
        self.verifier_provider = verifier_provider
        self.workspace_manager = workspace_manager or WorktreeManager(self.root)
        self.gate_runner = gate_runner
        self.worker_budget_usd = worker_budget_usd
        self.verifier_budget_usd = verifier_budget_usd
        self.pull_request_manager = pull_request_manager

    @staticmethod
    def _advance(
        current: RunStatus,
        target: RunStatus,
        recorder: RunRecorder,
        actor: str,
        detail,
        *,
        evidence: Sequence[str] = (),
    ) -> RunStatus:
        status = next_status(current, target)
        recorder.append(status, actor, detail, evidence=evidence)
        return status

    def _request(
        self,
        *,
        role: AgentRole,
        contract: TaskContract,
        pack: ContextPack,
        worktree: Worktree,
        recorder: RunRecorder,
        attempt: int,
        extra_prompt: str = "",
    ) -> AgentRequest:
        schema_name = (
            "agent-result.schema.json"
            if role is AgentRole.WORKER
            else "verifier-report.schema.json"
        )
        prompt = pack.render(role.value)
        if extra_prompt:
            prompt += "\n\n" + extra_prompt
        prompt += (
            "\n\nRETURN CONTRACT:\nReturn JSON matching the supplied output schema. "
            "Activity reports or confidence statements do not count."
        )
        return AgentRequest(
            role=role,
            agent_name=contract.worker if role is AgentRole.WORKER else "verifier",
            prompt=prompt,
            workdir=worktree.path,
            output_schema=worktree.path / "harness" / "schemas" / schema_name,
            raw_output_dir=recorder.local_dir / f"attempt-{attempt}" / role.value,
            timeout_seconds=contract.timeout_minutes * 60,
            budget_usd=(
                self.worker_budget_usd
                if role is AgentRole.WORKER
                else self.verifier_budget_usd
            ),
        )

    def _retry_or_escalate(
        self,
        *,
        status: RunStatus,
        recorder: RunRecorder,
        attempt: int,
        contract: TaskContract,
        feedback: tuple[dict[str, object], ...],
    ) -> RunStatus:
        if attempt >= contract.max_attempts:
            return self._advance(
                status,
                RunStatus.NEEDS_HUMAN,
                recorder,
                "orchestrator",
                {
                    "reason": "max_attempts_exceeded",
                    "attempts": attempt,
                    "feedback": feedback,
                },
            )
        return self._advance(
            status,
            RunStatus.BACK_TO_ACTION,
            recorder,
            "orchestrator",
            {"attempt": attempt, "feedback": feedback},
        )

    @staticmethod
    def _write_evidence(
        recorder: RunRecorder,
        contract: TaskContract,
        pack: ContextPack,
        verifier_result: AgentResult,
        attempts: int,
        worktree: Worktree,
    ) -> None:
        (recorder.evidence_dir / "contract.md").write_text(
            contract.path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (recorder.evidence_dir / "context-manifest.json").write_text(
            json.dumps(
                [asdict(entry) for entry in pack.manifest],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        report = {
            "status": verifier_result.status,
            "summary": verifier_result.summary,
            "evidence": list(verifier_result.evidence),
            "issues": [_issue_dict(issue) for issue in verifier_result.issues],
            "session_id": verifier_result.session_id,
        }
        (recorder.evidence_dir / "verifier-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (recorder.evidence_dir / "summary.md").write_text(
            "\n".join(
                (
                    f"# Harness run {recorder.run_id}",
                    "",
                    f"- Task: {contract.id}",
                    f"- Branch: `{worktree.branch}`",
                    f"- Attempts: {attempts}",
                    f"- Verifier: {verifier_result.status}",
                    f"- Summary: {verifier_result.summary}",
                    "",
                )
            ),
            encoding="utf-8",
        )

    def run(
        self,
        contract: TaskContract,
        *,
        create_pr: bool,
        run_id: str | None = None,
    ) -> RunOutcome:
        run_id = run_id or _new_run_id()
        try:
            worktree = self.workspace_manager.create(contract, run_id)
        except WorktreeError as exc:
            worktree = Worktree(
                path=self.root,
                branch="",
                base_sha="",
                created=False,
            )
            recorder = RunRecorder(
                local_root=self.root / ".harness" / "runs",
                evidence_root=self.root / ".harness" / "evidence",
                run_id=run_id,
            )
            status = self._advance(
                RunStatus.QUEUED,
                RunStatus.BLOCKED,
                recorder,
                "harness",
                {"reason": "worktree_create_failed", "evidence": [str(exc)]},
            )
            return RunOutcome(
                run_id=run_id,
                status=status,
                attempts=0,
                evidence_dir=recorder.evidence_dir,
                worktree=worktree,
            )
        recorder = RunRecorder(
            local_root=self.root / ".harness" / "runs",
            evidence_root=worktree.path / "docs" / "runs",
            run_id=run_id,
        )
        status = RunStatus.QUEUED
        status = self._advance(
            status,
            RunStatus.PREPARING,
            recorder,
            "orchestrator",
            {
                "task": contract.id,
                "worker_provider": self.worker_provider.name,
                "verifier_provider": self.verifier_provider.name,
                "worktree": str(worktree.path),
            },
        )

        task_relative = contract.path.relative_to(self.root)
        active_contract = load_task_contract(
            worktree.path / task_relative,
            worktree.path,
        )
        feedback: tuple[dict[str, object], ...] = ()
        attempts = 0
        last_pack: ContextPack | None = None
        verifier_result: AgentResult | None = None
        pr_url: str | None = None

        while attempts < active_contract.max_attempts:
            attempts += 1
            last_pack = build_context_pack(
                worktree.path,
                active_contract,
                feedback=feedback,
            )
            status = self._advance(
                status,
                RunStatus.IN_PROGRESS,
                recorder,
                "worker",
                {"attempt": attempts, "provider": self.worker_provider.name},
            )
            worker_request = self._request(
                role=AgentRole.WORKER,
                contract=active_contract,
                pack=last_pack,
                worktree=worktree,
                recorder=recorder,
                attempt=attempts,
            )
            try:
                worker_result = self.worker_provider.run(worker_request)
            except ProviderError as exc:
                feedback = (
                    {
                        "gate": "worker-provider",
                        "evidence": [str(exc)],
                        "required_correction": "Return a valid structured worker result.",
                        "files": [],
                    },
                )
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue
            if worker_result.status == "needs_human":
                status = self._advance(
                    status,
                    RunStatus.NEEDS_HUMAN,
                    recorder,
                    "worker",
                    {
                        "attempt": attempts,
                        "summary": worker_result.summary,
                        "evidence": worker_result.evidence,
                    },
                )
                break
            if worker_result.status == "fail":
                feedback = _feedback_from_result(worker_result, "worker")
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue

            status = self._advance(
                status,
                RunStatus.IN_VERIFY,
                recorder,
                "verifier",
                {"attempt": attempts},
            )
            changed = self.workspace_manager.changed_files(worktree)
            if not changed:
                feedback = (
                    {
                        "gate": "artifact",
                        "evidence": ["no changed artifact was produced"],
                        "required_correction": (
                            "Produce a concrete change inside editable_paths; "
                            "a status report does not count."
                        ),
                        "files": [],
                    },
                )
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue
            try:
                validate_changed_paths(changed, active_contract)
            except LockedSurfaceViolation as exc:
                status = self._advance(
                    status,
                    RunStatus.NEEDS_HUMAN,
                    recorder,
                    "harness",
                    {"reason": "locked_surface_changed", "evidence": [str(exc)]},
                )
                break
            except PathPolicyViolation as exc:
                feedback = (
                    {
                        "gate": "path-policy",
                        "evidence": [str(exc)],
                        "required_correction": "Revert changes outside editable paths.",
                        "files": list(changed),
                    },
                )
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue

            gate_results = self.gate_runner(
                active_contract.verification_commands,
                worktree.path,
                active_contract.timeout_minutes * 60,
            )
            if not gate_results or not all(result.passed for result in gate_results):
                feedback = (
                    _gate_feedback(gate_results)
                    if gate_results
                    else (
                        {
                            "gate": "deterministic",
                            "evidence": ["no gate result was produced"],
                            "required_correction": "Run every configured gate.",
                            "files": [],
                        },
                    )
                )
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue

            gate_payload = [
                {
                    "command": list(result.command),
                    "exit_code": result.exit_code,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                    "timed_out": result.timed_out,
                }
                for result in gate_results
            ]
            verifier_request = self._request(
                role=AgentRole.VERIFIER,
                contract=active_contract,
                pack=last_pack,
                worktree=worktree,
                recorder=recorder,
                attempt=attempts,
                extra_prompt=(
                    "CHANGED_FILES:\n"
                    + json.dumps(list(changed), ensure_ascii=False)
                    + "\n\nDIFF_SUMMARY:\n"
                    + self.workspace_manager.diff_summary(worktree)
                    + "\n\nLOCKED_GATE_RESULTS:\n"
                    + json.dumps(gate_payload, ensure_ascii=False, indent=2)
                    + "\n\nAudit the artifact against the Task Contract and enumerated "
                    "failure modes. Do not modify code."
                ),
            )
            try:
                verifier_result = self.verifier_provider.run(verifier_request)
            except ProviderError as exc:
                verifier_result = AgentResult.fail(
                    "verifier provider failed",
                    (str(exc),),
                )
            if verifier_result.status == "needs_human":
                status = self._advance(
                    status,
                    RunStatus.NEEDS_HUMAN,
                    recorder,
                    "verifier",
                    {
                        "attempt": attempts,
                        "summary": verifier_result.summary,
                        "evidence": verifier_result.evidence,
                    },
                )
                break
            if verifier_result.status == "fail":
                feedback = _feedback_from_result(verifier_result, "verifier")
                status = self._retry_or_escalate(
                    status=status,
                    recorder=recorder,
                    attempt=attempts,
                    contract=active_contract,
                    feedback=feedback,
                )
                if status is RunStatus.NEEDS_HUMAN:
                    break
                continue

            status = self._advance(
                status,
                RunStatus.RECORDING,
                recorder,
                "orchestrator",
                {
                    "attempts": attempts,
                    "verifier_summary": verifier_result.summary,
                    "create_pr": create_pr,
                },
                evidence=verifier_result.evidence,
            )
            self._write_evidence(
                recorder,
                active_contract,
                last_pack,
                verifier_result,
                attempts,
                worktree,
            )
            if create_pr:
                if self.pull_request_manager is None:
                    status = self._advance(
                        status,
                        RunStatus.NEEDS_HUMAN,
                        recorder,
                        "orchestrator",
                        {"reason": "draft_pr_manager_not_configured"},
                    )
                    break
                try:
                    pr_url = self.pull_request_manager.create_draft(
                        worktree,
                        active_contract,
                        recorder.evidence_dir,
                    )
                except Exception as exc:
                    status = self._advance(
                        status,
                        RunStatus.NEEDS_HUMAN,
                        recorder,
                        "orchestrator",
                        {
                            "reason": "draft_pr_creation_failed",
                            "evidence": [str(exc)],
                        },
                    )
                    break
                status = self._advance(
                    status,
                    RunStatus.PR_READY,
                    recorder,
                    "orchestrator",
                    {"pr_url": pr_url, "merge": "human_only"},
                )
            else:
                status = self._advance(
                    status,
                    RunStatus.COMPLETE,
                    recorder,
                    "orchestrator",
                    {"reason": "verified_without_pr"},
                )
            break

        return RunOutcome(
            run_id=run_id,
            status=status,
            attempts=attempts,
            evidence_dir=recorder.evidence_dir,
            worktree=worktree,
            pr_url=pr_url,
        )
