"""Ordered validation, host permissions and explicit human approval (HYP-062)."""

from dataclasses import replace

import pytest

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator, Command, Dispatcher
from hypomnesis.effects.permissions import PermissionPolicy

CMD = "https://test.example/command/1.0.0"
RES = "https://test.example/result/1.0.0"


def registry():
    return SchemaRegistry(
        [
            {
                "$id": CMD,
                "type": "object",
                "properties": {"command_id": {"type": "string"}, "value": {"type": "integer"}},
                "required": ["command_id", "value"],
                "additionalProperties": False,
            },
            {
                "$id": RES,
                "type": "object",
                "properties": {"status": {"const": "ok"}},
                "required": ["status"],
                "additionalProperties": False,
            },
        ]
    )


def setup(*, permissions=None, mode="production", **kwargs):
    calls = []

    def execute(payload):
        calls.append(dict(payload))
        return {"status": "ok"}

    dispatcher = Dispatcher(
        registry(), {"move"} if permissions is None else permissions, mode, **kwargs
    )
    dispatcher.register(Actuator("motor", "move", CMD, RES, execute))
    return dispatcher, calls


def test_all_nine_steps_are_ordered_and_result_recorded_before_observation():
    d, calls = setup(approve=lambda c: c.payload["value"] == 2)
    observed = []

    def observe(payload, result):
        assert d.history[-1].result == result
        observed.append((payload, result))
        return []

    d.register(
        replace(
            d.actuators["motor"],
            requires_human=True,
            observe_effects=observe,
        )
    )
    outcome = d.dispatch(d.command("motor", {"value": 2}))
    assert outcome.state == "Completed"
    assert [c.stage for c in outcome.checks] == [
        "structure",
        "contract",
        "permission",
        "business",
        "safety",
        "approval",
        "execute",
        "response",
        "result",
        "observation",
    ]
    assert all(c.passed for c in outcome.checks)
    assert len(calls) == len(observed) == 1
    assert d.dispatch(outcome.command) is outcome
    assert len(calls) == 1


@pytest.mark.parametrize(
    "stage", ["structure", "contract", "permission", "business", "safety", "approval"]
)
def test_each_rejection_stops_before_execution_and_later_checks(stage):
    d, calls = setup(permissions=set() if stage == "permission" else None)
    payload = {"value": 2}
    if stage == "structure":
        payload["value"] = float("nan")
    if stage == "contract":
        payload["value"] = "not an integer"
    if stage in ("business", "safety"):
        attribute = "constraints" if stage == "business" else "safety"
        d.register(replace(d.actuators["motor"], **{attribute: lambda _: ["refused"]}))
    if stage == "approval":
        d.register(replace(d.actuators["motor"], requires_human=True))
    outcome = d.dispatch(d.command("motor", payload))
    assert outcome.state == "Rejected"
    assert not outcome.dispatched and not calls
    assert outcome.checks[-1].stage == stage and not outcome.checks[-1].passed


def test_policy_is_exact_and_explicit_denial_overrides_grant():
    policy = PermissionPolicy(frozenset({"move", "read"}), frozenset({"move"}))
    assert not policy.permits("move") and not policy.permits("read:other")
    assert policy.permits("read")
    d, calls = setup(policy=policy)
    assert d.dispatch(d.command("motor", {"value": 1})).state == "Rejected"
    assert not calls
    with pytest.raises(ValueError):
        PermissionPolicy({"move"})


@pytest.mark.parametrize("answer", [False, None, "yes", 1])
def test_human_approval_requires_explicit_true(answer):
    d, calls = setup(approve=lambda _: answer)
    d.register(replace(d.actuators["motor"], requires_human=True))
    assert d.dispatch(d.command("motor", {"value": 1})).state == "Rejected"
    assert not calls


def test_missing_result_contract_rejects_before_execute():
    d, calls = setup()
    d.register(replace(d.actuators["motor"], result_schema="https://test.example/missing/1.0.0"))
    assert d.dispatch(d.command("motor", {"value": 1})).state == "Rejected"
    assert not calls


def test_simulation_response_is_validated_without_physical_execution():
    d, calls = setup(mode="simulate")
    d.register(replace(d.actuators["motor"], simulate=lambda _: {"wrong": True}))
    outcome = d.dispatch(d.command("motor", {"value": 1}))
    assert outcome.state == "Rejected" and outcome.result is None
    assert not calls and not outcome.dispatched


def test_dry_run_stops_after_all_preconditions():
    d, calls = setup(mode="dry-run")
    outcome = d.dispatch(d.command("motor", {"value": 1}))
    assert outcome.state == "DryRun"
    assert outcome.checks[-1].stage == "safety"
    assert not calls


