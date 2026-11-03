"""Langages M2 et programmes M1 : procédures écrites en Hypomnesis (effets comme
valeurs), interprétées par le moteur M3."""

import json
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import ContractError
from hypomnesis.engine.language import LanguageError, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.epistemics.provenance import Support
from hypomnesis.language.errors import EvaluationError, TypeCheckError

ROOT = Path(__file__).resolve().parents[2]
MECANIQUE = ROOT / "languages" / "mecanique"
VENTILATION = ROOT / "languages" / "ventilation"
PLAQUE = (ROOT / "programs" / "mecanique" / "plaque_120x80.hyp").read_text()
MESUREE = (ROOT / "programs" / "mecanique" / "plaque_mesuree.hyp").read_text()
SALLE = (ROOT / "programs" / "ventilation" / "salle_serveurs.hyp").read_text()


def plaque(tmp_path, program=PLAQUE, **kwargs):
    return run_procedure(load_language(MECANIQUE), program, out_dir=tmp_path, **kwargs)


# ------------------------------------------------------------- mécanique (M2)


def test_design_end_to_end_in_production(tmp_path):
    report = plaque(tmp_path, mode="production")
    kb = report.kb
    assert report.result == "Valide"
    assert kb.value("demande.epaisseur") == 3  # standard, au plus près de l'estimation 3.2
    assert [o.state for o in report.commands] == ["Completed", "Completed"]
    assert (tmp_path / "plaque-support.svg").read_text().startswith("<svg")
    saved = json.loads((tmp_path / "rapport.json").read_text())
    names = {s["name"] for s in saved["trace"]["spans"]}
    assert {"hypomnesis.run", "solver.solve", "actuator.execute"} <= names


def test_validity_inherits_the_support_of_the_estimate(tmp_path):
    kb = plaque(tmp_path).kb
    assert kb.support("demande.largeur") is Support.OBSERVED
    assert kb.support("demande.valide") is Support.ESTIMATED
    assert kb.confidence("demande.valide") == pytest.approx(0.6)


def test_the_m1_program_chooses_the_estimator(tmp_path):
    a = plaque(tmp_path / "a")
    b = plaque(tmp_path / "b", PLAQUE.replace("estimateur_regle", "estimateur_abaque"))
    assert a.kb.value("epaisseur.estimation") != b.kb.value("epaisseur.estimation")
    assert "abaque" in b.kb.facts["epaisseur.estimation"].method


def test_constraints_declared_in_the_language_drive_the_solver(tmp_path):
    program = PLAQUE.replace("masse_max = 0.5", "masse_max = 0.2").replace(
        "estimateur_regle", "estimateur_abaque"
    )
    kb = plaque(tmp_path, program).kb
    assert kb.value("epaisseur.estimation") == 3  # 0.226 kg : trop lourd
    assert kb.value("demande.epaisseur") == 2


def test_infeasible_requirements(tmp_path):
    report = plaque(tmp_path, PLAQUE.replace("masse_max = 0.5", "masse_max = 0.01"))
    assert report.result == "Impossible" and not report.commands


def test_known_value_skips_estimation(tmp_path):
    kb = plaque(tmp_path, PLAQUE.replace("epaisseur = None", "epaisseur = Some 4.0")).kb
    assert "epaisseur.estimation" not in kb.facts
    assert kb.support("demande.valide") is Support.OBSERVED


def test_measurement_revises_the_design_inside_the_language(tmp_path):
    report = plaque(tmp_path, MESUREE, environment={"mesure": "5"})
    kb = report.kb
    assert "epaisseur.estimation" not in kb.facts
    assert kb.value("demande.epaisseur") == 5
    assert kb.support("demande.valide") is Support.OBSERVED
    assert any("invalidés" in note for note in report.notes)
    assert [e.kind for e in kb.journal].count("invalidated") == 4  # historique conservé


def test_dry_run_and_missing_permission_never_reach_the_actuator(tmp_path):
    dry = plaque(tmp_path / "a", mode="dry-run")
    assert [o.state for o in dry.commands] == ["DryRun", "DryRun"]
    denied = plaque(tmp_path / "b", mode="production", permissions=frozenset())
    assert all(o.state == "Rejected" and not o.dispatched for o in denied.commands)
    assert not list((tmp_path / "b").glob("*.svg"))


def test_command_escaping_the_output_directory_is_rejected(tmp_path):
    report = plaque(
        tmp_path / "out", PLAQUE.replace('"plaque-support"', '"../evasion"'), mode="production"
    )
    assert all("contraintes métier" in o.states[-1][1] for o in report.commands)
    assert not (tmp_path / "evasion.svg").exists()


