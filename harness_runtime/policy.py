from __future__ import annotations

from pathlib import PurePosixPath
from typing import Iterable

from .contracts import TaskContract


class PathPolicyViolation(ValueError):
    """Raised when a worker changes a path it does not own."""


class LockedSurfaceViolation(PathPolicyViolation):
    """Raised when a worker changes an evaluator or control-plane surface."""


def _normalize_changed_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or ".." in path.parts
        or normalized.startswith("/")
    ):
        raise PathPolicyViolation(
            f"changed path must stay inside the repository: {value}"
        )
    return path.as_posix().removeprefix("./")


def _matches(path: str, policy_path: str) -> bool:
    policy_prefix = policy_path.rstrip("/")
    return path == policy_prefix or path.startswith(policy_prefix + "/")


def validate_changed_paths(
    changed_paths: Iterable[str],
    contract: TaskContract,
) -> tuple[str, ...]:
    normalized = tuple(_normalize_changed_path(path) for path in changed_paths)
    locked = tuple(
        path
        for path in normalized
        if any(_matches(path, policy_path) for policy_path in contract.locked_paths)
    )
    if locked:
        raise LockedSurfaceViolation(
            f"locked surfaces were changed: {', '.join(sorted(locked))}"
        )

    outside = tuple(
        path
        for path in normalized
        if not any(_matches(path, policy_path) for policy_path in contract.editable_paths)
    )
    if outside:
        raise PathPolicyViolation(
            f"paths outside editable surfaces were changed: {', '.join(sorted(outside))}"
        )
    return normalized

