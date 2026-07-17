from __future__ import annotations

import shutil
from pathlib import Path

from harness_runtime.cli import main
from harness_runtime.config import load_runtime_config

from test_fail_retry_pass import prepare_runtime_project


def test_doctor_reports_installed_tools(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: f"C:/bin/{name}.exe",
    )

    exit_code = main(["doctor"], root=tmp_path)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "claude" in output
    assert "codex" in output
    assert "git" in output
    assert "gh" in output


def test_validate_accepts_governed_task_contract(
    tmp_path: Path,
    capsys,
) -> None:
    _, task = prepare_runtime_project(tmp_path)

    exit_code = main(["validate", str(task)], root=tmp_path)

    assert exit_code == 0
    assert "T-002" in capsys.readouterr().out


def test_validate_reports_contract_errors(
    tmp_path: Path,
    capsys,
) -> None:
    task = tmp_path / "task.md"
    task.write_text("# no contract\n", encoding="utf-8")

    exit_code = main(["validate", str(task)], root=tmp_path)

    assert exit_code == 2
    assert "YAML frontmatter" in capsys.readouterr().err


def test_live_run_rejects_completed_task(tmp_path: Path, capsys) -> None:
    _, task = prepare_runtime_project(tmp_path)
    text = task.read_text(encoding="utf-8").replace("status: todo", "status: done")
    task.write_text(text, encoding="utf-8")

    exit_code = main(
        [
            "run",
            str(task),
            "--worker",
            "codex",
            "--verifier",
            "claude",
        ],
        root=tmp_path,
    )

    assert exit_code == 2
    assert "done" in capsys.readouterr().err


def test_runtime_config_supplies_provider_specific_budgets(tmp_path: Path) -> None:
    harness = tmp_path / "harness"
    harness.mkdir()
    (harness / "runtime.yaml").write_text(
        """\
version: 1
providers:
  claude:
    worker_budget_usd: 4.5
    verifier_budget_usd: 1.5
  codex: {}
""",
        encoding="utf-8",
    )

    config = load_runtime_config(tmp_path)

    assert config.budget("claude", "worker") == 4.5
    assert config.budget("claude", "verifier") == 1.5
    assert config.budget("codex", "worker") is None
