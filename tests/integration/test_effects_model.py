"""Exhaustive executable parity of the Lean and Python command automata."""

import json
import subprocess
from pathlib import Path

import pytest

from hypomnesis.effects.commands import (
    TERMINAL,
    CommandRecord,
    RetryPolicy,
    State,
    can_move,
    may_retry,
)

FORMAL = Path(__file__).resolve().parents[2] / "formal"


@pytest.fixture(scope="module")
def tables(lean_lake):
    lake = lean_lake
    build = subprocess.run(
        [lake, "build", "Hypomnesis.Effects.Commands"],
        cwd=FORMAL,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    result = subprocess.run(
        [lake, "env", "lean", "EffectsTable.lean"],
        cwd=FORMAL,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_lean_and_python_agree_on_every_state_pair(tables):
    matrix = tables["transitions"]
    assert len(matrix) == len(State) ** 2
    pairs = {(source, target): allowed for source, target, allowed in matrix}
    assert len(pairs) == len(matrix)
    assert set(pairs) == {(s.value, t.value) for s in State for t in State}
    for (source, target), allowed in pairs.items():
        assert type(allowed) is bool
        assert allowed is can_move(State(source), State(target)), (source, target)


def test_lean_and_python_agree_on_terminal_states(tables):
    rows = tables["terminal"]
    assert len(rows) == len(State) and {s for s, _ in rows} == {s.value for s in State}
    for state, terminal in rows:
        assert type(terminal) is bool
        assert terminal is (State(state) in TERMINAL)


def test_lean_and_python_agree_on_retry_guards(tables):
    rows = tables["retry"]
    assert len(rows) == len(State) * 2 * 4 * 4
    assert len({tuple(row[:4]) for row in rows}) == len(rows)
    for state, idempotent, count, limit, allowed in rows:
        record = CommandRecord("c")
        record.history = [(State.DISPATCHED, "")] * count
        if State(state) != State.DISPATCHED:
            record.history.append((State(state), ""))
        assert record.attempts == count
        assert type(allowed) is bool
        assert allowed is may_retry(record, idempotent, RetryPolicy(max_attempts=limit))
