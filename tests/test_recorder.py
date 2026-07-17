from __future__ import annotations

import json
from pathlib import Path

from harness_runtime.recorder import RunRecorder
from harness_runtime.state import RunStatus


def read_events(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_recorder_writes_local_and_sanitized_evidence_logs(tmp_path: Path) -> None:
    recorder = RunRecorder(
        local_root=tmp_path / ".harness" / "runs",
        evidence_root=tmp_path / "docs" / "runs",
        run_id="run-1",
    )

    recorder.append(
        RunStatus.PREPARING,
        "orchestrator",
        {"message": "context ready", "OPENAI_API_KEY": "secret-value"},
        evidence=("plans/task-002.md",),
    )

    local = read_events(tmp_path / ".harness" / "runs" / "run-1" / "events.jsonl")
    evidence = read_events(tmp_path / "docs" / "runs" / "run-1" / "events.jsonl")
    assert local == evidence
    assert evidence[0]["status"] == "preparing"
    assert evidence[0]["detail"]["OPENAI_API_KEY"] == "[REDACTED]"
    assert evidence[0]["evidence"] == ["plans/task-002.md"]


def test_recorder_is_append_only_and_recovers_last_status(tmp_path: Path) -> None:
    recorder = RunRecorder(tmp_path / "raw", tmp_path / "evidence", "run-2")

    recorder.append(RunStatus.PREPARING, "orchestrator", "context")
    recorder.append(RunStatus.IN_PROGRESS, "worker", "started")

    event_path = tmp_path / "evidence" / "run-2" / "events.jsonl"
    assert len(read_events(event_path)) == 2
    assert recorder.last_status() is RunStatus.IN_PROGRESS


def test_recorder_ignores_truncated_last_line_when_recovering(tmp_path: Path) -> None:
    recorder = RunRecorder(tmp_path / "raw", tmp_path / "evidence", "run-3")
    recorder.append(RunStatus.PREPARING, "orchestrator", "context")
    event_path = tmp_path / "evidence" / "run-3" / "events.jsonl"
    with event_path.open("a", encoding="utf-8") as stream:
        stream.write('{"status":')

    assert recorder.last_status() is RunStatus.PREPARING
