from pathlib import Path

import pytest

from hypomnesis.backends import z3_solver
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.ir.problem import Solution
from hypomnesis.language.errors import EvaluationError

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/solveur"
PROGRAM = (ROOT / "demo/programs/solveur/domaines.hyp").read_text()


def test_typed_effect_returns_exact_nominal_model_to_m1(tmp_path):
    report = run_procedure(load_language(LANGUAGE), PROGRAM, out_dir=tmp_path)
    assert report.result["verdict"] == {"tag": "Sat"}
    assert dict(report.result["assignment"]) == {
        "entier": {"tag": "IntegerValue", "arg": 2},
        "reel": {"tag": "Rational", "arg": [1, 3]},
        "booleen": {"tag": "BooleanValue", "arg": True},
    }
    assert report.result["duration_ms"] >= 0
    assert not report.commands and not report.kb.facts
    assert any(span.name == "solver.solve" for span in report.tracer.spans)


@pytest.mark.parametrize(("status", "reason"), [("unsat", ""), ("unknown", "timeout")])
def test_typed_effect_distinguishes_unsat_and_unknown(tmp_path, monkeypatch, status, reason):
    monkeypatch.setattr(
        z3_solver, "solve", lambda p: Solution(status, reason=reason, duration_ms=1.0)
    )
    report = run_procedure(load_language(LANGUAGE), PROGRAM, out_dir=tmp_path)
    assert report.result["verdict"] == {"tag": status.capitalize()}
    assert report.result["assignment"] == []
    assert report.result["reason"] == (
        {"tag": "Some", "arg": reason} if reason else {"tag": "None"}
    )


def test_kernel_rejects_plugin_model_even_when_plugin_claims_no_violations(tmp_path, monkeypatch):
    monkeypatch.setattr(
        z3_solver,
        "solve",
        lambda p: Solution("sat", {"entier": 2, "reel": 0, "booleen": True}),
    )
    with pytest.raises(EvaluationError, match="solution refusée"):
        run_procedure(load_language(LANGUAGE), PROGRAM, out_dir=tmp_path)
    assert not (tmp_path / "rapport.json").exists()
