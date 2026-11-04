"""Exercise the actual proof CI guard without adding invalid proofs to the repository."""

import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


@pytest.mark.parametrize(
    ("proof", "expected"),
    [
        ("theorem probe : True := by trivial\n", 0),
        ("theorem probe : True := by sorry\n", 1),
        ("theorem probe : True := by admit\n", 1),
    ],
)
def test_proof_ci_rejects_placeholder(tmp_path, proof, expected):
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    guard = next(
        step for step in workflow["jobs"]["proofs"]["steps"] if step.get("name") == "Reject sorry"
    )
    source = tmp_path / "Hypomnesis" / "Nested" / "Probe.lean"
    source.parent.mkdir(parents=True)
    source.write_text(proof, encoding="utf-8")
    result = subprocess.run(
        ["bash", "-c", guard["run"]], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == expected, result.stdout + result.stderr
