from __future__ import annotations

import pytest

from harness_runtime.state import InvalidTransition, RunStatus, next_status


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        (RunStatus.QUEUED, RunStatus.PREPARING),
        (RunStatus.PREPARING, RunStatus.IN_PROGRESS),
        (RunStatus.IN_PROGRESS, RunStatus.IN_VERIFY),
        (RunStatus.IN_VERIFY, RunStatus.BACK_TO_ACTION),
        (RunStatus.BACK_TO_ACTION, RunStatus.IN_PROGRESS),
        (RunStatus.IN_VERIFY, RunStatus.RECORDING),
        (RunStatus.RECORDING, RunStatus.COMPLETE),
        (RunStatus.RECORDING, RunStatus.PR_READY),
    ],
)
def test_allows_declared_transitions(
    current: RunStatus, requested: RunStatus
) -> None:
    assert next_status(current, requested) is requested


def test_pr_ready_cannot_transition_to_merge() -> None:
    with pytest.raises(InvalidTransition, match="pr_ready"):
        next_status(RunStatus.PR_READY, "merged")


@pytest.mark.parametrize(
    "terminal",
    [
        RunStatus.COMPLETE,
        RunStatus.PR_READY,
        RunStatus.INVALID_CONTRACT,
        RunStatus.BLOCKED,
        RunStatus.TIMED_OUT,
        RunStatus.NEEDS_HUMAN,
    ],
)
def test_terminal_states_cannot_transition(terminal: RunStatus) -> None:
    with pytest.raises(InvalidTransition):
        next_status(terminal, RunStatus.PREPARING)

