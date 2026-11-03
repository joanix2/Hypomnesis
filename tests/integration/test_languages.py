"""Langages M2 et programmes M1 exécutés par les procédures génériques du moteur (M3)."""

import json
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import ContractError
from hypomnesis.engine.design import run_design
from hypomnesis.engine.feedback import run_feedback
from hypomnesis.engine.language import LanguageError, load_language
from hypomnesis.epistemics.provenance import Support

ROOT = Path(__file__).resolve().parents[2]
MECANIQUE = ROOT / "languages" / "mecanique"
VENTILATION = ROOT / "languages" / "ventilation"
PLAQUE = (ROOT / "programs" / "mecanique" / "plaque_120x80.hyp").read_text()
SALLE = (ROOT / "programs" / "ventilation" / "salle_serveurs.hyp").read_text()


def design(tmp_path, program=PLAQUE, **kwargs):
    return run_design(load_language(MECANIQUE), program, out_dir=tmp_path, **kwargs)


# ------------------------------------------------------- conception sous contraintes


def test_end_to_end_in_production(tmp_path):
    report = design(tmp_path, mode="production")
    kb = report.kb
    assert kb.value("demande.epaisseur") == 3.0  # standard, au plus près de l'estimation 3.2
    assert report.verdict == "Valide"
    assert [o.state for o in report.commands] == ["Completed", "Completed"]
    assert (tmp_path / "plaque-support.svg").read_text().startswith("<svg")
    saved = json.loads((tmp_path / "rapport.json").read_text())
    assert saved["knowledge"]["demande.valide"]["support"] == "estimé"
    names = {s["name"] for s in saved["trace"]["spans"]}
    assert {"hypomnesis.run", "estimator.predict", "solver.solve", "validator.check"} <= names


def test_support_and_confidence_propagate(tmp_path):
    kb = design(tmp_path).kb
    assert kb.support("demande.largeur") is Support.OBSERVED
    assert kb.support("demande.valide") is Support.ESTIMATED
    assert kb.confidence("demande.valide") == pytest.approx(0.6)


def test_swapping_the_estimator_keeps_the_program(tmp_path):
    a, b = design(tmp_path, estimator="regle"), design(tmp_path, estimator="abaque")
    assert a.program == b.program
    assert a.kb.value("demande.epaisseur.estimation") != b.kb.value("demande.epaisseur.estimation")


def test_constraints_declared_in_the_language_drive_the_solver(tmp_path):
    program = PLAQUE.replace("masse_max = 0.5", "masse_max = 0.2")
    report = design(tmp_path, program, estimator="abaque")
    assert report.kb.value("demande.epaisseur.estimation") == 3.0  # 0.226 kg : trop lourd
    assert report.kb.value("demande.epaisseur") == 2.0


def test_infeasible_requirements(tmp_path):
    report = design(tmp_path, PLAQUE.replace("masse_max = 0.5", "masse_max = 0.01"))
    assert report.verdict == "Impossible" and not report.commands


def test_known_value_skips_estimation(tmp_path):
    report = design(tmp_path, PLAQUE.replace("epaisseur = None", "epaisseur = Some 4.0"))
    assert "demande.epaisseur.estimation" not in report.kb.facts
    assert report.kb.support("demande.valide") is Support.OBSERVED


def test_observation_revises_dependent_conclusions(tmp_path):
    report = design(tmp_path, observations={"epaisseur": 5.0})
    assert set(report.revision) == {
        "demande.epaisseur.estimation",
        "demande.epaisseur",
        "demande.masse_kg",
        "demande.valide",
    }
    assert report.kb.support("demande.valide") is Support.OBSERVED
    assert "estimé" in "\n".join(report.explanation_before)


