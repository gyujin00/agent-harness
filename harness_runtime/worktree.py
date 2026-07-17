from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .contracts import TaskContract


class WorktreeError(RuntimeError):
    """Raised when the runtime cannot create or inspect an isolated worktree."""


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str
    base_sha: str
    created: bool


def _slug(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-._")
    return sanitized or "run"


class WorktreeManager:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def spec(self, contract: TaskContract, run_id: str) -> Worktree:
        suffix = _slug(run_id)
        stem = f"{contract.domain}-{contract.id}-{suffix}"
        return Worktree(
            path=self.root / ".worktrees" / stem,
            branch=f"{contract.domain}/{contract.id}-{suffix}",
            base_sha="",
            created=False,
        )

    def _git(
        self,
        arguments: tuple[str, ...],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ("git",) + arguments,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise WorktreeError(f"git {' '.join(arguments)} failed: {detail}")
        return completed

    def create(self, contract: TaskContract, run_id: str) -> Worktree:
        specification = self.spec(contract, run_id)
        ignored = subprocess.run(
            ("git", "check-ignore", "-q", ".worktrees/probe"),
            cwd=self.root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        if ignored.returncode != 0:
            raise WorktreeError(".worktrees must be ignored before runtime use")
        base_sha = self._git(("rev-parse", "HEAD")).stdout.strip()
        self._git(
            (
                "worktree",
                "add",
                str(specification.path),
                "-b",
                specification.branch,
                base_sha,
            )
        )
        return Worktree(
            path=specification.path,
            branch=specification.branch,
            base_sha=base_sha,
            created=True,
        )

    def changed_files(self, worktree: Worktree) -> tuple[str, ...]:
        commands = (
            ("diff", "--name-only", f"{worktree.base_sha}...HEAD"),
            ("diff", "--name-only"),
            ("diff", "--cached", "--name-only"),
            ("ls-files", "--others", "--exclude-standard"),
        )
        changed: set[str] = set()
        for command in commands:
            output = self._git(command, cwd=worktree.path).stdout
            changed.update(
                line.strip().replace("\\", "/")
                for line in output.splitlines()
                if line.strip()
            )
        return tuple(sorted(changed))

    def diff_summary(self, worktree: Worktree) -> str:
        tracked = self._git(
            ("diff", "--stat", worktree.base_sha),
            cwd=worktree.path,
        ).stdout.strip()
        untracked = self._git(
            ("ls-files", "--others", "--exclude-standard"),
            cwd=worktree.path,
        ).stdout.strip()
        sections = []
        if tracked:
            sections.append(tracked)
        if untracked:
            sections.append("UNTRACKED:\n" + untracked)
        return "\n\n".join(sections) or "No diff"
