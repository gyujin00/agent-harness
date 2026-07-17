from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    QUEUED = "queued"
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    IN_VERIFY = "in_verify"
    BACK_TO_ACTION = "back_to_action"
    RECORDING = "recording"
    PR_READY = "pr_ready"
    COMPLETE = "complete"
    INVALID_CONTRACT = "invalid_contract"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"
    NEEDS_HUMAN = "needs_human"


TERMINAL_STATUSES = frozenset(
    {
        RunStatus.PR_READY,
        RunStatus.COMPLETE,
        RunStatus.INVALID_CONTRACT,
        RunStatus.BLOCKED,
        RunStatus.TIMED_OUT,
        RunStatus.NEEDS_HUMAN,
    }
)

ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.QUEUED: frozenset(
        {RunStatus.PREPARING, RunStatus.INVALID_CONTRACT, RunStatus.BLOCKED}
    ),
    RunStatus.PREPARING: frozenset(
        {RunStatus.IN_PROGRESS, RunStatus.INVALID_CONTRACT, RunStatus.BLOCKED}
    ),
    RunStatus.IN_PROGRESS: frozenset(
        {
            RunStatus.IN_VERIFY,
            RunStatus.BACK_TO_ACTION,
            RunStatus.TIMED_OUT,
            RunStatus.NEEDS_HUMAN,
        }
    ),
    RunStatus.IN_VERIFY: frozenset(
        {
            RunStatus.BACK_TO_ACTION,
            RunStatus.RECORDING,
            RunStatus.TIMED_OUT,
            RunStatus.NEEDS_HUMAN,
        }
    ),
    RunStatus.BACK_TO_ACTION: frozenset(
        {
            RunStatus.IN_PROGRESS,
            RunStatus.TIMED_OUT,
            RunStatus.NEEDS_HUMAN,
        }
    ),
    RunStatus.RECORDING: frozenset(
        {RunStatus.PR_READY, RunStatus.COMPLETE, RunStatus.NEEDS_HUMAN}
    ),
    **{terminal: frozenset() for terminal in TERMINAL_STATUSES},
}


class InvalidTransition(ValueError):
    """Raised when a run attempts a state transition outside the harness."""


def next_status(
    current: RunStatus, requested: RunStatus | str
) -> RunStatus:
    try:
        target = requested if isinstance(requested, RunStatus) else RunStatus(requested)
    except ValueError as exc:
        raise InvalidTransition(
            f"cannot transition from {current.value} to unknown state {requested!r}"
        ) from exc
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(
            f"cannot transition from {current.value} to {target.value}"
        )
    return target