def test_ill_typed_program_is_refused_before_any_effect(tmp_path):
    with pytest.raises(TypeCheckError):
        plaque(tmp_path, PLAQUE.replace("largeur = 120.0", 'largeur = "120"'))
    assert not (tmp_path / "rapport.json").exists()


# ------------------------------------------------------------ garde-fous du moteur


def test_a_program_cannot_rely_on_missing_premises(tmp_path):
    program = 'let procedure = Effect.record "x" 1 "?" (Effect.Derived ["inexistant"])'
    with pytest.raises(EvaluationError, match="prémisses inconnues") as raised:
        plaque(tmp_path, program)
    assert "Faits connus à ce point : aucun" in raised.value.message


def test_retracting_an_unrecorded_fact_lists_the_known_ones(tmp_path):
    program = (
        'let procedure = Effect.record "a" 1 "?" Effect.Given >>= fun () -> '
        'Effect.retract "b" "?" >>= fun _ -> Effect.return 0'
    )
    with pytest.raises(EvaluationError, match="retrait d'un fait inconnu : b") as raised:
        plaque(tmp_path, program)
    assert "Faits connus à ce point : a" in raised.value.message


def test_undeclared_sensor_is_refused(tmp_path):
    with pytest.raises(LanguageError, match="capteur non déclaré"):
        plaque(tmp_path, 'let procedure = Effect.observe "micro-espion"')


def test_entry_must_be_a_procedure(tmp_path):
    with pytest.raises(LanguageError, match=r"Effect\.t"):
        plaque(tmp_path, "let procedure = 42")


def test_runaway_procedure_is_stopped_by_the_step_budget(tmp_path):
    program = (
        'let rec boucle () = Effect.note "x" >>= fun () -> boucle ()\nlet procedure = boucle ()'
    )
    report = plaque(tmp_path, program, max_steps=50)
    assert "budget" in report.stopped and len(report.notes) == 50


# ------------------------------------------------------------ ventilation (M2)


def salle(program=SALLE, **env):
    return run_procedure(load_language(VENTILATION), program, mode="production", environment=env)


def test_working_fan_confirms_the_effect():
    report = salle()
    assert report.result == "aucune action nécessaire"
    assert report.kb.support("effet_confirme.1") is Support.OBSERVED
    assert report.kb.support("effet_attendu.1") is Support.HYPOTHESIS


def test_broken_fan_refutes_the_hypothesis():
    report = salle(panne="1")
    kb = report.kb
    assert "hypothese" not in kb.facts and "effet_attendu.1" not in kb.facts
    assert kb.support("hypothese.refutee") is Support.OBSERVED


def test_regulation_loop_is_bounded_by_the_program():
    report = salle(SALLE.replace("budget = 5", "budget = 1"), temperature="60")
    assert len(report.commands) == 1 and report.result == "budget épuisé"


def test_sensor_message_outside_its_contract_is_rejected():
    with pytest.raises(ContractError):
        salle(temperature="999")


# ---------------------------------------------------------------- CLI et manifestes


def test_cli_from_natural_language(tmp_path, capsys):
    request = "Crée une plaque de 200 × 150 mm, masse maximale 1 kg."
    assert main(["lancer", str(MECANIQUE), "--demande", request, "--sortie", str(tmp_path)]) == 0
    assert "épaisseur résolue : 4. mm" in capsys.readouterr().out


def test_cli_procedure(capsys, tmp_path):
    args = ["lancer", str(VENTILATION), str(ROOT / "programs/ventilation/salle_serveurs.hyp")]
    assert main([*args, "--env", "panne=1", "--sortie", str(tmp_path)]) == 0
    assert "hypothèse réfutée" in capsys.readouterr().out


def test_invalid_manifest_is_refused(tmp_path):
    (tmp_path / "langage.json").write_text(json.dumps({"name": "x", "version": "1", "sources": []}))
    with pytest.raises(LanguageError, match="manifeste invalide"):
        load_language(tmp_path)


def test_adapters_must_live_inside_the_language():
    with pytest.raises(LanguageError, match="hors du paquet"):
        load_language(MECANIQUE).adapter("../../src/hypomnesis/cli.py:main")


# ------------------------------------------------------------------ architecture


def test_engine_contains_no_domain():
    """M3 ne connaît aucun langage M2 : aucun nom de domaine dans le moteur."""
    words = ("plaque", "ventil", "epaisseur", "geometry.export", "fan.set", "celsius", "coulisse")
    offenders = [
        f"{path.relative_to(ROOT)}: {word}"
        for path in (ROOT / "src" / "hypomnesis").rglob("*")
        if path.suffix in (".py", ".hyp", ".json", ".lark")
        for word in words
        if word in path.read_text(encoding="utf-8").lower()
    ]
    assert offenders == []
