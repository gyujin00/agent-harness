from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .contracts import TaskContract
from .worktree import Worktree


class PullRequestError(RuntimeError):
    """Raised when a verified branch cannot be promoted to a Draft PR."""


Executor = Callable[
    [tuple[str, ...], Path],
    subprocess.CompletedProcess[str],
]


def _default_executor(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )


class PullRequestManager:
    """Commit, push, and create a Draft PR. Merge is intentionally absent."""

    def __init__(self, executor: Executor = _default_executor) -> None:
        self.executor = executor

    @staticmethod
    def build_create_command(
        title: str,
        body_file: Path,
    ) -> tuple[str, ...]:
        return (
            "gh",
            "pr",
            "create",
            "--draft",
            "--title",
            title,
            "--body-file",
            str(body_file),
        )

    def _run(self, command: tuple[str, ...], cwd: Path) -> str:
        completed = self.executor(command, cwd)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise PullRequestError(
                f"{' '.join(command[:3])} failed: {detail or 'unknown error'}"
            )
        return completed.stdout.strip()

    def create_draft(
        self,
        worktree: Worktree,
        contract: TaskContract,
        evidence_dir: Path,
    ) -> str:
        if not contract.pr.enabled or not contract.pr.draft:
            raise PullRequestError("Task Contract does not allow a Draft PR")
        summary = evidence_dir / "summary.md"
        if not summary.is_file():
            raise PullRequestError("run summary is missing")

        self._run(("git", "add", "--all"), worktree.path)
        self._run(
            (
                "git",
                "commit",
                "-m",
                f"feat({contract.domain}): complete {contract.id}",
            ),
            worktree.path,
        )
        self._run(
            ("git", "push", "-u", "origin", worktree.branch),
            worktree.path,
        )
        title_line = next(
            (
                line.lstrip("# ").strip()
                for line in contract.body.splitlines()
                if line.startswith("#")
            ),
            contract.id,
        )
        url = self._run(
            self.build_create_command(
                f"[{contract.id}] {title_line}",
                summary,
            ),
            worktree.path,
        )
        if not url.startswith(("https://", "http://")):
            raise PullRequestError(f"gh did not return a PR URL: {url!r}")
        return url

