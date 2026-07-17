from __future__ import annotations

from pathlib import Path

from harness_runtime.context_pack import build_context_pack
from harness_runtime.contracts import load_task_contract

from test_contracts import VALID_TASK, write_project


def prepare_context_project(tmp_path: Path) -> Path:
    task = write_project(
        tmp_path,
        VALID_TASK.replace(
            "백엔드 계약을 구현한다.",
            "백엔드 계약을 구현한다. 기준은 `requirements/prd.md`다.",
        ),
    )
    (tmp_path / "AGENTS.md").write_text("# Constitution\n", encoding="utf-8")
    (tmp_path / "agent-specs").mkdir()
    (tmp_path / "agent-specs" / "backend-worker.spec.md").write_text(
        "# Backend worker\n", encoding="utf-8"
    )
    (tmp_path / "agent-specs" / "verifier.spec.md").write_text(
        "# Verifier\n", encoding="utf-8"
    )
    (tmp_path / "harness").mkdir()
    for name in (
        "permissions.policy.md",
        "worktree.md",
        "verification.policy.md",
        "connectors.md",
    ):
        (tmp_path / "harness" / name).write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "prd.md").write_text("# PRD\n", encoding="utf-8")
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "worker-launch.md").write_text(
        "WORKER LAUNCH CONTRACT\n",
        encoding="utf-8",
    )
    (tmp_path / "prompts" / "verifier-launch.md").write_text(
        "VERIFIER LAUNCH CONTRACT\n",
        encoding="utf-8",
    )
    (tmp_path / "unrelated.txt").write_text("do not include\n", encoding="utf-8")
    return task


def test_context_pack_contains_only_governed_relevant_files(tmp_path: Path) -> None:
    task = prepare_context_project(tmp_path)
    contract = load_task_contract(task, tmp_path)

    pack = build_context_pack(tmp_path, contract)

    relative_files = {path.relative_to(tmp_path).as_posix() for path in pack.files}
    assert relative_files == {
        "AGENTS.md",
        "agent-specs/backend-worker.spec.md",
        "agent-specs/verifier.spec.md",
        "harness/connectors.md",
        "harness/permissions.policy.md",
        "harness/verification.policy.md",
        "harness/worktree.md",
        "loops/backend.loop.yaml",
        "plans/task-002.md",
        "prompts/verifier-launch.md",
        "prompts/worker-launch.md",
        "requirements/prd.md",
    }
    assert "unrelated.txt" not in relative_files
    assert all(entry.sha256 for entry in pack.manifest)


def test_context_pack_includes_only_latest_structured_feedback(tmp_path: Path) -> None:
    task = prepare_context_project(tmp_path)
    contract = load_task_contract(task, tmp_path)

    pack = build_context_pack(
        tmp_path,
        contract,
        feedback=(
            {
                "gate": "contract",
                "evidence": ["status mismatch"],
                "required_correction": "return 409",
                "files": ["backend/api.py"],
            },
        ),
    )

    rendered = pack.render("worker")
    assert '"gate": "contract"' in rendered
    assert "return 409" in rendered
    assert "unrelated.txt" not in rendered


def test_context_pack_selects_only_the_requested_role_prompt(tmp_path: Path) -> None:
    task = prepare_context_project(tmp_path)
    contract = load_task_contract(task, tmp_path)
    pack = build_context_pack(tmp_path, contract)

    worker = pack.render("worker")
    verifier = pack.render("verifier")

    assert "WORKER LAUNCH CONTRACT" in worker
    assert "VERIFIER LAUNCH CONTRACT" not in worker
    assert "VERIFIER LAUNCH CONTRACT" in verifier
    assert "WORKER LAUNCH CONTRACT" not in verifier
