"""M1/M2 feedback, epistemic revision and the pure/effect boundary."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from hypomnesis.effects.commands import TransportError
from hypomnesis.engine.language import LanguageError, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.engine.rules import RuleEngine, language_rule
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.provenance import Support
from hypomnesis.language.errors import EvaluationError

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/ventilation"
PROGRAM = (ROOT / "demo/programs/ventilation/salle_serveurs.hyp").read_text()


@pytest.mark.parametrize("broken", [False, True])
def test_distinct_confirmation_sensor_and_exact_revision_have_replayable_evidence(tmp_path, broken):
    report = run_procedure(
        load_language(LANGUAGE),
        PROGRAM,
        mode="production",
        out_dir=tmp_path,
        environment={"panne": broken, "transport": "files"},
    )
    base = report.kb
    assert len(report.commands) == 1 and report.commands[0].state == "Completed"
    assert base.value("thermo-1#1")["sensor_id"] == "thermo-1"
    assert base.value("thermo-2#1")["sensor_id"] == "thermo-2"
    assert base.support("decision.1") == Support.OBSERVED
    if broken:
        assert report.result.startswith("hypothèse réfutée")
        assert "hypothese" not in base.facts and "effet_attendu.1" not in base.facts
        assert base.support("hypothese.refutee") == Support.OBSERVED
        assert set(base.facts["hypothese.refutee"].premises) == {
            "decision.1",
            "thermo-1#1",
            "thermo-2#1",
        }
        assert {e.key for e in base.journal if e.kind == "invalidated"} == {
            "hypothese",
            "effet_attendu.1",
        }
    else:
        assert report.result == "aucune action nécessaire"
        assert base.support("effet_attendu.1") == Support.HYPOTHESIS
        assert base.support("effet_confirme.1") == Support.OBSERVED
        assert not base.retracted
    log = next((tmp_path / "scenarios").glob("*.jsonl"))
    messages = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(messages) == 6
    assert [m["payload"]["sensor_id"] for m in messages if "celsius" in m["payload"]] == [
        "thermo-1",
        "thermo-2",
    ]
    spans = report.to_json()["trace"]["spans"]
    by_id = {s["span_id"]: s for s in spans}
    for span in spans:
        if span["name"] == "procedure.resume":
            assert span["attributes"]["boundary"] == "pure"
            assert by_id[span["parent_id"]]["name"] == "hypomnesis.run"
        if span["name"] == "actuator.execute":
            assert by_id[span["parent_id"]]["name"] == "command.dispatch"
        if span["name"] == "observer.read":
            assert by_id[span["parent_id"]]["name"] == "hypomnesis.run"
    assert sum(s["name"] == "actuator.execute" for s in spans) == 1
    assert sum(s["name"] == "observer.read" for s in spans) == 2
    assert any(s["name"] == "procedure.resume" for s in spans)


@pytest.mark.parametrize(
    ("mode", "permissions", "state"),
    [
        ("dry-run", None, "DryRun"),
        ("simulate", None, "Simulated"),
        ("production", frozenset(), "Rejected"),
    ],
)
def test_unexecuted_command_does_not_refute_a_physical_hypothesis(
    tmp_path, mode, permissions, state
):
    report = run_procedure(
        load_language(LANGUAGE),
        PROGRAM,
        mode=mode,
        permissions=permissions,
        out_dir=tmp_path,
        environment={"panne": True},
    )
    assert report.result == f"commande non confirmée : {state}"
    assert len(report.commands) == 1 and report.commands[0].state == state
    assert "hypothese.refutee" not in report.kb.facts
    assert report.kb.support("hypothese") == Support.HYPOTHESIS
    assert not report.kb.retracted and "thermo-2#1" not in report.kb.facts
    assert not any(s.name == "actuator.execute" for s in report.tracer.spans)


@pytest.mark.parametrize(
    ("error", "state"),
    [
        (TransportError, "UnknownOutcome"),
        (ConnectionError, "Failed"),
    ],
)
def test_failed_response_does_not_refute_the_fan(tmp_path, error, state):
    language = load_language(LANGUAGE)
    factory = language.adapters.get("actuator", "fan.set")

    def fail(_):
        raise error("response lost")

    language.adapters.bindings[("actuator", "fan.set")] = lambda env: replace(
        factory(env), execute=fail
    )
    report = run_procedure(language, PROGRAM, mode="production", out_dir=tmp_path)
    assert report.result == f"commande non confirmée : {state}"
    assert report.commands[0].attempts == 1
    assert "hypothese.refutee" not in report.kb.facts and not report.kb.retracted


@pytest.mark.parametrize(
    ("budget", "temperature", "result", "actions"),
    [
        (0, 31, "budget épuisé", 0),
        (0, 28, "aucune action nécessaire", 0),
        (1, 31, "aucune action nécessaire", 1),
        (1, 60, "budget épuisé", 1),
    ],
)
def test_exact_action_budget_checks_goal_after_last_action(
    tmp_path, budget, temperature, result, actions
):
    report = run_procedure(
        load_language(LANGUAGE),
        PROGRAM.replace("budget = 5", f"budget = {budget}"),
        mode="production",
        out_dir=tmp_path,
        environment={"temperature": temperature},
    )
    assert report.result == result and len(report.commands) == actions
    assert not report.stopped


def test_negative_budget_and_absent_temperature_fail_explicitly(tmp_path):
    with pytest.raises((EvaluationError, LanguageError), match="négatif"):
        run_procedure(
            load_language(LANGUAGE),
            PROGRAM.replace("budget = 5", "budget = -1"),
            out_dir=tmp_path,
        )
    assert not (tmp_path / "rapport.json").exists()
    session = load_language(LANGUAGE).session
    with pytest.raises(EvaluationError, match="celsius"):
        session.eval("Ventilation.celsius Json.Null")


def test_m2_decision_is_also_usable_by_the_generic_pure_rule_engine():
    session = load_language(LANGUAGE).session
    session.load("""
let rule (inputs : Json.t list) : Json.t option =
  match inputs with
  | [Json.Num temperature] ->
      Option.map (fun v -> Json.Int v) (Ventilation.decider temperature)
  | _ -> None
""")
    base = KnowledgeBase()
    base.observe("temperature", 31.0, "sensor transcript")
    rule = language_rule(session, "decision", "speed", ("temperature",), "rule")
    assert RuleEngine(base, (rule,)).run().status == "fixed_point"
    assert base.value("speed") == 100 and base.support("speed") == Support.OBSERVED
