from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness_runtime.providers.base import (
    AgentRequest,
    AgentRole,
    ProviderError,
    decode_agent_result,
)
from harness_runtime.providers.claude import ClaudeProvider
from harness_runtime.providers.codex import CodexProvider


@pytest.fixture
def schema(tmp_path: Path) -> Path:
    path = tmp_path / "result.schema.json"
    path.write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["status", "summary", "evidence"],
                "properties": {
                    "status": {"enum": ["pass", "fail", "needs_human"]},
                    "summary": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def request_for(
    tmp_path: Path,
    schema: Path,
    role: AgentRole = AgentRole.WORKER,
) -> AgentRequest:
    workdir = tmp_path / "worktree"
    workdir.mkdir(exist_ok=True)
    raw = tmp_path / "raw"
    return AgentRequest(
        role=role,
        agent_name="backend-worker" if role is AgentRole.WORKER else "verifier",
        prompt="Implement the Task Contract.",
        workdir=workdir,
        output_schema=schema,
        raw_output_dir=raw,
        timeout_seconds=60,
        budget_usd=2.5,
    )


def test_claude_worker_uses_structured_noninteractive_mode(
    tmp_path: Path, schema: Path
) -> None:
    request = request_for(tmp_path, schema)

    command = ClaudeProvider().build_command(request)

    assert command[:2] == ("claude", "-p")
    assert command[command.index("--agent") + 1] == "backend-worker"
    assert command[command.index("--permission-mode") + 1] == "dontAsk"
    assert "--json-schema" in command
    assert "--no-session-persistence" in command
    assert "--dangerously-skip-permissions" not in command
    assert "bypassPermissions" not in command


def test_claude_verifier_has_no_edit_tools(tmp_path: Path, schema: Path) -> None:
    request = request_for(tmp_path, schema, AgentRole.VERIFIER)

    command = ClaudeProvider().build_command(request)

    allowed = command[command.index("--tools") + 1]
    assert "Read" in allowed
    assert "Edit" not in allowed
    assert "Write" not in allowed


def test_codex_worker_uses_workspace_write_without_bypass(
    tmp_path: Path, schema: Path
) -> None:
    request = request_for(tmp_path, schema)

    command = CodexProvider().build_command(request)

    assert command[:2] == ("codex", "exec")
    assert command[command.index("-s") + 1] == "workspace-write"
    assert command[command.index("-a") + 1] == "never"
    assert "--output-schema" in command
    assert "--ephemeral" in command
    assert command[-1] == "-"
    assert "--dangerously-bypass-approvals-and-sandbox" not in command


def test_codex_verifier_is_read_only(tmp_path: Path, schema: Path) -> None:
    request = request_for(tmp_path, schema, AgentRole.VERIFIER)

    command = CodexProvider().build_command(request)

    assert command[command.index("-s") + 1] == "read-only"


def test_decodes_direct_and_wrapped_structured_results() -> None:
    direct = decode_agent_result(
        '{"status":"pass","summary":"done","evidence":["test"]}'
    )
    wrapped = decode_agent_result(
        '{"structured_output":{"status":"fail","summary":"broken",'
        '"evidence":["gate"],"issues":[]}}'
    )

    assert direct.status == "pass"
    assert direct.evidence == ("test",)
    assert wrapped.status == "fail"
    assert wrapped.summary == "broken"


def test_rejects_non_json_or_unknown_status() -> None:
    with pytest.raises(ProviderError, match="valid JSON"):
        decode_agent_result("I finished the task")
    with pytest.raises(ProviderError, match="unsupported status"):
        decode_agent_result(
            '{"status":"success","summary":"done","evidence":[]}'
        )

