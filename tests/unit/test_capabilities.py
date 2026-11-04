"""Capability interfaces (HYP-040): one conforming fake plugin per interface, error containment."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from hypomnesis.capabilities import (
    RAISED,
    ROLES,
    Actuator,
    Certificate,
    Diagnostic,
    Estimator,
    Generator,
    KnowledgeBase,
    Observer,
    Resolver,
    Result,
    Severity,
    Solver,
    Transpiler,
    Validator,
    failure,
    guarded,
    roles_of,
    success,
)

ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------ fake plugins (no backend)


class FakeObserver:
    def observe(self, query: str, /) -> Result[float]:
        return success(21.5)


class FakeGenerator:
    def generate(self, spec: int, /, *, limit: int) -> Result[Sequence[int]]:
        return success(list(range(spec))[:limit])


class FakeEstimator:
    def estimate(self, unknown: str, /) -> Result[float]:
        return success(0.5, diagnostics=[Diagnostic("estimate.rough", "coarse", Severity.WARNING)])


class FakeTranspiler:
    def transpile(self, source: str, /) -> Result[str]:
        return success(source.upper())


class FakeSolver:
    def solve(self, problem: Mapping[str, int], /) -> Result[Mapping[str, int]]:
        return success({"x": problem["bound"] - 1})


class FakeValidator:
    def validate(self, proposal: int, /) -> Result[int]:
        if proposal >= 0:
            return success(proposal, certificate=Certificate("witness", {"checked": proposal}))
        return failure(
            Diagnostic("validate.refused", "negative", data={"counterexample": proposal})
        )


class FakeKnowledgeBase:
    def __init__(self) -> None:
        self.facts: list[str] = []

    def query(self, question: object, /) -> Result[Sequence[str]]:
        return success([f for f in self.facts if f == question])

    def store(self, fact: str, /) -> Result[None]:
        self.facts.append(fact)
        return success(None)


class FakeActuator:
    def actuate(self, command: str, /) -> Result[str]:
        return success(f"done:{command}")


class FakeResolver:
    def resolve(self, goal: str, capabilities: Mapping[str, object], /) -> Result[str]:
        return success(f"{goal}:{len(capabilities)}")


# Static conformance: pyright checks each assignment against the protocol.
_OBSERVER: Observer[str, float] = FakeObserver()
_GENERATOR: Generator[int, int] = FakeGenerator()
_ESTIMATOR: Estimator[str, float] = FakeEstimator()
_TRANSPILER: Transpiler[str, str] = FakeTranspiler()
_SOLVER: Solver[Mapping[str, int], Mapping[str, int]] = FakeSolver()
_VALIDATOR: Validator[int, int] = FakeValidator()
_KNOWLEDGE_BASE: KnowledgeBase[str] = FakeKnowledgeBase()
_ACTUATOR: Actuator[str, str] = FakeActuator()
_RESOLVER: Resolver[str, str] = FakeResolver()

FAKES: dict[str, object] = {
    "Observer": FakeObserver(),
    "Generator": FakeGenerator(),
    "Estimator": FakeEstimator(),
    "Transpiler": FakeTranspiler(),
    "Solver": FakeSolver(),
    "Validator": FakeValidator(),
    "KnowledgeBase": FakeKnowledgeBase(),
    "Actuator": FakeActuator(),
    "Resolver": FakeResolver(),
}


# ------------------------------------------------------------------ conformance


def test_roles_match_the_manifest_schema():
    schema = json.loads(
        (ROOT / "src/hypomnesis/contracts/schemas/extension-manifest-1.0.0.json").read_text()
    )
    assert set(ROLES) == set(schema["properties"]["role"]["enum"])
    assert set(FAKES) == set(ROLES)


@pytest.mark.parametrize("role", sorted(ROLES))
def test_fake_plugin_conforms_to_its_role_only(role: str):
    assert isinstance(FAKES[role], ROLES[role])
    assert roles_of(FAKES[role]) == (role,)


def test_object_without_the_methods_has_no_role():
    assert roles_of(object()) == ()


def test_nominal_calls():
    assert FakeObserver().observe("t").value == 21.5
    assert FakeGenerator().generate(5, limit=3).value == [0, 1, 2]
    estimated = FakeEstimator().estimate("u")
    assert estimated.value == 0.5 and estimated.ok  # a warning does not make it fail
    assert FakeTranspiler().transpile("a").value == "A"
    assert FakeSolver().solve({"bound": 3}).value == {"x": 2}
    assert FakeActuator().actuate("go").value == "done:go"
    assert FakeResolver().resolve("g", {"a": object()}).value == "g:1"
    kb = FakeKnowledgeBase()
    assert kb.store("f").ok
    assert kb.query("f").value == ["f"]


def test_validator_returns_a_certificate_or_a_counterexample():
    accepted = FakeValidator().validate(2)
    assert accepted.ok and accepted.certificate == Certificate("witness", {"checked": 2})
    refused = FakeValidator().validate(-1)
    assert not refused.ok and refused.value is None
    assert refused.diagnostics[0].data == {"counterexample": -1}


# ------------------------------------------------------------------ error containment


class Exploding:
    @guarded
    def solve(self, problem: int, /) -> Result[int]:
        raise ZeroDivisionError("boom")

    @guarded
    def fine(self, problem: int, /) -> Result[int]:
        return success(problem + 1)


def test_exception_becomes_a_failed_result():
    result = Exploding().solve(1)
    assert not result.ok and result.value is None
    (diagnostic,) = result.diagnostics
    assert diagnostic.code == RAISED
    assert diagnostic.severity is Severity.ERROR
    assert "ZeroDivisionError" in diagnostic.message and "boom" in diagnostic.message
    assert diagnostic.data == {"exception": "ZeroDivisionError"}


def test_guarded_is_transparent_on_success():
    assert Exploding().fine(1) == success(2)
    assert Exploding.fine.__name__ == "fine"


def test_guarded_lets_interrupts_through():
    @guarded
    def interrupted() -> Result[int]:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        interrupted()
