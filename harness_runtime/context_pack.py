from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import TaskContract


REFERENCE_PATTERN = re.compile(r"`([^`\r\n]+)`")


class ContextPackError(ValueError):
    """Raised when required governed context cannot be assembled."""


@dataclass(frozen=True)
class ContextEntry:
    path: str
    sha256: str


@dataclass(frozen=True)
class ContextPack:
    root: Path
    contract: TaskContract
    files: tuple[Path, ...]
    manifest: tuple[ContextEntry, ...]
    feedback: tuple[Mapping[str, Any], ...]

    def render(self, role: str) -> str:
        if role not in {"worker", "verifier"}:
            raise ValueError(f"unsupported context role: {role}")
        launch_prompt = self.root / "prompts" / f"{role}-launch.md"
        sections = [
            launch_prompt.read_text(encoding="utf-8").strip(),
            f"ROLE: {role}",
            f"TASK: {self.contract.id}",
            "Follow the project constitution and Task Contract. "
            "Return only evidence-backed results.",
        ]
        if self.feedback:
            sections.extend(
                (
                    "LATEST_VERIFIED_FEEDBACK:",
                    json.dumps(
                        list(self.feedback),
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    ),
                )
            )
        sections.append("CONTEXT_FILES:")
        for path in self.files:
            relative = path.relative_to(self.root).as_posix()
            if relative in {
                "prompts/worker-launch.md",
                "prompts/verifier-launch.md",
            }:
                continue
            sections.append(f"\n--- {relative} ---\n{path.read_text(encoding='utf-8')}")
        return "\n".join(sections)


def _required_paths(root: Path, contract: TaskContract) -> tuple[Path, ...]:
    return (
        root / "AGENTS.md",
        contract.path,
        root / contract.loop,
        root / "agent-specs" / f"{contract.worker}.spec.md",
        root / "agent-specs" / "verifier.spec.md",
        root / "harness" / "permissions.policy.md",
        root / "harness" / "worktree.md",
        root / "harness" / "verification.policy.md",
        root / "harness" / "connectors.md",
        root / "prompts" / "worker-launch.md",
        root / "prompts" / "verifier-launch.md",
    )


def _referenced_paths(root: Path, body: str) -> tuple[Path, ...]:
    paths: list[Path] = []
    for raw_reference in REFERENCE_PATTERN.findall(body):
        reference = raw_reference.strip().replace("\\", "/")
        if not reference or " " in reference or reference.startswith(("http://", "https://")):
            continue
        candidate = (root / reference).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            paths.append(candidate)
    return tuple(paths)


def build_context_pack(
    root: Path,
    contract: TaskContract,
    *,
    feedback: Sequence[Mapping[str, Any]] = (),
) -> ContextPack:
    root = root.resolve()
    required = tuple(path.resolve() for path in _required_paths(root, contract))
    missing = [path.relative_to(root).as_posix() for path in required if not path.is_file()]
    if missing:
        raise ContextPackError(f"required context files are missing: {', '.join(missing)}")

    candidates = required + _referenced_paths(root, contract.body)
    files = tuple(sorted(set(candidates), key=lambda path: path.relative_to(root).as_posix()))
    manifest = tuple(
        ContextEntry(
            path=path.relative_to(root).as_posix(),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in files
    )
    return ContextPack(
        root=root,
        contract=contract,
        files=files,
        manifest=manifest,
        feedback=tuple(feedback),
    )
