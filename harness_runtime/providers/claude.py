from __future__ import annotations

from .base import AgentRequest, AgentRole, SubprocessProvider


class ClaudeProvider(SubprocessProvider):
    name = "claude"

    def build_command(self, request: AgentRequest) -> tuple[str, ...]:
        command = [
            "claude",
            "-p",
            "--agent",
            request.agent_name,
            "--permission-mode",
            "dontAsk",
            "--output-format",
            "json",
            "--json-schema",
            request.output_schema.read_text(encoding="utf-8"),
            "--no-session-persistence",
        ]
        if request.role is AgentRole.VERIFIER:
            command.extend(("--tools", "Read,Grep,Glob,Bash"))
        if request.budget_usd is not None:
            command.extend(("--max-budget-usd", str(request.budget_usd)))
        if request.model:
            command.extend(("--model", request.model))
        return tuple(command)

