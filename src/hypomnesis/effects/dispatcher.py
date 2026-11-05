"""Controlled execution of commands (cahier des charges §9.7, §9.8, §10.3).

A command is an immutable value built by a pure program. Only the dispatcher
executes it, through a fixed sequence of checks, recording every state
transition in a :class:`~hypomnesis.effects.commands.CommandRecord` (the
explicit automaton lives in ``commands.py``):

    Created → Validated → Authorized → Dispatched → Completed
                 ↘ Rejected      ↘ Rejected   ↘ Failed / TimedOut / UnknownOutcome

JSON structure, contracts, host permissions, business and safety constraints,
then required human approval are checked before selecting the execution mode.
Real and simulated responses are validated. Production optionally observes
the physical effect after recording the result. Every check is recorded.

The actuator is never reached by an invalid or unauthorised command, and a
command identifier is dispatched at most once: giving the same command again
returns the existing outcome. After a transport failure (``TransportError``)
only an idempotent actuator is retried, within its ``RetryPolicy``; otherwise
the outcome is ``UnknownOutcome``. The clock and the sleep are injected.
"""

from __future__ import annotations

import itertools
import json
import time
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
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
from hypomnesis.effects.permissions import PermissionPolicy
from hypomnesis.language.errors import EvaluationError
from hypomnesis.observability.trace import current_tracer, operation
from hypomnesis.runtime.json import data_to_json

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
    safety: Callable[[Payload], list[str]] = lambda _: []
    requires_human: bool = False
    observe_effects: Callable[[Payload, dict[str, Any]], list[str]] | None = None


@dataclass(frozen=True)
class Command:
    id: str
    actuator: str
    payload: Payload


class DuplicateCommand(ValueError):
    """The same ``command_id`` was given for a different command."""


@dataclass(frozen=True)
class PipelineCheck:
    stage: str
    passed: bool
    detail: str = ""


