from __future__ import annotations

import subprocess

from .base import AgentRequest, AgentRole, ProviderError, SubprocessProvider


class CodexProvider(SubprocessProvider):
    name = "codex"

    @staticmethod
    def _last_message_path(request: AgentRequest):
        return request.raw_output_dir / f"{request.role.value}.last.json"

    def build_command(self, request: AgentRequest) -> tuple[str, ...]:
        sandbox = (
            "read-only"
            if request.role is AgentRole.VERIFIER
            else "workspace-write"
        )
        command = [
            "codex",
            "exec",
            "-C",
            str(request.workdir),
            "-s",
            sandbox,
            "-a",
            "never",
            "--ephemeral",
            "--output-schema",
            str(request.output_schema),
            "--output-last-message",
            str(self._last_message_path(request)),
        ]
        if request.model:
            command.extend(("-m", request.model))
        command.append("-")
        return tuple(command)

    def result_text(
        self,
        request: AgentRequest,
        completed: subprocess.CompletedProcess[str],
    ) -> str:
        last_message = self._last_message_path(request)
        if not last_message.is_file():
            raise ProviderError("codex did not write its structured last message")
        return last_message.read_text(encoding="utf-8")

