"""Démonstrateur MVP « plaque » (HYP-120) : critères d'acceptation."""

import json

import pytest

from hypomnesis.cli import main
from hypomnesis.demos.plaque.pipeline import TranscriptionError, run
from hypomnesis.epistemics.provenance import Support

REQUEST = (
    "Crée une plaque de 120 × 80 mm, estime son épaisseur, "
    "vérifie sa validité et exporte sa géométrie."
)


def test_end_to_end_in_production(tmp_path):
    report = run(REQUEST, mode="production", out_dir=tmp_path)
    kb = report.kb
    assert "Plaque.demande" in report.steps[0][1]  # programme typé
    assert kb.value("plaque.epaisseur") == 3.0  # standard, au plus près de l'estimation 3.2
    assert report.verdict == "Valide"
    assert [o.state for o in report.commands] == ["Completed", "Completed"]
    assert (tmp_path / "plaque.svg").read_text().startswith("<svg")
    assert json.loads((tmp_path / "plaque.json").read_text())["thickness_mm"] == 3.0
    saved = json.loads((tmp_path / "rapport.json").read_text())
    assert saved["knowledge"]["plaque.valide"]["support"] == "estimé"
    names = {s["name"] for s in saved["trace"]["spans"]}
    assert {"hypomnesis.run", "estimator.predict", "solver.solve", "validator.check"} <= names


def test_validity_inherits_the_support_of_the_estimate(tmp_path):
    kb = run(REQUEST, out_dir=tmp_path).kb
    assert kb.support("plaque.largeur") is Support.OBSERVED
    assert kb.support("plaque.epaisseur") is Support.ESTIMATED
    assert kb.support("plaque.valide") is Support.ESTIMATED
    assert kb.confidence("plaque.valide") == pytest.approx(0.6)


def test_swapping_the_estimator_keeps_the_program(tmp_path):
    a = run(REQUEST, estimator="regle", out_dir=tmp_path)
    b = run(REQUEST, estimator="abaque", out_dir=tmp_path)
    assert a.transcription.program == b.transcription.program
    assert a.kb.value("plaque.epaisseur_estimee") != b.kb.value("plaque.epaisseur_estimee")
    assert "abaque" in b.kb.facts["plaque.epaisseur_estimee"].method


def test_solver_respects_domain_rules_when_the_estimate_does_not(tmp_path):
    report = run(REQUEST, estimator="abaque", masse_max=0.2, out_dir=tmp_path)
    assert report.kb.value("plaque.epaisseur_estimee") == 3.0  # 0.226 kg : trop lourd
    assert report.kb.value("plaque.epaisseur") == 2.0
    assert report.verdict == "Valide"


def test_infeasible_requirements_are_reported(tmp_path):
    report = run(REQUEST, masse_max=0.01, out_dir=tmp_path)
    assert report.verdict == "Impossible"
    assert not report.commands


def test_measurement_revises_dependent_conclusions(tmp_path):
    report = run(REQUEST, out_dir=tmp_path, mesure=5.0)
    kb = report.kb
    assert set(report.revision) == {
        "plaque.epaisseur_estimee",
        "plaque.epaisseur",
        "plaque.masse_kg",
        "plaque.valide",
    }
    assert kb.value("plaque.epaisseur") == 5.0
    assert kb.support("plaque.valide") is Support.OBSERVED
    assert "estimé" in "\n".join(report.explanation_before)
    assert [e.kind for e in kb.journal].count("invalidated") == 4  # l'historique est conservé


def test_dry_run_never_reaches_the_actuator(tmp_path):
    report = run(REQUEST, mode="dry-run", out_dir=tmp_path)
    assert [o.state for o in report.commands] == ["DryRun", "DryRun"]
    assert not any(o.dispatched for o in report.commands)
    assert not (tmp_path / "plaque.svg").exists()


def test_unauthorised_command_never_reaches_the_actuator(tmp_path):
    report = run(REQUEST, mode="production", out_dir=tmp_path, permissions=frozenset())
    assert all(o.state == "Rejected" and not o.dispatched for o in report.commands)
    assert not (tmp_path / "plaque.svg").exists()


def test_invalid_command_is_rejected_by_contract(tmp_path):
    from hypomnesis.demos.plaque.pipeline import EXPORT_PERMISSION, export_actuator, schema_registry
    from hypomnesis.effects.dispatcher import Dispatcher

    dispatcher = Dispatcher(schema_registry(), {EXPORT_PERMISSION}, mode="production")
    dispatcher.register(export_actuator(tmp_path))
    bad = {
        "command_id": "x",
        "part": {"name": "p", "width_mm": -1, "height_mm": 1, "thickness_mm": 1},
        "format": "svg",
        "path": "p.svg",
    }
    escape = {**bad, "part": {**bad["part"], "width_mm": 10}, "path": "../evasion.svg"}
    for payload, reason in ((bad, "contrat"), (escape, "contraintes métier")):
        outcome = dispatcher.dispatch(dispatcher.command("geometry.export", payload))
        assert outcome.state == "Rejected" and reason in outcome.states[-1][1]
        assert not outcome.dispatched
    assert not (tmp_path.parent / "evasion.svg").exists()


def test_request_without_dimensions_is_refused():
    with pytest.raises(TranscriptionError):
        run("Crée une plaque, s'il te plaît.")


def test_cli_demo(tmp_path, capsys):
    assert main(["demo", "plaque", "--sortie", str(tmp_path), "--mesure", "5"]) == 0
    out = capsys.readouterr().out
    assert "Avant la mesure" in out and "support observé" in out
