from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import yaml

from .config import RuntimeConfig, RuntimeConfigError, load_runtime_config
from .context_pack import ContextPack, ContextPackError, build_context_pack
from .contracts import ContractError, TaskContract, load_task_contract
from .orchestrator import LoopRunner
from .providers.base import AgentRequest, AgentRole
from .providers.claude import ClaudeProvider
from .providers.codex import CodexProvider
from .pull_request import PullRequestManager
from .state import RunStatus


PROVIDER_NAMES = ("claude", "codex")
LIVE_STATUSES = frozenset({"todo", "in_progress", "back_to_action"})


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harnessctl",
        description="Run governed Claude Code/Codex development loops.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check local CLI readiness without model calls.")
    validate = commands.add_parser("validate", help="Validate a Task Contract and context.")
    validate.add_argument("task")
    run = commands.add_parser("run", help="Run or preview one Task Contract.")
    run.add_argument("task")
    run.add_argument("--worker", choices=PROVIDER_NAMES, required=True)
    run.add_argument("--verifier", choices=PROVIDER_NAMES, required=True)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--create-pr", action="store_true")
    return parser


def _root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    completed = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        raise ContractError("run harnessctl inside a Git repository")
    return Path(completed.stdout.strip()).resolve()


def _task_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _provider(name: str):
    if name == "claude":
        return ClaudeProvider()
    if name == "codex":
        return CodexProvider()
    raise ContractError(f"unsupported provider: {name}")


def _validate_loop(root: Path, contract: TaskContract) -> None:
    try:
        loaded = yaml.safe_load((root / contract.loop).read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContractError(f"invalid loop YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ContractError("loop must be a mapping")
    action = loaded.get("action")
    verify = loaded.get("verify")
    record = loaded.get("record")
    if not isinstance(action, dict) or action.get("agent") != contract.worker:
        raise ContractError("loop action.agent must match Task Contract worker")
    if not isinstance(verify, dict) or verify.get("verifier") != "verifier":
        raise ContractError("loop verify.verifier must be the independent verifier")
    if not isinstance(record, dict) or record.get("required") is not True:
        raise ContractError("loop record.required must be true")
    trigger = loaded.get("trigger")
    trigger_items = trigger if isinstance(trigger, list) else [trigger]
    if not any(
        isinstance(item, dict) and item.get("type") == "human.goal"
        for item in trigger_items
    ):
        raise ContractError("first runtime release requires a human.goal trigger")


def _load_validated(
    root: Path,
    task_value: str,
) -> tuple[TaskContract, ContextPack]:
    contract = load_task_contract(_task_path(root, task_value), root)
    _validate_loop(root, contract)
    return contract, build_context_pack(root, contract)


def _doctor() -> int:
    required = ("git", "claude", "codex")
    optional = ("gh",)
    missing = []
    print(f"python: {sys.version.split()[0]} ({sys.executable})")
    for name in required + optional:
        location = shutil.which(name)
        state = location or "NOT FOUND"
        suffix = "" if name in required else " (optional until --create-pr)"
        print(f"{name}: {state}{suffix}")
        if name in required and location is None:
            missing.append(name)
    if missing:
        print(f"missing required tools: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("model calls: 0")
    return 0


def _redacted_command(command: tuple[str, ...]) -> str:
    display = list(command)
    if "--json-schema" in display:
        index = display.index("--json-schema") + 1
        display[index] = "<schema-json>"
    return subprocess.list2cmdline(display)


def _dry_run(
    root: Path,
    contract: TaskContract,
    pack: ContextPack,
    config: RuntimeConfig,
    worker_name: str,
    verifier_name: str,
    create_pr: bool,
) -> int:
    raw = root / ".harness" / "dry-run"
    requests = []
    for role, provider_name, agent_name, schema_name in (
        (
            AgentRole.WORKER,
            worker_name,
            contract.worker,
            "agent-result.schema.json",
        ),
        (
            AgentRole.VERIFIER,
            verifier_name,
            "verifier",
            "verifier-report.schema.json",
        ),
    ):
        request = AgentRequest(
            role=role,
            agent_name=agent_name,
            prompt=pack.render(role.value),
            workdir=root,
            output_schema=root / "harness" / "schemas" / schema_name,
            raw_output_dir=raw / role.value,
            timeout_seconds=contract.timeout_minutes * 60,
            budget_usd=config.budget(provider_name, role.value),
        )
        requests.append((provider_name, _provider(provider_name), request))

    print(f"task={contract.id}")
    print(f"worker={worker_name}")
    print(f"verifier={verifier_name}")
    print(f"max_attempts={contract.max_attempts}")
    print(f"timeout_minutes={contract.timeout_minutes}")
    print(f"create_pr={create_pr and contract.pr.enabled}")
    print("worktree: not created")
    print("model calls: 0")
    print("context:")
    for entry in pack.manifest:
        print(f"  - {entry.path} sha256={entry.sha256[:12]}")
    print("gates:")
    for command in contract.verification_commands:
        print(f"  - {command}")
    print("provider commands:")
    for name, provider, request in requests:
        print(f"  - {name}/{request.role.value}: "
              f"{_redacted_command(provider.build_command(request))}")
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    root: Path | None = None,
) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        project_root = _root(root)
        if args.command == "doctor":
            return _doctor()
        contract, pack = _load_validated(project_root, args.task)
        print(f"validated: {contract.id} ({contract.domain}, {contract.status})")
        if args.command == "validate":
            return 0

        config = load_runtime_config(project_root)
        if args.dry_run:
            return _dry_run(
                project_root,
                contract,
                pack,
                config,
                args.worker,
                args.verifier,
                args.create_pr,
            )
        if contract.status not in LIVE_STATUSES:
            raise ContractError(
                f"live run requires status todo/in_progress/back_to_action, "
                f"got {contract.status}"
            )
        if args.create_pr and not contract.pr.enabled:
            raise ContractError("Task Contract does not allow PR creation")

        worker = _provider(args.worker)
        verifier = _provider(args.verifier)
        loop = LoopRunner(
            root=project_root,
            worker_provider=worker,
            verifier_provider=verifier,
            worker_budget_usd=config.budget(args.worker, "worker"),
            verifier_budget_usd=config.budget(args.verifier, "verifier"),
            pull_request_manager=PullRequestManager() if args.create_pr else None,
        )
        outcome = loop.run(contract, create_pr=args.create_pr)
        print(
            f"run={outcome.run_id} status={outcome.status.value} "
            f"attempts={outcome.attempts}"
        )
        print(f"evidence={outcome.evidence_dir}")
        if outcome.pr_url:
            print(f"pr={outcome.pr_url}")
        return 0 if outcome.status in {RunStatus.COMPLETE, RunStatus.PR_READY} else 3
    except (
        ContractError,
        ContextPackError,
        RuntimeConfigError,
        OSError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def entrypoint() -> None:
    raise SystemExit(main())

