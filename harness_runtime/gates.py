from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class UnsafeCommandError(ValueError):
    """Raised when a verification command requests shell interpretation."""


@dataclass(frozen=True)
class GateResult:
    command: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool

    @property
    def passed(self) -> bool:
        return not self.timed_out and self.exit_code == 0


def _has_shell_operator(command: str) -> bool:
    quote: str | None = None
    index = 0
    while index < len(command):
        character = command[index]
        if quote is not None:
            if character == quote and (index == 0 or command[index - 1] != "\\"):
                quote = None
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
            index += 1
            continue
        if character in {"|", ";", ">", "<", "`", "\n", "\r"}:
            return True
        if command.startswith(("&&", "$("), index):
            return True
        index += 1
    return False


def parse_command(command: str) -> tuple[str, ...]:
    if not command.strip():
        raise UnsafeCommandError("verification command must not be empty")
    if _has_shell_operator(command):
        raise UnsafeCommandError(
            f"verification command requires forbidden shell interpretation: {command}"
        )
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except ValueError as exc:
        raise UnsafeCommandError(f"invalid verification command quoting: {command}") from exc
    if os.name == "nt":
        tokens = [
            token[1:-1]
            if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}
            else token
            for token in tokens
        ]
    if not tokens:
        raise UnsafeCommandError("verification command must not be empty")
    return tuple(tokens)


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_gate(
    command: str | Sequence[str],
    cwd: Path,
    timeout_seconds: int,
) -> GateResult:
    arguments = (
        parse_command(command)
        if isinstance(command, str)
        else tuple(str(token) for token in command)
    )
    try:
        completed = subprocess.run(
            arguments,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return GateResult(
            command=arguments,
            exit_code=None,
            stdout=_text(exc.stdout),
            stderr=_text(exc.stderr),
            timed_out=True,
        )
    return GateResult(
        command=arguments,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        timed_out=False,
    )


def run_gates(
    commands: Sequence[str],
    cwd: Path,
    timeout_seconds: int,
) -> tuple[GateResult, ...]:
    results: list[GateResult] = []
    for command in commands:
        result = run_gate(command, cwd, timeout_seconds)
        results.append(result)
        if not result.passed:
            break
    return tuple(results)

