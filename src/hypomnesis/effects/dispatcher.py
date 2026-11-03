"""Controlled execution of commands (cahier des charges §9.7, §9.8, §10.3).

A command is an immutable value built by a pure program. Only the dispatcher
executes it, through a fixed sequence of checks, recording every state
transition:

    Created → Validated → Authorized → Dispatched → Completed
                 ↘ Rejected      ↘ Rejected   ↘ Failed

1. the payload is validated against the actuator's JSON Schema;
2. the permission is checked against the host's policy;
3. business constraints (actuator-specific, pure functions) are checked;
4. the mode decides: ``simulate`` returns a fictitious result, ``dry-run``
   stops before dispatch, ``production`` calls the actuator;
5. the actuator's result is validated against its result schema.

The actuator is never reached by an invalid or unauthorised command.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry

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


@dataclass(frozen=True)
class Command:
    id: str
    actuator: str
    payload: Payload


@dataclass
class Outcome:
    command: Command
    states: list[tuple[str, str]] = field(default_factory=list)  # (state, detail)
    result: dict[str, Any] | None = None

    @property
    def state(self) -> str:
        return self.states[-1][0]

    @property
    def dispatched(self) -> bool:
        return any(s == "Dispatched" for s, _ in self.states)


class Dispatcher:
    def __init__(
        self,
        registry: SchemaRegistry,
        permissions: set[str],
        mode: str = "dry-run",
        on_transition: Callable[[Command, str, str], None] | None = None,
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

    def register(self, actuator: Actuator) -> None:
        self.actuators[actuator.id] = actuator

    def command(self, actuator: str, payload: Payload) -> Command:
        return Command(f"cmd-{next(self._ids)}", actuator, dict(payload))

    def dispatch(self, command: Command) -> Outcome:
        outcome = Outcome(command)
        self.history.append(outcome)

        def move(state: str, detail: str = "") -> None:
            outcome.states.append((state, detail))
            if self._on_transition:
                self._on_transition(command, state, detail)

        move("Created")
        actuator = self.actuators.get(command.actuator)
        if actuator is None:
            move("Rejected", f"actionneur inconnu {command.actuator}")
            return outcome
        issues = self.registry.issues(actuator.command_schema, dict(command.payload))
        if issues:
            move("Rejected", "contrat : " + "; ".join(map(str, issues)))
            return outcome
        move("Validated", actuator.command_schema)
        if actuator.permission not in self.permissions:
            move("Rejected", f"permission refusée : {actuator.permission}")
            return outcome
        violations = actuator.constraints(command.payload)
        if violations:
            move("Rejected", "contraintes métier : " + "; ".join(violations))
            return outcome
        move("Authorized", actuator.permission)
        if self.mode == "dry-run":
            move("DryRun", "validée et autorisée, non exécutée")
            return outcome
        if self.mode == "simulate":
            outcome.result = actuator.simulate(command.payload)
            move("Simulated", "réponse fictive")
            return outcome
        move("Dispatched")
        try:
            result = actuator.execute(command.payload)
        except Exception as exc:  # the outcome records the failure; nothing is retried
            move("Failed", f"{type(exc).__name__}: {exc}")
            return outcome
        issues = self.registry.issues(actuator.result_schema, result)
        if issues:
            move("Failed", "réponse non conforme : " + "; ".join(map(str, issues)))
            return outcome
        outcome.result = result
        move("Completed")
        return outcome