def test_dry_run_and_missing_permission_never_reach_the_actuator(tmp_path):
    dry = design(tmp_path / "a", mode="dry-run")
    assert [o.state for o in dry.commands] == ["DryRun", "DryRun"]
    denied = design(tmp_path / "b", mode="production", permissions=frozenset())
    assert all(o.state == "Rejected" and not o.dispatched for o in denied.commands)
    assert not list((tmp_path / "b").glob("*.svg"))


def test_command_escaping_the_output_directory_is_rejected(tmp_path):
    program = PLAQUE.replace('"plaque-support"', '"../evasion"')
    report = design(tmp_path / "out", program, mode="production")
    assert all(
        o.state == "Rejected" and "contraintes métier" in o.states[-1][1] for o in report.commands
    )
    assert not (tmp_path / "evasion.svg").exists()


def test_ill_typed_program_is_refused_before_any_effect(tmp_path):
    from hypomnesis.language.errors import TypeCheckError

    with pytest.raises(TypeCheckError):
        design(tmp_path, PLAQUE.replace("largeur = 120.0", 'largeur = "120"'))
    assert not (tmp_path / "rapport.json").exists()


# ------------------------------------------------------------ boucle de rétroaction


def loop(**env):
    return run_feedback(load_language(VENTILATION), SALLE, environment=env)


def test_working_actuator_confirms_the_effect():
    report = loop()
    assert report.conclusion == "aucune action nécessaire"
    assert report.kb.support("effet_confirme.c1") is Support.OBSERVED
    assert "hypothese" in report.kb.facts


def test_broken_actuator_refutes_the_hypothesis():
    report = loop(panne="1")
    kb = report.kb
    assert "hypothese" not in kb.facts and "effet_attendu.c1" not in kb.facts
    assert kb.support("hypothese.refutee") is Support.OBSERVED


def test_loop_is_bounded():
    report = run_feedback(
        load_language(VENTILATION),
        SALLE.replace("budget = 5", "budget = 1"),
        environment={"temperature": "60"},
    )
    assert len(report.commands) == 1 and "budget" in report.conclusion


def test_sensor_message_outside_its_contract_is_rejected():
    with pytest.raises(ContractError):
        loop(temperature="999")


# ---------------------------------------------------------------- CLI et manifestes


def test_cli_from_natural_language(tmp_path, capsys):
    request = "Crée une plaque de 200 × 150 mm, masse maximale 1 kg."
    assert main(["lancer", str(MECANIQUE), "--demande", request, "--sortie", str(tmp_path)]) == 0
    assert "epaisseur = 4.0" in capsys.readouterr().out


def test_cli_feedback(capsys):
    assert (
        main(
            [
                "lancer",
                str(VENTILATION),
                str(ROOT / "programs/ventilation/salle_serveurs.hyp"),
                "--env",
                "panne=1",
            ]
        )
        == 0
    )
    assert "hypothèse réfutée" in capsys.readouterr().out


def test_invalid_manifest_is_refused(tmp_path):
    (tmp_path / "langage.json").write_text(json.dumps({"name": "x", "version": "1", "sources": []}))
    with pytest.raises(LanguageError, match="manifeste invalide"):
        load_language(tmp_path)


def test_adapters_must_live_inside_the_language(tmp_path):
    language = load_language(MECANIQUE)
    with pytest.raises(LanguageError, match="hors du paquet"):
        language.adapter("../../src/hypomnesis/cli.py:main")


# ------------------------------------------------------------------ architecture


def test_engine_contains_no_domain():
    """M3 ne connaît aucun langage M2 : aucun nom de domaine dans le moteur."""
    words = ("plaque", "ventil", "epaisseur", "geometry.export", "fan.set", "celsius")
    offenders = [
        f"{path.relative_to(ROOT)}: {word}"
        for path in (ROOT / "src" / "hypomnesis").rglob("*")
        if path.suffix in (".py", ".hyp", ".json", ".lark")
        for word in words
        if word in path.read_text(encoding="utf-8").lower()
    ]
    assert offenders == []
