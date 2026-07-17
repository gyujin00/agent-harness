from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from .state import RunStatus


SENSITIVE_KEY_PARTS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "CREDENTIAL")


def _sanitize(value: Any, *, key: str = "") -> Any:
    upper_key = key.upper()
    if key and any(part in upper_key for part in SENSITIVE_KEY_PARTS):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(item_key): _sanitize(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, RunStatus):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class RunEvent:
    timestamp: str
    run_id: str
    status: str
    actor: str
    detail: Any
    evidence: list[str]


class RunRecorder:
    """Append-only raw and reviewable evidence for one harness run."""

    def __init__(
        self,
        local_root: Path,
        evidence_root: Path,
        run_id: str,
    ) -> None:
        if not run_id or any(character in run_id for character in "\\/:*?\"<>|"):
            raise ValueError("run_id must be a safe directory name")
        self.run_id = run_id
        self.local_dir = local_root / run_id
        self.evidence_dir = evidence_root / run_id
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.local_events = self.local_dir / "events.jsonl"
        self.evidence_events = self.evidence_dir / "events.jsonl"

    def append(
        self,
        status: RunStatus,
        actor: str,
        detail: Any,
        *,
        evidence: Sequence[str] = (),
    ) -> RunEvent:
        event = RunEvent(
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            run_id=self.run_id,
            status=status.value,
            actor=actor,
            detail=_sanitize(detail),
            evidence=[str(item) for item in evidence],
        )
        payload = json.dumps(
            asdict(event),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path in (self.local_events, self.evidence_events):
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(payload + "\n")
        return event

    def last_status(self) -> RunStatus | None:
        if not self.evidence_events.exists():
            return None
        last: RunStatus | None = None
        for line in self.evidence_events.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                last = RunStatus(payload["status"])
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                continue
        return last

