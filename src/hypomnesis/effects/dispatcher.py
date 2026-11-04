"""Controlled execution of commands (cahier des charges §9.7, §9.8, §10.3).

A command is an immutable value built by a pure program. Only the dispatcher
executes it, through a fixed sequence of checks, recording every state
transition in a :class:`~hypomnesis.effects.commands.CommandRecord` (the
explicit automaton lives in ``commands.py``):

    Created → Validated → Authorized → Dispatched → Completed
                 ↘ Rejected      ↘ Rejected   ↘ Failed / TimedOut / UnknownOutcome

1. the payload is validated against the actuator's JSON Schema;
2. the permission is checked against the host's policy;
3. business constraints (actuator-specific, pure functions) are checked;
4. the mode decides: ``simulate`` returns a fictitious result, ``dry-run``
   stops before dispatch, ``production`` calls the actuator;
5. the actuator's result is validated against its result schema.

The actuator is never reached by an invalid or unauthorised command, and a
command identifier is dispatched at most once: giving the same command again
returns the existing outcome. After a transport failure (``TransportError``)
only an idempotent actuator is retried, within its ``RetryPolicy``; otherwise
the outcome is ``UnknownOutcome``. The clock and the sleep are injected.
"""

from __future__ import annotations

import itertools
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.commands import (
    NO_RETRY,
    CommandRecord,
    RetryPolicy,
    State,
    TransportError,
    may_retry,
)

MODES = ("simulate", "dry-run", "production")
Payload = Mapping[str, Any]


@dataclass(frozen=True)
class Actuator:
    id: str
    permission: str
    command_schema: str
    result_schema: str
    execute: Callable[[Payload], dict[str, Any]]
    #: Business constraints: payload -> list of violations (pure).
    constraints: Callable[[Payload], list[str]] = lambda _: []
    #: Fictitious result for simulation mode.
    simulate: Callable[[Payload], dict[str, Any]] = lambda p: {"status": "simulated"}
    #: Doing the action twice has the effect of doing it once. Conservative default:
    #: a non-idempotent actuator is never retried automatically.
    idempotent: bool = False
    #: Automatic retries after a transport failure (idempotent actuators only).
    retry: RetryPolicy = NO_RETRY
    #: Seconds allowed from creation of the command; ``None`` = no deadline.
    timeout: float | None = None


@dataclass(frozen=True)
class Command:
    id: str
    actuator: str
    payload: Payload


class DuplicateCommand(ValueError):
    """The same ``command_id`` was given for a different command."""


@dataclass
class Outcome:
    command: Command
    record: CommandRecord
    result: dict[str, Any] | None = None

    @property
    def states(self) -> list[tuple[str, str]]:  # (state, detail)
        return [(state.value, detail) for state, detail in self.record.history]

    @property
    def state(self) -> str:
        return self.record.state.value

    @property
    def dispatched(self) -> bool:
        return self.record.attempts > 0

    @property
    def attempts(self) -> int:
        return self.record.attempts


class Dispatcher:
    def __init__(
        self,
        registry: SchemaRegistry,
        permissions: set[str],
        mode: str = "dry-run",
        on_transition: Callable[[Command, str, str], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if mode not in MODES:
            raise ValueError(f"mode {mode!r} inconnu ({', '.join(MODES)})")
        self.registry = registry
        self.permissions = set(permissions)
        self.mode = mode
        self.actuators: dict[str, Actuator] = {}
        self.history: list[Outcome] = []
        self._ids = itertools.count(1)
        self._on_transition = on_transition
        self._clock = clock
        self._sleep = sleep
        self._outcomes: dict[str, Outcome] = {}  # deduplication by command_id

    def register(self, actuator: Actuator) -> None:
        self.actuators[actuator.id] = actuator

    def command(self, actuator: str, payload: Payload) -> Command:
        """A new command; its identifier (§9.7) is added to the payload if absent."""
        command_id = f"cmd-{next(self._ids)}"
        return Command(command_id, actuator, {"command_id": command_id, **payload})

    def dispatch(self, command: Command) -> Outcome:
        """Run a command through the automaton; a known ``command_id`` is never run again."""
        known = self._outcomes.get(command.id)
        if known is not None:
            if known.command != command:
                raise DuplicateCommand(f"{command.id} désigne déjà une autre commande")
            return known
        actuator = self.actuators.get(command.actuator)
        deadline = None
        if actuator is not None and actuator.timeout is not None:
            deadline = self._clock() + actuator.timeout
        outcome = Outcome(command, CommandRecord(command.id, deadline))
        self.history.append(outcome)
        self._outcomes[command.id] = outcome

        def move(state: State, detail: str = "") -> None:
            outcome.record.move(state, detail)
            if self._on_transition:
                self._on_transition(command, state.value, detail)

        if self._on_transition:
            self._on_transition(command, State.CREATED.value, "")
        if actuator is None:
            move(State.REJECTED, f"actionneur inconnu {command.actuator}")
            return outcome
        issues = self.registry.issues(actuator.command_schema, dict(command.payload))
        if issues:
            move(State.REJECTED, "contrat : " + "; ".join(map(str, issues)))
            return outcome
        move(State.VALIDATED, actuator.command_schema)
        if actuator.permission not in self.permissions:
            move(State.REJECTED, f"permission refusée : {actuator.permission}")
            return outcome
        violations = actuator.constraints(command.payload)
        if violations:
            move(State.REJECTED, "contraintes métier : " + "; ".join(violations))
            return outcome
        move(State.AUTHORIZED, actuator.permission)
        if self.mode == "dry-run":
            move(State.DRY_RUN, "validée et autorisée, non exécutée")
            return outcome
        if self.mode == "simulate":
            outcome.result = actuator.simulate(command.payload)
            move(State.SIMULATED, "réponse fictive")
            return outcome
        if outcome.record.expired(self._clock()):
            move(State.TIMED_OUT, "échéance dépassée avant l'envoi")
            return outcome
        self._execute(actuator, outcome, move)
        return outcome

    def _execute(
        self, actuator: Actuator, outcome: Outcome, move: Callable[[State, str], None]
    ) -> None:
        """Hand the command to the actuator; retry only when ``may_retry`` allows it."""
        record = outcome.record
        move(State.DISPATCHED, "")
        while True:
            try:
                result = actuator.execute(outcome.command.payload)
            except TransportError as exc:
                if record.expired(self._clock()):
                    move(State.TIMED_OUT, f"échéance dépassée ; issue inconnue ({exc})")
                    return
                if not may_retry(record, actuator.idempotent, actuator.retry):
                    why = (
                        "commande non idempotente"
                        if not actuator.idempotent
                        else "relances épuisées"
                    )
                    move(State.UNKNOWN_OUTCOME, f"{exc} ; {why}, aucune relance")
                    return
                self._sleep(actuator.retry.delay_after(record.attempts))
                if record.expired(self._clock()):
                    move(State.TIMED_OUT, "échéance dépassée avant la relance")
                    return
                move(
                    State.DISPATCHED, f"relance {record.attempts + 1}/{actuator.retry.max_attempts}"
                )
                continue
            except Exception as exc:  # the actuator answered with a failure: it is reported
                move(State.FAILED, f"{type(exc).__name__}: {exc}")
                return
            break
        if record.expired(self._clock()):
            move(State.TIMED_OUT, "réponse reçue après l'échéance")
            return
        issues = self.registry.issues(actuator.result_schema, result)
        if issues:
            move(State.FAILED, "réponse non conforme : " + "; ".join(map(str, issues)))
            return
        outcome.result = result
        move(State.COMPLETED, "")
