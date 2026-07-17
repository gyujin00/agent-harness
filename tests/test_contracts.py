from __future__ import annotations

from pathlib import Path

import pytest

from harness_runtime.contracts import ContractError, load_task_contract


VALID_TASK = """\
---
id: T-002
sprint: sprint-02
domain: backend
loop: loops/backend.loop.yaml
status: todo
worker: backend-worker
max_attempts: 3
timeout_minutes: 30
editable_paths:
  - backend/
  - tests/backend/
locked_paths:
  - eval/
  - harness/
  - plans/
verification_commands:
  - python -m pytest tests/backend -q
pr:
  enabled: true
  draft: true
---

# Task-002

## 목적
백엔드 계약을 구현한다.
"""


def write_project(tmp_path: Path, task_text: str = VALID_TASK) -> Path:
    (tmp_path / "loops").mkdir()
    (tmp_path / "loops" / "backend.loop.yaml").write_text(
        "action:\n  agent: backend-worker\n",
        encoding="utf-8",
    )
    (tmp_path / "plans").mkdir()
    task = tmp_path / "plans" / "task-002.md"
    task.write_text(task_text, encoding="utf-8")
    return task


def test_loads_valid_task_contract(tmp_path: Path) -> None:
    task = write_project(tmp_path)

    contract = load_task_contract(task, tmp_path)

    assert contract.id == "T-002"
    assert contract.domain == "backend"
    assert contract.loop == Path("loops/backend.loop.yaml")
    assert contract.editable_paths == ("backend/", "tests/backend/")
    assert contract.pr.enabled is True
    assert contract.pr.draft is True
    assert contract.body.startswith("# Task-002")


def test_rejects_task_without_frontmatter(tmp_path: Path) -> None:
    task = write_project(tmp_path, "# Task only\n")

    with pytest.raises(ContractError, match="YAML frontmatter"):
        load_task_contract(task, tmp_path)


def test_rejects_locked_editable_overlap(tmp_path: Path) -> None:
    task = write_project(
        tmp_path,
        VALID_TASK.replace(
            "locked_paths:\n  - eval/",
            "locked_paths:\n  - backend/",
        ),
    )

    with pytest.raises(ContractError, match="overlap"):
        load_task_contract(task, tmp_path)


def test_rejects_path_outside_repository(tmp_path: Path) -> None:
    task = write_project(
        tmp_path,
        VALID_TASK.replace("  - backend/", "  - ../outside/", 1),
    )

    with pytest.raises(ContractError, match="inside the repository"):
        load_task_contract(task, tmp_path)


def test_rejects_missing_loop_file(tmp_path: Path) -> None:
    task = write_project(
        tmp_path,
        VALID_TASK.replace("loops/backend.loop.yaml", "loops/missing.loop.yaml"),
    )

    with pytest.raises(ContractError, match="loop file"):
        load_task_contract(task, tmp_path)
