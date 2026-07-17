from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


RESULT_STATUSES = frozenset({"pass", "fail", "needs_human"})


class AgentRole(StrEnum):
    WORKER = "worker"
    VERIFIER = "verifier"


class ProviderError(RuntimeError):
    """Raised when a provider cannot return a trusted structured result."""


@dataclass(frozen=True)
class AgentIssue:
    gate: str
    evidence: tuple[str, ...] = ()
    required_correction: str = ""
    files: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate,
            "evidence": list(self.evidence),
            "required_correction": self.required_correction,
            "files": list(self.files),
        }


@dataclass(frozen=True)
class AgentRequest:
    role: AgentRole
    agent_name: str
    prompt: str
    workdir: Path
    output_schema: Path
    raw_output_dir: Path
    timeout_seconds: int
    budget_usd: float | None = None
    model: str | None = None


@dataclass(frozen=True)
class AgentResult:
    status: str
    summary: str
    evidence: tuple[str, ...] = ()
    issues: tuple[AgentIssue, ...] = ()
    session_id: str | None = None

    def __post_init__(self) -> None:
        if self.status not in RESULT_STATUSES:
            raise ValueError(f"unsupported status: {self.status}")

    @classmethod
    def pass_(
        cls,
        summary: str,
        evidence: Sequence[str] = (),
        *,
        session_id: str | None = None,
    ) -> AgentResult:
        return cls("pass", summary, tuple(evidence), session_id=session_id)

    @classmethod
    def fail(
        cls,
        summary: str,
        evidence: Sequence[str] = (),
        *,
        issues: Sequence[AgentIssue] = (),
        session_id: str | None = None,
    ) -> AgentResult:
        return cls(
            "fail",
            summary,
            tuple(evidence),
            tuple(issues),
            session_id,
        )

    @classmethod
    def needs_human(
        cls,
        summary: str,
        evidence: Sequence[str] = (),
        *,
        issues: Sequence[AgentIssue] = (),
        session_id: str | None = None,
    ) -> AgentResult:
        return cls(
            "needs_human",
            summary,
            tuple(evidence),
            tuple(issues),
            session_id,
        )


class Provider(Protocol):
    name: str

    def run(self, request: AgentRequest) -> AgentResult: ...


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ProviderError(f"{field} must be an array of strings")
    return tuple(value)


def _decode_issue(value: Any) -> AgentIssue:
    if not isinstance(value, Mapping):
        raise ProviderError("each issue must be an object")
    gate = value.get("gate")
    correction = value.get("required_correction", "")
    if not isinstance(gate, str) or not gate:
        raise ProviderError("issue.gate must be a non-empty string")
    if not isinstance(correction, str):
        raise ProviderError("issue.required_correction must be a string")
    return AgentIssue(
        gate=gate,
        evidence=_string_tuple(value.get("evidence", []), "issue.evidence"),
        required_correction=correction,
        files=_string_tuple(value.get("files", []), "issue.files"),
    )


def decode_agent_result(text: str) -> AgentResult:
    try:
        payload: Any = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ProviderError("provider did not return valid JSON") from exc
    if isinstance(payload, Mapping) and "structured_output" in payload:
        payload = payload["structured_output"]
    if isinstance(payload, Mapping) and isinstance(payload.get("result"), str):
        try:
            nested = json.loads(payload["result"])
        except json.JSONDecodeError:
            nested = None
        if isinstance(nested, Mapping):
            payload = nested
    if not isinstance(payload, Mapping):
        raise ProviderError("provider result must be a JSON object")

    status = payload.get("status")
    summary = payload.get("summary")
    if status not in RESULT_STATUSES:
        raise ProviderError(f"unsupported status: {status!r}")
    if not isinstance(summary, str):
        raise ProviderError("summary must be a string")
    raw_issues = payload.get("issues", [])
    if not isinstance(raw_issues, list):
        raise ProviderError("issues must be an array")
    session_id = payload.get("session_id")
    if session_id is not None and not isinstance(session_id, str):
        raise ProviderError("session_id must be a string or null")
    return AgentResult(
        status=status,
        summary=summary,
        evidence=_string_tuple(payload.get("evidence", []), "evidence"),
        issues=tuple(_decode_issue(issue) for issue in raw_issues),
        session_id=session_id,
    )


class SubprocessProvider(ABC):
    name: str

    @abstractmethod
    def build_command(self, request: AgentRequest) -> tuple[str, ...]:
        raise NotImplementedError

    def result_text(
        self,
        request: AgentRequest,
        completed: subprocess.CompletedProcess[str],
    ) -> str:
        return completed.stdout

    def run(self, request: AgentRequest) -> AgentResult:
        request.raw_output_dir.mkdir(parents=True, exist_ok=True)
        command = self.build_command(request)
        try:
            completed = subprocess.run(
                command,
                cwd=request.workdir,
                input=request.prompt,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                shell=False,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ProviderError(f"{self.name} CLI was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                f"{self.name} {request.role.value} timed out after "
                f"{request.timeout_seconds}s"
            ) from exc

        prefix = request.role.value
        (request.raw_output_dir / f"{prefix}.stdout.log").write_text(
            completed.stdout,
            encoding="utf-8",
        )
        (request.raw_output_dir / f"{prefix}.stderr.log").write_text(
            completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise ProviderError(
                f"{self.name} {request.role.value} exited with "
                f"{completed.returncode}"
            )
        return decode_agent_result(self.result_text(request, completed))

