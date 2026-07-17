from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


ALLOWED_DOMAINS = frozenset({"backend", "frontend", "ai"})
ALLOWED_STATUSES = frozenset(
    {"todo", "in_progress", "in_verify", "done", "back_to_action"}
)
REQUIRED_FIELDS = frozenset(
    {
        "id",
        "sprint",
        "domain",
        "loop",
        "status",
        "worker",
        "max_attempts",
        "timeout_minutes",
        "editable_paths",
        "locked_paths",
        "verification_commands",
        "pr",
    }
)


class ContractError(ValueError):
    """Raised when a Task Contract cannot be trusted by the runtime."""


@dataclass(frozen=True)
class PullRequestPolicy:
    enabled: bool = False
    draft: bool = True


@dataclass(frozen=True)
class TaskContract:
    id: str
    sprint: str
    domain: str
    loop: Path
    status: str
    worker: str
    max_attempts: int
    timeout_minutes: int
    editable_paths: tuple[str, ...]
    locked_paths: tuple[str, ...]
    verification_commands: tuple[str, ...]
    pr: PullRequestPolicy
    path: Path
    body: str


def _split_frontmatter(text: str) -> tuple[str, str]:
    normalized = text.lstrip("\ufeff")
    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ContractError("Task Contract must start with YAML frontmatter")
    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ContractError("Task Contract YAML frontmatter is not closed") from exc
    frontmatter = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :]).lstrip()
    if not body:
        raise ContractError("Task Contract body must not be empty")
    return frontmatter, body


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{field} must be a mapping")
    return value


def _require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value.strip()


def _require_positive_int(data: dict[str, Any], field: str) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractError(f"{field} must be a positive integer")
    return value


def _require_string_list(
    data: dict[str, Any], field: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise ContractError(f"{field} must be {qualifier}")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ContractError(f"{field} must contain only non-empty strings")
    return tuple(item.strip() for item in value)


def _normalize_repo_path(value: str, field: str) -> str:
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ContractError(f"{field} path must stay inside the repository: {value}")
    cleaned = path.as_posix().removeprefix("./")
    if cleaned in {"", "."}:
        raise ContractError(f"{field} path must stay inside the repository: {value}")
    if value.endswith(("/", "\\")) and not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned


def _paths_overlap(left: str, right: str) -> bool:
    left_prefix = left.rstrip("/")
    right_prefix = right.rstrip("/")
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def load_task_contract(path: Path, root: Path) -> TaskContract:
    root = root.resolve()
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ContractError(f"Task Contract must stay inside the repository: {path}")
    if not path.is_file():
        raise ContractError(f"Task Contract does not exist: {path}")

    frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    try:
        loaded = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        raise ContractError(f"invalid YAML frontmatter: {exc}") from exc
    data = _require_mapping(loaded, "frontmatter")

    missing = sorted(REQUIRED_FIELDS - data.keys())
    if missing:
        raise ContractError(f"missing required fields: {', '.join(missing)}")

    task_id = _require_string(data, "id")
    if not task_id.startswith("T-") or not task_id[2:].isdigit():
        raise ContractError("id must match T-<digits>")
    domain = _require_string(data, "domain")
    if domain not in ALLOWED_DOMAINS:
        raise ContractError(f"domain must be one of: {', '.join(sorted(ALLOWED_DOMAINS))}")
    status = _require_string(data, "status")
    if status not in ALLOWED_STATUSES:
        raise ContractError(f"unsupported task status: {status}")

    loop = Path(_normalize_repo_path(_require_string(data, "loop"), "loop"))
    loop_path = (root / loop).resolve()
    if not loop_path.is_relative_to(root) or not loop_path.is_file():
        raise ContractError(f"loop file does not exist inside the repository: {loop}")

    editable = tuple(
        _normalize_repo_path(item, "editable_paths")
        for item in _require_string_list(data, "editable_paths")
    )
    locked = tuple(
        _normalize_repo_path(item, "locked_paths")
        for item in _require_string_list(data, "locked_paths", allow_empty=True)
    )
    overlaps = sorted(
        f"{editable_path} <-> {locked_path}"
        for editable_path in editable
        for locked_path in locked
        if _paths_overlap(editable_path, locked_path)
    )
    if overlaps:
        raise ContractError(f"editable and locked paths overlap: {', '.join(overlaps)}")

    pr_data = _require_mapping(data["pr"], "pr")
    enabled = pr_data.get("enabled")
    draft = pr_data.get("draft")
    if not isinstance(enabled, bool) or not isinstance(draft, bool):
        raise ContractError("pr.enabled and pr.draft must be booleans")

    return TaskContract(
        id=task_id,
        sprint=_require_string(data, "sprint"),
        domain=domain,
        loop=loop,
        status=status,
        worker=_require_string(data, "worker"),
        max_attempts=_require_positive_int(data, "max_attempts"),
        timeout_minutes=_require_positive_int(data, "timeout_minutes"),
        editable_paths=editable,
        locked_paths=locked,
        verification_commands=_require_string_list(data, "verification_commands"),
        pr=PullRequestPolicy(enabled=enabled, draft=draft),
        path=path,
        body=body,
    )

