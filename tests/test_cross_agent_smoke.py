from __future__ import annotations

from pathlib import Path

import pytest

from harness_runtime.cli import main

from test_fail_retry_pass import prepare_runtime_project


@pytest.mark.parametrize(
    ("worker", "verifier"),
    [("claude", "codex"), ("codex", "claude")],
)
def test_dry_run_accepts_cross_provider_pairs(
    tmp_path: Path,
    worker: str,
    verifier: str,
    capsys,
) -> None:
    _, task = prepare_runtime_project(tmp_path)

    exit_code = main(
        [
            "run",
            str(task),
            "--worker",
            worker,
            "--verifier",
            verifier,
            "--dry-run",
        ],
        root=tmp_path,
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert f"worker={worker}" in output
    assert f"verifier={verifier}" in output
    assert "worktree: not created" in output
    assert "model calls: 0" in output

