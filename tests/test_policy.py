from __future__ import annotations

from pathlib import Path

import pytest

from harness_runtime.contracts import load_task_contract
from harness_runtime.policy import (
    LockedSurfaceViolation,
    PathPolicyViolation,
    validate_changed_paths,
)

from test_contracts import write_project


def make_contract(tmp_path: Path):
    return load_task_contract(write_project(tmp_path), tmp_path)


def test_allows_changes_inside_editable_paths(tmp_path: Path) -> None:
    contract = make_contract(tmp_path)

    result = validate_changed_paths(
        ["backend/api.py", "tests/backend/test_api.py"],
        contract,
    )

    assert result == ("backend/api.py", "tests/backend/test_api.py")


def test_locked_path_change_is_rejected(tmp_path: Path) -> None:
    contract = make_contract(tmp_path)

    with pytest.raises(LockedSurfaceViolation, match="eval/thresholds.yaml"):
        validate_changed_paths(
            ["backend/api.py", "eval/thresholds.yaml"],
            contract,
        )


def test_change_outside_editable_paths_is_rejected(tmp_path: Path) -> None:
    contract = make_contract(tmp_path)

    with pytest.raises(PathPolicyViolation, match="README.md"):
        validate_changed_paths(["README.md"], contract)


def test_parent_traversal_is_rejected(tmp_path: Path) -> None:
    contract = make_contract(tmp_path)

    with pytest.raises(PathPolicyViolation, match="inside the repository"):
        validate_changed_paths(["../outside.py"], contract)