@dataclass
class Outcome:
    command: Command
    record: CommandRecord
    result: dict[str, Any] | None = None
    checks: list[PipelineCheck] = field(default_factory=list)

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
        policy: PermissionPolicy | None = None,
        approve: Callable[[Command], bool] | None = None,
    ) -> None:
        if mode not in MODES:
            raise ValueError(f"mode {mode!r} inconnu ({', '.join(MODES)})")
        self.registry = registry
        self.permissions = set(permissions)
        self.policy = policy
        self._approve = approve
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
        fresh = command.id not in self._outcomes
        with operation("actuator.authorize", plugin=command.actuator, mode=self.mode):
            outcome, actuator = self._authorize(command)
        if actuator is not None:

            def move(state: State, detail: str = "") -> None:
                outcome.record.move(state, detail)
                if self._on_transition:
                    self._on_transition(command, state.value, detail)

            handler = {
                "dry-run": self._dry_run,
                "simulate": self._simulate,
                "production": self._production,
            }[self.mode]
            handler(actuator, outcome, move)
        tracer = current_tracer()
        if fresh and tracer is not None:
            tracer.metrics.command(outcome.state, self.mode)
        return outcome

    def _authorize(self, command: Command) -> tuple[Outcome, Actuator | None]:
        known = self._outcomes.get(command.id)
        if known is not None:
            if known.command != command:
                raise DuplicateCommand(f"{command.id} désigne déjà une autre commande")
            return known, None
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

        def gate(stage: str, validate: Callable[[], list[str]]) -> bool:
            try:
                violations = validate()
                if type(violations) is not list or any(type(v) is not str for v in violations):
                    raise ValueError("validation must return a list of violations")
            except Exception as exc:
                violations = [f"{type(exc).__name__}: {exc}"]
            outcome.checks.append(PipelineCheck(stage, not violations, "; ".join(violations)))
            if violations:
                label = {
                    "business": "contraintes métier",
                    "safety": "sécurité",
                    "approval": "validation humaine",
                }[stage]
                move(State.REJECTED, f"{label} : " + "; ".join(violations))
            return not violations

        if self._on_transition:
            self._on_transition(command, State.CREATED.value, "")
        if actuator is None:
            move(State.REJECTED, f"actionneur inconnu {command.actuator}")
            return outcome, None
        try:
            json.dumps(dict(command.payload), allow_nan=False)
            data_to_json(dict(command.payload))
        except (TypeError, ValueError, EvaluationError) as exc:
            outcome.checks.append(PipelineCheck("structure", False, str(exc)))
            move(State.REJECTED, f"structure JSON : {exc}")
            return outcome, None
        outcome.checks.append(PipelineCheck("structure", True))
        if (
            actuator.command_schema not in self.registry
            or actuator.result_schema not in self.registry
        ):
            outcome.checks.append(PipelineCheck("contract", False, "contrat inconnu"))
            move(State.REJECTED, "contrat inconnu")
            return outcome, None
        issues = self.registry.issues(actuator.command_schema, dict(command.payload))
        if "command_id" in command.payload and command.payload["command_id"] != command.id:
            outcome.checks.append(PipelineCheck("contract", False, "command_id incompatible"))
            move(State.REJECTED, "command_id incompatible")
            return outcome, None
        outcome.checks.append(PipelineCheck("contract", not issues, "; ".join(map(str, issues))))
        if issues:
            move(State.REJECTED, "contrat : " + "; ".join(map(str, issues)))
            return outcome, None
        move(State.VALIDATED, actuator.command_schema)
        permitted = (
            self.policy.permits(actuator.permission)
            if self.policy is not None
            else actuator.permission in self.permissions
        )
        outcome.checks.append(PipelineCheck("permission", permitted, actuator.permission))
        if not permitted:
            move(State.REJECTED, f"permission refusée : {actuator.permission}")
            return outcome, None
        if not gate("business", lambda: actuator.constraints(deepcopy(dict(command.payload)))):
            return outcome, None
        if not gate("safety", lambda: actuator.safety(deepcopy(dict(command.payload)))):
            return outcome, None
        if actuator.requires_human:

            def approval() -> list[str]:
                approved = (
                    self._approve is not None
                    and self._approve(
                        Command(command.id, command.actuator, deepcopy(dict(command.payload)))
                    )
                    is True
                )
                return [] if approved else ["validation humaine requise ou refusée"]

            if not gate("approval", approval):
                return outcome, None
        move(State.AUTHORIZED, actuator.permission)
        return outcome, actuator

    def _dry_run(
        self, actuator: Actuator, outcome: Outcome, move: Callable[[State, str], None]
    ) -> None:
        move(State.DRY_RUN, "validée et autorisée, non exécutée")

    def _simulate(
        self, actuator: Actuator, outcome: Outcome, move: Callable[[State, str], None]
    ) -> None:
        try:
            outcome.result = actuator.simulate(deepcopy(dict(outcome.command.payload)))
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            outcome.checks.append(PipelineCheck("response", False, detail))
            move(State.REJECTED, "simulation : " + detail)
            return
        issues = self._response_issues(actuator, outcome.result)
        outcome.checks.append(PipelineCheck("response", not issues, "; ".join(issues)))
        if issues:
            outcome.result = None
            move(State.REJECTED, "réponse simulée non conforme : " + "; ".join(issues))
            return
        move(State.SIMULATED, "réponse fictive")

    def _production(
        self, actuator: Actuator, outcome: Outcome, move: Callable[[State, str], None]
    ) -> None:
        if outcome.record.expired(self._clock()):
            move(State.TIMED_OUT, "échéance dépassée avant l'envoi")
            return
        self._execute(actuator, outcome, move)

    def _response_issues(self, actuator: Actuator, result: Any) -> list[str]:
        if not isinstance(result, dict):
            return ["la réponse doit être un objet JSON"]
        try:
            json.dumps(result, allow_nan=False)
            data_to_json(result)
        except (TypeError, ValueError, EvaluationError) as exc:
            return [f"structure JSON : {exc}"]
        return list(map(str, self.registry.issues(actuator.result_schema, result)))

    def _execute(
        self, actuator: Actuator, outcome: Outcome, move: Callable[[State, str], None]
    ) -> None:
        """Hand the command to the actuator; retry only when ``may_retry`` allows it."""
        record = outcome.record
        move(State.DISPATCHED, "")
        outcome.checks.append(PipelineCheck("execute", True, "adaptateur appelé"))
        while True:
            try:
                with operation("actuator.execute", plugin=actuator.id):
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
        issues = self._response_issues(actuator, result)
        outcome.checks.append(PipelineCheck("response", not issues, "; ".join(issues)))
        if issues:
            move(State.FAILED, "réponse non conforme : " + "; ".join(map(str, issues)))
            return
        outcome.result = result
        outcome.checks.append(PipelineCheck("result", True, "résultat enregistré"))
        if actuator.observe_effects is not None:
            try:
                with operation("observer.verify", plugin=actuator.id):
                    violations = actuator.observe_effects(
                        deepcopy(dict(outcome.command.payload)), deepcopy(result)
                    )
                if type(violations) is not list or any(type(v) is not str for v in violations):
                    raise ValueError("observation must return a list of violations")
            except Exception as exc:
                violations = [f"{type(exc).__name__}: {exc}"]
            outcome.checks.append(
                PipelineCheck("observation", not violations, "; ".join(violations))
            )
            if violations:
                move(State.FAILED, "observation réelle : " + "; ".join(violations))
                return
        move(State.COMPLETED, "")
