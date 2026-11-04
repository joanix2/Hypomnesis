"""Exhaustive executable parity of the Lean and Python command automata."""

import json
import shutil
import subprocess
from pathlib import Path

from hypomnesis.effects.commands import State, can_move

FORMAL = Path(__file__).resolve().parents[2] / "formal"


def test_lean_and_python_agree_on_every_state_pair():
    lake = shutil.which("lake") or str(Path.home() / ".elan/bin/lake")
    build = subprocess.run(
        [lake, "build", "Hypomnesis.Effects.Dispatch"],
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
    matrix = json.loads(result.stdout)
    assert len(matrix) == len(State) ** 2
    pairs = {(source, target): allowed for source, target, allowed in matrix}
    assert len(pairs) == len(matrix)
    assert set(pairs) == {(s.value, t.value) for s in State for t in State}
    for (source, target), allowed in pairs.items():
        assert type(allowed) is bool
        assert allowed is can_move(State(source), State(target)), (source, target)
