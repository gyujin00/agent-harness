from __future__ import annotations

from pathlib import Path

from harness_runtime.contracts import load_task_contract
from harness_runtime.worktree import WorktreeManager

from test_contracts import write_project


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

