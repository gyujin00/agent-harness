from __future__ import annotations

import sys
from pathlib import Path

import pytest

from harness_runtime.gates import UnsafeCommandError, run_gate, run_gates


def python_command(source: str) -> str:
    escaped = source.replace('"', '\\"')
    return f'{sys.executable} -c "{escaped}"'


def test_gate_captures_success_output(tmp_path: Path) -> None:
    result = run_gate(python_command("print('gate-ok')"), tmp_path, 5)

    assert result.passed is True
    assert result.exit_code == 0
    assert result.stdout.strip() == "gate-ok"
    assert result.timed_out is False


def test_gate_nonzero_exit_is_failure(tmp_path: Path) -> None:
    result = run_gate(python_command("raise SystemExit(7)"), tmp_path, 5)

    assert result.passed is False
    assert result.exit_code == 7
    assert result.timed_out is False


def test_gate_timeout_is_failure(tmp_path: Path) -> None:
    result = run_gate(
        python_command("import time; time.sleep(2)"),
        tmp_path,
        timeout_seconds=1,
    )

    assert result.passed is False
    assert result.timed_out is True
    assert result.exit_code is None


@pytest.mark.parametrize(
    "command",
    [
        "python check.py | tee result.txt",
        "python check.py && echo pass",
        "python check.py > result.txt",
        "python check.py; echo pass",
        "python $(get-command.py)",
    ],
)
def test_gate_rejects_shell_control_operators(
    command: str, tmp_path: Path
) -> None:
    with pytest.raises(UnsafeCommandError):
        run_gate(command, tmp_path, 5)


def test_run_gates_stops_after_first_failure(tmp_path: Path) -> None:
    results = run_gates(
        (
            python_command("raise SystemExit(2)"),
            python_command("print('must-not-run')"),
        ),
        tmp_path,
        timeout_seconds=5,
    )

    assert len(results) == 1
    assert results[0].exit_code == 2
