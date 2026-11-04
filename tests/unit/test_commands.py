"""Automate des commandes : transitions, déduplication, délais, relances (HYP-061)."""

import itertools
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.commands import (
    NO_RETRY,
    TERMINAL,
    TRANSITIONS,
    CommandRecord,
    IllegalTransition,
    RetryPolicy,
    State,
    TransportError,
    can_move,
    may_retry,
)
from hypomnesis.effects.dispatcher import Actuator, Command, Dispatcher, DuplicateCommand

CMD = "urn:test:cmd/v1"
RES = "urn:test:res/v1"
REGISTRY = SchemaRegistry(
    [
        {"$id": CMD, "type": "object", "required": ["command_id"]},
        {"$id": RES, "type": "object"},
    ]
)


class FakeTime:
    """Injected clock and sleep: time only moves when the code under test sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class Device:
    """A scripted actuator: each call consumes a step ``(acted, answer)``.

    ``acted`` says whether the physical action happened; ``answer`` is ``ok``,
    ``transport`` (no reliable answer, even if the action happened) or ``error``.
    """

    def __init__(
        self, script: list[tuple[bool, str]], tick: float = 0.0, time: FakeTime | None = None
    ):
        self.script = itertools.chain(script, itertools.repeat((False, "ok")))
        self.calls = 0
        self.acted = 0
        self.tick = tick
        self.time = time

    def __call__(self, payload: Any) -> dict[str, Any]:
        self.calls += 1
        acted, answer = next(self.script)
        self.acted += acted
        if self.time is not None:
            self.time.now += self.tick
        if answer == "transport":
            raise TransportError("pas de réponse")
        if answer == "error":
            raise RuntimeError("panne")
        return {"status": "ok"}


def make(
    device: Device,
    *,
    idempotent: bool = False,
    retry: RetryPolicy = NO_RETRY,
    timeout: float | None = None,
    time: FakeTime | None = None,
) -> tuple[Dispatcher, Command]:
    time = time or FakeTime()
    dispatcher = Dispatcher(REGISTRY, {"p"}, "production", clock=time.clock, sleep=time.sleep)
    dispatcher.register(
        Actuator("a", "p", CMD, RES, device, idempotent=idempotent, retry=retry, timeout=timeout)
    )
    return dispatcher, dispatcher.command("a", {})


def names(outcome: Any) -> list[str]:
    return [s for s, _ in outcome.states]


# --- the automaton ------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "target"), list(itertools.product(State, State)), ids=lambda s: s.value
)
def test_every_pair_is_allowed_exactly_when_the_table_says_so(source: State, target: State):
    record = CommandRecord("c")
    record.history = [(source, "")]
    if target in TRANSITIONS[source]:
        assert can_move(source, target)
        record.move(target)
        assert record.state is target
    else:
        assert not can_move(source, target)
        with pytest.raises(IllegalTransition):
            record.move(target)
        assert record.state is source  # a refused move leaves the journal untouched


def test_the_table_covers_every_state():
    assert set(TRANSITIONS) == set(State)


def test_terminal_states_are_absorbing():
    expected = {
        State.COMPLETED,
        State.REJECTED,
        State.FAILED,
        State.TIMED_OUT,
        State.UNKNOWN_OUTCOME,
        State.DRY_RUN,
        State.SIMULATED,
    }
    assert expected == TERMINAL
    for state in TERMINAL:
        assert TRANSITIONS[state] == frozenset()


def test_happy_path_follows_the_specification():
    path = [
        State.VALIDATED,
        State.AUTHORIZED,
        State.DISPATCHED,
        State.ACCEPTED,
        State.COMPLETED,
    ]
    record = CommandRecord("c")
    for state in path:
        record.move(state)
    assert record.terminal and record.attempts == 1


def test_no_state_reaches_dispatched_without_authorization():
    predecessors = {s for s, targets in TRANSITIONS.items() if State.DISPATCHED in targets}
    assert predecessors == {State.AUTHORIZED, State.DISPATCHED}


# --- dispatcher: behaviour unchanged ------------------------------------------


def test_successful_command_states():
    dispatcher, command = make(Device([]))
    outcome = dispatcher.dispatch(command)
    assert names(outcome) == ["Created", "Validated", "Authorized", "Dispatched", "Completed"]
    assert outcome.state == "Completed" and outcome.dispatched
    assert outcome.result == {"status": "ok"}


def test_actuator_error_is_failed_and_not_retried():
    device = Device([(False, "error")])
    dispatcher, command = make(device, idempotent=True, retry=RetryPolicy(max_attempts=5))
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "Failed" and device.calls == 1


def test_transition_callback_sees_every_state():
    seen: list[str] = []
    dispatcher = Dispatcher(
        REGISTRY, {"p"}, "production", on_transition=lambda c, s, d: seen.append(s)
    )
    dispatcher.register(Actuator("a", "p", CMD, RES, Device([])))
    dispatcher.dispatch(dispatcher.command("a", {}))
    assert seen == ["Created", "Validated", "Authorized", "Dispatched", "Completed"]


# --- deduplication ------------------------------------------------------------


def test_same_command_id_is_not_executed_twice():
    device = Device([])
    dispatcher, command = make(device)
    first = dispatcher.dispatch(command)
    again = dispatcher.dispatch(command)
    assert again is first and device.calls == 1
    assert len(dispatcher.history) == 1


def test_same_id_with_another_content_is_refused():
    dispatcher, command = make(Device([]))
    dispatcher.dispatch(command)
    with pytest.raises(DuplicateCommand):
        dispatcher.dispatch(
            Command(command.id, command.actuator, {"command_id": command.id, "x": 1})
        )


def test_deduplication_also_covers_refused_commands():
    dispatcher = Dispatcher(REGISTRY, set(), "production")
    dispatcher.register(Actuator("a", "p", CMD, RES, Device([])))
    command = dispatcher.command("a", {})
    assert dispatcher.dispatch(command).state == "Rejected"
    dispatcher.permissions.add("p")  # a later grant does not resurrect a refused command
    assert dispatcher.dispatch(command).state == "Rejected"


# --- retries ------------------------------------------------------------------


def test_non_idempotent_command_is_never_retried():
    device = Device([(True, "transport")])
    dispatcher, command = make(device, retry=RetryPolicy(max_attempts=5))
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "UnknownOutcome" and device.calls == 1
    assert "aucune relance" in outcome.states[-1][1]


def test_idempotent_command_is_retried_up_to_the_limit():
    device = Device([(False, "transport")] * 2)
    time = FakeTime()
    policy = RetryPolicy(max_attempts=3, delay=1.0, backoff=2.0)
    dispatcher, command = make(device, idempotent=True, retry=policy, time=time)
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "Completed" and device.calls == 3 and outcome.attempts == 3
    assert time.sleeps == [1.0, 2.0]  # injected sleep: nothing really waits


def test_retries_are_bounded():
    device = Device([(True, "transport")] * 10)
    dispatcher, command = make(device, idempotent=True, retry=RetryPolicy(max_attempts=3))
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "UnknownOutcome" and device.calls == 3
    assert "relances épuisées" in outcome.states[-1][1]


def test_may_retry_guard():
    record = CommandRecord("c")
    for state in (State.VALIDATED, State.AUTHORIZED, State.DISPATCHED):
        record.move(state)
    policy = RetryPolicy(max_attempts=2)
    assert may_retry(record, True, policy)
    assert not may_retry(record, False, policy)
    record.move(State.DISPATCHED)  # second attempt: the budget is spent
    assert not may_retry(record, True, policy)
    record.move(State.UNKNOWN_OUTCOME)
    assert not may_retry(record, True, RetryPolicy(max_attempts=9))


def test_retry_policy_validation():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        RetryPolicy(delay=-1)
    assert RetryPolicy(delay=2, backoff=3).delay_after(3) == 18


# --- expiry -------------------------------------------------------------------


def test_late_answer_times_out():
    time = FakeTime()
    device = Device([], tick=5.0, time=time)
    dispatcher, command = make(device, timeout=3.0, time=time)
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "TimedOut" and outcome.result is None
    assert device.calls == 1


def test_deadline_stops_retries():
    time = FakeTime()
    device = Device([(False, "transport")] * 5, tick=1.0, time=time)
    policy = RetryPolicy(max_attempts=5, delay=2.0)
    dispatcher, command = make(device, idempotent=True, retry=policy, timeout=4.0, time=time)
    outcome = dispatcher.dispatch(command)
    assert outcome.state == "TimedOut" and device.calls < 5


def test_answer_within_the_deadline_completes():
    time = FakeTime()
    dispatcher, command = make(Device([], tick=1.0, time=time), timeout=3.0, time=time)
    assert dispatcher.dispatch(command).state == "Completed"


# --- simulated transport failures: at most one execution ---------------------

STEP = st.tuples(st.booleans(), st.sampled_from(["ok", "transport", "error"]))


@given(
    script=st.lists(STEP, max_size=12),
    max_attempts=st.integers(1, 6),
    redeliveries=st.integers(0, 5),
)
def test_non_idempotent_command_acts_at_most_once(script, max_attempts, redeliveries):
    device = Device(script)
    dispatcher, command = make(device, retry=RetryPolicy(max_attempts=max_attempts))
    for _ in range(1 + redeliveries):  # the transport redelivers the same command
        dispatcher.dispatch(command)
    assert device.calls <= 1 and device.acted <= 1


@given(script=st.lists(STEP, max_size=12), max_attempts=st.integers(1, 6))
def test_idempotent_retries_never_exceed_the_budget(script, max_attempts):
    device = Device(script)
    dispatcher, command = make(
        device, idempotent=True, retry=RetryPolicy(max_attempts=max_attempts)
    )
    outcome = dispatcher.dispatch(command)
    assert device.calls == outcome.attempts <= max_attempts
    assert outcome.record.terminal
