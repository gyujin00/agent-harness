from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from harness_runtime.contracts import TaskContract, load_task_contract
from harness_runtime.gates import GateResult
from harness_runtime.orchestrator import LoopRunner
from harness_runtime.providers.base import AgentIssue, AgentResult, AgentRole
from harness_runtime.providers.fake import FakeProvider
from harness_runtime.state import RunStatus
from harness_runtime.worktree import Worktree

from test_contracts import VALID_TASK, write_project


class FakeWorkspaceManager:
    def __init__(self, root: Path, changed: tuple[str, ...] = ("backend/api.py",)):
        self.root = root
        self.changed = changed

    def create(self, contract: TaskContract, run_id: str) -> Worktree:
        return Worktree(
            path=self.root,
            branch=f"{contract.domain}/{contract.id}-{run_id}",
            base_sha="base",
            created=False,
        )

    def changed_files(self, worktree: Worktree) -> tuple[str, ...]:
        return self.changed

    def diff_summary(self, worktree: Worktree) -> str:
        return "\n".join(f"M {path}" for path in self.changed)


def passing_gates(commands, cwd, timeout_seconds):
    return (
        GateResult(
            command=("fake-gate",),
            exit_code=0,
            stdout="passed",
            stderr="",
            timed_out=False,
        ),
    )


def prepare_runtime_project(
    tmp_path: Path,
    *,
    max_attempts: int = 3,
) -> tuple[TaskContract, Path]:
    task_text = VALID_TASK.replace(
        "max_attempts: 3",
        f"max_attempts: {max_attempts}",
    ).replace(
        "백엔드 계약을 구현한다.",
        "백엔드 계약을 구현한다. 기준은 `requirements/prd.md`다.",
    )
    task = write_project(tmp_path, task_text)
    (tmp_path / "AGENTS.md").write_text("# Constitution\n", encoding="utf-8")
    (tmp_path / "agent-specs").mkdir()
    (tmp_path / "agent-specs" / "backend-worker.spec.md").write_text(
        "# Worker\n", encoding="utf-8"
    )
    (tmp_path / "agent-specs" / "verifier.spec.md").write_text(
        "# Verifier\n", encoding="utf-8"
    )
    (tmp_path / "harness").mkdir()
    for name in (
        "permissions.policy.md",
        "worktree.md",
        "verification.policy.md",
        "connectors.md",
    ):
        (tmp_path / "harness" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "harness" / "schemas").mkdir()
    for name in ("agent-result.schema.json", "verifier-report.schema.json"):
        (tmp_path / "harness" / "schemas" / name).write_text(
            '{"type":"object"}',
            encoding="utf-8",
        )
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "prd.md").write_text("# PRD\n", encoding="utf-8")
    return load_task_contract(task, tmp_path), task


def event_statuses(root: Path, run_id: str) -> list[str]:
    path = root / "docs" / "runs" / run_id / "events.jsonl"
    return [
        json.loads(line)["status"]
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def runner(
    root: Path,
    worker: FakeProvider,
    verifier: FakeProvider,
    changed: tuple[str, ...] = ("backend/api.py",),
) -> LoopRunner:
    return LoopRunner(
        root=root,
        worker_provider=worker,
        verifier_provider=verifier,
        workspace_manager=FakeWorkspaceManager(root, changed),
        gate_runner=passing_gates,
    )


def test_loop_retries_failed_verification_then_records_pass(tmp_path: Path) -> None:
    contract, _ = prepare_runtime_project(tmp_path)
    worker = FakeProvider(
        [AgentResult.pass_("attempt-1"), AgentResult.pass_("attempt-2")]
    )
    verifier = FakeProvider(
        [
            AgentResult.fail(
                "missing contract",
                issues=(
                    AgentIssue(
                        gate="api-contract",
                        evidence=("expected 409, got 200",),
                        required_correction="return 409",
                        files=("backend/api.py",),
                    ),
                ),
            ),
            AgentResult.pass_("verified", ("fake-gate passed",)),
        ]
    )

    outcome = runner(tmp_path, worker, verifier).run(
        contract,
        create_pr=False,
        run_id="run-retry-pass",
    )

    assert outcome.status is RunStatus.COMPLETE
    assert outcome.attempts == 2
    assert event_statuses(tmp_path, outcome.run_id) == [
        "preparing",
        "in_progress",
        "in_verify",
        "back_to_action",
        "in_progress",
        "in_verify",
        "recording",
        "complete",
    ]
    assert len(worker.requests) == 2
    assert len(verifier.requests) == 2
    assert worker.requests[0].role is AgentRole.WORKER
    assert verifier.requests[0].role is AgentRole.VERIFIER
    assert "return 409" in worker.requests[1].prompt
    assert "attempt-1" not in verifier.requests[0].prompt


def test_loop_escalates_after_max_attempts(tmp_path: Path) -> None:
    contract, _ = prepare_runtime_project(tmp_path, max_attempts=2)
    worker = FakeProvider(
        [AgentResult.pass_("attempt-1"), AgentResult.pass_("attempt-2")]
    )
    verifier = FakeProvider(
        [AgentResult.fail("same defect"), AgentResult.fail("same defect")]
    )

    outcome = runner(tmp_path, worker, verifier).run(
        contract,
        create_pr=False,
        run_id="run-exhausted",
    )

    assert outcome.status is RunStatus.NEEDS_HUMAN
    assert outcome.attempts == 2
    assert event_statuses(tmp_path, outcome.run_id)[-1] == "needs_human"


def test_locked_surface_change_escalates_without_verifier(tmp_path: Path) -> None:
    contract, _ = prepare_runtime_project(tmp_path)
    worker = FakeProvider([AgentResult.pass_("changed evaluator")])
    verifier = FakeProvider([AgentResult.pass_("must not run")])

    outcome = runner(
        tmp_path,
        worker,
        verifier,
        changed=("backend/api.py", "eval/thresholds.yaml"),
    ).run(
        contract,
        create_pr=False,
        run_id="run-locked",
    )

    assert outcome.status is RunStatus.NEEDS_HUMAN
    assert len(verifier.requests) == 0


def test_worker_needs_human_stops_before_verification(tmp_path: Path) -> None:
    contract, _ = prepare_runtime_project(tmp_path)
    worker = FakeProvider([AgentResult.needs_human("missing product decision")])
    verifier = FakeProvider([AgentResult.pass_("must not run")])

    outcome = runner(tmp_path, worker, verifier).run(
        contract,
        create_pr=False,
        run_id="run-worker-blocked",
    )

    assert outcome.status is RunStatus.NEEDS_HUMAN
    assert len(verifier.requests) == 0