def test_observation_failure_is_reported_with_result_preserved():
    d, calls = setup()
    d.register(replace(d.actuators["motor"], observe_effects=lambda *_: ["not reached"]))
    outcome = d.dispatch(d.command("motor", {"value": 1}))
    assert len(calls) == 1 and outcome.state == "Failed"
    assert outcome.result == {"status": "ok"}
    assert outcome.checks[-1].stage == "observation" and not outcome.checks[-1].passed


def test_json_object_keys_and_arrays_are_not_coerced():
    d, calls = setup()
    for bad in [{1: 2}, {"value": (1, 2)}]:
        outcome = d.dispatch(d.command("motor", bad))
        assert outcome.state == "Rejected"
        assert outcome.checks[-1].stage == "structure"
    assert not calls


def test_check_callbacks_cannot_mutate_command_payload():
    d, calls = setup()

    def mutate(payload):
        payload["value"] = 100
        return []

    d.register(replace(d.actuators["motor"], constraints=mutate, safety=mutate))
    command = Command("external-id", "motor", {"command_id": "external-id", "value": 1})
    assert d.dispatch(command).state == "Completed"
    assert calls[0]["value"] == 1 and command.payload["value"] == 1


@pytest.mark.parametrize("stage", ["business", "safety", "approval", "observation"])
def test_callback_errors_are_recorded_and_not_success_shaped(stage):
    d, calls = setup()

    def fail(*_):
        raise RuntimeError("unavailable")

    if stage == "approval":
        d._approve = fail
        d.register(replace(d.actuators["motor"], requires_human=True))
    else:
        attribute = {
            "business": "constraints",
            "safety": "safety",
            "observation": "observe_effects",
        }[stage]
        d.register(replace(d.actuators["motor"], **{attribute: fail}))
    outcome = d.dispatch(d.command("motor", {"value": 1}))
    assert outcome.state == ("Failed" if stage == "observation" else "Rejected")
    assert len(calls) == (1 if stage == "observation" else 0)
    assert not outcome.checks[-1].passed
    assert "RuntimeError: unavailable" in outcome.checks[-1].detail


def test_command_identifier_must_match_payload_identifier():
    d, calls = setup()
    outcome = d.dispatch(Command("first", "motor", {"command_id": "other", "value": 1}))
    assert outcome.state == "Rejected"
    assert not calls


@pytest.mark.parametrize("mode", ["simulate", "production"])
@pytest.mark.parametrize("result", [{"value": float("inf")}, {1: "not a key"}, {"x": (1,)}, None])
def test_response_must_be_strict_json_even_with_an_open_contract(mode, result):
    d, _ = setup(mode=mode)
    schema = d.registry.add({"$id": "https://test.example/open/1.0.0"})
    d.register(
        replace(
            d.actuators["motor"],
            result_schema=schema,
            execute=lambda _: result,
            simulate=lambda _: result,
        )
    )
    outcome = d.dispatch(d.command("motor", {"value": 1}))
    assert outcome.state == ("Rejected" if mode == "simulate" else "Failed")
    assert outcome.result is None
    assert outcome.checks[-1].stage == "response" and not outcome.checks[-1].passed


def test_simulation_error_is_rejected_and_cached_without_retry():
    d, calls = setup(mode="simulate")

    def fail(_):
        raise RuntimeError("no fake device")

    d.register(replace(d.actuators["motor"], simulate=fail))
    command = d.command("motor", {"value": 1})
    outcome = d.dispatch(command)
    assert outcome.state == "Rejected"
    assert "no fake device" in outcome.checks[-1].detail
    assert d.dispatch(command) is outcome and not calls


@pytest.mark.parametrize("mode", ["simulate", "dry-run", "production"])
def test_handlers_share_checks_but_only_use_the_selected_execution(mode):
    d, calls = setup(mode=mode)
    simulated = []
    d.register(
        replace(
            d.actuators["motor"],
            simulate=lambda p: simulated.append(dict(p)) or {"status": "ok"},
        )
    )
    outcome = d.dispatch(d.command("motor", {"value": 2}))
    assert [c.stage for c in outcome.checks[:5]] == [
        "structure",
        "contract",
        "permission",
        "business",
        "safety",
    ]
    assert len(calls) == (1 if mode == "production" else 0)
    assert len(simulated) == (1 if mode == "simulate" else 0)
    assert outcome.attempts == (1 if mode == "production" else 0)


@pytest.mark.parametrize("mode", ["simulate", "dry-run", "production"])
def test_every_handler_remains_gated_by_common_safety(mode):
    d, calls = setup(mode=mode)
    simulated = []
    d.register(
        replace(
            d.actuators["motor"],
            safety=lambda _: ["unsafe"],
            simulate=lambda p: simulated.append(dict(p)) or {"status": "ok"},
        )
    )
    outcome = d.dispatch(d.command("motor", {"value": 2}))
    assert outcome.state == "Rejected"
    assert not calls and not simulated
    assert not outcome.dispatched
