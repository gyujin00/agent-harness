from __future__ import annotations

import subprocess
from pathlib import Path

from harness_runtime.contracts import load_task_contract
from harness_runtime.pull_request import PullRequestManager
from harness_runtime.worktree import Worktree

from test_contracts import write_project


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[str, ...], Path]] = []

    def __call__(
        self,
        command: tuple[str, ...],
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, cwd))
        stdout = "https://github.com/example/repo/pull/7\n" if command[:3] == (
            "gh",
            "pr",
            "create",
        ) else ""
        return subprocess.CompletedProcess(command, 0, stdout, "")


def test_pull_request_adapter_only_builds_draft_create(tmp_path: Path) -> None:
    manager = PullRequestManager()

    command = manager.build_create_command("title", tmp_path / "body.md")

    assert command[:3] == ("gh", "pr", "create")
    assert "--draft" in command
    assert "merge" not in command
    assert not hasattr(PullRequestManager, "merge")


def test_create_draft_commits_pushes_and_returns_url(tmp_path: Path) -> None:
    contract = load_task_contract(write_project(tmp_path), tmp_path)
    evidence = tmp_path / "docs" / "runs" / "run-1"
    evidence.mkdir(parents=True)
    (evidence / "summary.md").write_text("# Summary\n", encoding="utf-8")
    executor = RecordingExecutor()
    manager = PullRequestManager(executor=executor)
    worktree = Worktree(
        path=tmp_path,
        branch="backend/T-002-run-1",
        base_sha="base",
        created=True,
    )

    url = manager.create_draft(worktree, contract, evidence)

    assert url == "https://github.com/example/repo/pull/7"
    commands = [command for command, _ in executor.calls]
    assert commands[0] == ("git", "add", "--all")
    assert commands[1][:2] == ("git", "commit")
    assert commands[2] == (
        "git",
        "push",
        "-u",
        "origin",
        "backend/T-002-run-1",
    )
    assert commands[3][:3] == ("gh", "pr", "create")
    assert all("merge" not in command for command in commands)

