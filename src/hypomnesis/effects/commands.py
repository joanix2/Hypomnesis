"""State machine of a command (cahier des charges §9.7).

The automaton is an explicit transition table: nothing moves unless the table
says so, and terminal states have no outgoing transition (they are absorbing).
This table is the Python mirror of the Lean property « at most one execution of
a non-idempotent command, whatever the retries and transport failures »
(``docs/verification/proprietes.md``, HYP-066):

    Created → Validated → Authorized → Dispatched → Accepted → Completed
       ↓          ↓           ↓  ↘ DryRun / Simulated   ↓  ↘ Failed
    Rejected   Rejected    TimedOut                  UnknownOutcome / TimedOut

The only way to execute an action twice is the ``Dispatched → Dispatched``
self-transition (a retry), and :func:`may_retry` grants it to idempotent
commands only, up to ``RetryPolicy.max_attempts``.

This module is pure: time is injected by the caller (``now``), nothing sleeps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class State(StrEnum):
    CREATED = "Created"
    VALIDATED = "Validated"
    AUTHORIZED = "Authorized"
    DISPATCHED = "Dispatched"
    ACCEPTED = "Accepted"
    COMPLETED = "Completed"
    REJECTED = "Rejected"
    FAILED = "Failed"
    #: The deadline passed before a reliable answer.
    TIMED_OUT = "TimedOut"
    #: The action may or may not have happened (transport failure, no answer).
    UNKNOWN_OUTCOME = "UnknownOutcome"
    #: Mode states (§10.3): the command stops before any real dispatch.
    DRY_RUN = "DryRun"
    SIMULATED = "Simulated"


S = State

TRANSITIONS: dict[State, frozenset[State]] = {
    S.CREATED: frozenset({S.VALIDATED, S.REJECTED}),
    S.VALIDATED: frozenset({S.AUTHORIZED, S.REJECTED}),
    S.AUTHORIZED: frozenset({S.DISPATCHED, S.DRY_RUN, S.SIMULATED, S.REJECTED, S.TIMED_OUT}),
    # Dispatched → Dispatched is a retry, guarded by `may_retry`.
    S.DISPATCHED: frozenset(
        {S.DISPATCHED, S.ACCEPTED, S.COMPLETED, S.FAILED, S.TIMED_OUT, S.UNKNOWN_OUTCOME}
    ),
    S.ACCEPTED: frozenset({S.COMPLETED, S.FAILED, S.TIMED_OUT, S.UNKNOWN_OUTCOME}),
    S.COMPLETED: frozenset(),
    S.REJECTED: frozenset(),
    S.FAILED: frozenset(),
    S.TIMED_OUT: frozenset(),
    S.UNKNOWN_OUTCOME: frozenset(),
    S.DRY_RUN: frozenset(),
    S.SIMULATED: frozenset(),
}

TERMINAL: frozenset[State] = frozenset(s for s, targets in TRANSITIONS.items() if not targets)


def can_move(source: State, target: State) -> bool:
    return target in TRANSITIONS[source]


class IllegalTransition(ValueError):
    """The transition table forbids this move."""


class TransportError(Exception):
    """No reliable answer from the actuator: the action may or may not have happened."""


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded automatic retries; the delay before attempt n+1 is ``delay * backoff**(n-1)``."""

    max_attempts: int = 1
    delay: float = 0.0
    backoff: float = 1.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts doit être >= 1")
        if self.delay < 0 or self.backoff < 1:
            raise ValueError("delay >= 0 et backoff >= 1 attendus")

    def delay_after(self, attempts: int) -> float:
        """Wait before the next attempt, once ``attempts`` attempts have been made."""
        return self.delay * self.backoff ** (attempts - 1)


@dataclass
class CommandRecord:
    """The journal of one command: identifier, history, deadline."""

    command_id: str
    #: Absolute deadline on the injected clock, or ``None`` (no expiry).
    deadline: float | None = None
    history: list[tuple[State, str]] = field(default_factory=lambda: [(State.CREATED, "")])

    @property
    def state(self) -> State:
        return self.history[-1][0]

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL

    @property
    def attempts(self) -> int:
        """Number of times the action was handed to the actuator."""
        return sum(1 for state, _ in self.history if state is State.DISPATCHED)

    def move(self, target: State, detail: str = "") -> None:
        if not can_move(self.state, target):
            raise IllegalTransition(f"{self.command_id}: {self.state} → {target} interdite")
        self.history.append((target, detail))

    def expired(self, now: float) -> bool:
        return self.deadline is not None and now > self.deadline


#: One attempt, no retry.
NO_RETRY = RetryPolicy()


def may_retry(record: CommandRecord, idempotent: bool, policy: RetryPolicy) -> bool:
    """Whether the action may be handed to the actuator once more, automatically.

    A non-idempotent command is never retried: after ``Dispatched`` we cannot
    know whether the first attempt acted.
    """
    return idempotent and record.state is State.DISPATCHED and record.attempts < policy.max_attempts
