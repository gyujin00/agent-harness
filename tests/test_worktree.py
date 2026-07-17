from __future__ import annotations

import subprocess
from pathlib import Path

from harness_runtime.contracts import load_task_contract
from harness_runtime.worktree import WorktreeManager

from test_contracts import write_project


def git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git",) + arguments,
        cwd=root,
        capture_output=True,
        text=True,
        shell=False,
        check=True,
    )


def test_worktree_uses_domain_task_branch(tmp_path: Path) -> None:
    contract = load_task_contract(write_project(tmp_path), tmp_path)
    manager = WorktreeManager(tmp_path)

    spec = manager.spec(contract, "20260717-120000")

    assert spec.branch == "backend/T-002-20260717-120000"
    assert spec.path == tmp_path / ".worktrees" / "backend-T-002-20260717-120000"
    assert spec.created is False


def test_worktree_run_id_is_sanitized(tmp_path: Path) -> None:
    contract = load_task_contract(write_project(tmp_path), tmp_path)
    manager = WorktreeManager(tmp_path)

    spec = manager.spec(contract, "run id/with:punctuation")

    assert spec.branch == "backend/T-002-run-id-with-punctuation"
    assert spec.path.name == "backend-T-002-run-id-with-punctuation"


def test_create_and_inspect_real_isolated_worktree(tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "harness-test@example.com")
    git(tmp_path, "config", "user.name", "Harness Test")
    (tmp_path / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    task = write_project(tmp_path)
    git(tmp_path, "add", "--all")
    git(tmp_path, "commit", "-m", "fixture")
    contract = load_task_contract(task, tmp_path)
    manager = WorktreeManager(tmp_path)

    worktree = manager.create(contract, "integration")
    (worktree.path / "backend").mkdir()
    (worktree.path / "backend" / "api.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    assert worktree.created is True
    assert worktree.path.is_dir()
    assert git(worktree.path, "branch", "--show-current").stdout.strip() == (
        "backend/T-002-integration"
    )
    assert manager.changed_files(worktree) == ("backend/api.py",)
