"""Executable correspondence of the handler model and actual mode boundaries."""

import json
import subprocess
from pathlib import Path

import pytest

from hypomnesis.certify import session_certificate
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import MODES, Actuator, Dispatcher
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure

ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "formal"


@pytest.fixture(scope="module")
def handlers(lean_lake):
    lake = lean_lake
    for args in (["build", "Hypomnesis.Effects.Handlers"], ["env", "lean", "HandlersTable.lean"]):
        result = subprocess.run(
            [lake, *args], cwd=FORMAL, text=True, capture_output=True, timeout=120, check=False
        )
        assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_all_mode_gates_deadlines_and_responses_match_real_dispatcher(handlers):
    rows = handlers["steps"]
    assert len(rows) == 3 * 2 * 2 * 2
    assert {row["mode"] for row in rows} == set(MODES)
    assert len({(r["mode"], r["allowed"], r["expired"], r["valid"]) for r in rows}) == len(rows)
    for row in rows:
        schemas = SchemaRegistry.with_builtin_schemas()
        schemas.add(
            {
                "$id": "urn:handlers:command",
                "type": "object",
                "properties": {"command_id": {"type": "string"}, "input": {"type": "integer"}},
                "required": ["command_id", "input"],
                "additionalProperties": False,
            }
        )
        schemas.add(
            {
                "$id": "urn:handlers:response",
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
                "additionalProperties": False,
            }
        )
        calls = []

        def respond(mode, value, *, valid=row["valid"], calls=calls):
            calls.append(mode)
            return {"value": value if valid else "invalid"}

        clock = iter([0.0, 2.0 if row["expired"] else 0.0, 0.0])
        dispatcher = Dispatcher(
            schemas,
            {"motor.run"} if row["allowed"] else set(),
            row["mode"],
            clock=lambda clock=clock: next(clock),
        )
        dispatcher.register(
            Actuator(
                "motor",
                "motor.run",
                "urn:handlers:command",
                "urn:handlers:response",
                lambda _: respond("production", 7),
                simulate=lambda _: respond("simulate", 5),
                timeout=1.0,
            )
        )
        outcome = dispatcher.dispatch(dispatcher.command("motor", {"input": 3}))
        assert outcome.state == row["reply"]["state"], row
        assert (None if outcome.result is None else outcome.result["value"]) == row["reply"][
            "result"
        ], row
        assert len(calls) == row["world"], row
        assert (["motor"] if outcome.dispatched else []) == row["dispatches"], row
        assert calls == ([row["mode"]] if row["world"] else []), row


def test_reference_interprets_continuations_and_bounded_prefixes(handlers):
    rows = handlers["programs"]
    assert len(rows) == 15
    for row in rows:
        mode, fuel = row["mode"], row["fuel"]
        assert (row["value"] is None) is (fuel < 3)
        if fuel >= 3:
            assert row["value"] == {
                "state": {"dry-run": "DryRun", "simulate": "Simulated", "production": "Completed"}[
                    mode
                ],
                "result": {"dry-run": None, "simulate": 5, "production": 7}[mode],
            }
        assert row["dispatches"] == (["motor"] if mode == "production" and fuel >= 2 else [])
        assert row["world"] == min(fuel, 3) - (1 if mode == "dry-run" and fuel >= 2 else 0)


SOURCE = """
let demande = {
  Plaque.nom = "handlers"; largeur = 120.0; hauteur = 80.0;
  epaisseur = Some 3.0; masse_max = 0.5
}
let procedure =
  Effect.note "start" >>= fun () ->
  Effect.act "geometry.export" (Plaque.commande_export demande 3.0 "json") >>= fun reply ->
  let state = Option.value (Json.str_field "state" reply) "missing" in
  Effect.record "reply" state "actuator response" Effect.Given >>= fun () ->
  (if state = "Completed" then Effect.note "actual completion"
   else Effect.note "no completion") >>= fun () ->
  Effect.return state
"""


@pytest.fixture(scope="module")
def expected_ir():
    language = load_language(ROOT / "demo/languages/mecanique", execute=False)
    language.session.check(SOURCE)
    return session_certificate(language.session)


@pytest.mark.parametrize(
    ("mode", "state"),
    [("dry-run", "DryRun"), ("simulate", "Simulated"), ("production", "Completed")],
)
def test_same_compiled_source_branches_only_on_actual_reply(tmp_path, mode, state, expected_ir):
    language = load_language(ROOT / "demo/languages/mecanique")
    report = run_procedure(language, SOURCE, mode=mode, out_dir=tmp_path)
    assert session_certificate(language.session) == expected_ir
    assert report.program == SOURCE
    assert report.result == report.kb.facts["reply"].value == state
    assert report.notes == [
        "start",
        "actual completion" if mode == "production" else "no completion",
    ]
    assert (tmp_path / "handlers.json").is_file() is (mode == "production")
    dispatches = [s for s in report.tracer.spans if s.name == "actuator.execute"]
    assert len(dispatches) == (1 if mode == "production" else 0)


def test_lean_requirement_is_an_error_not_an_optional_skip(tmp_path, monkeypatch):
    from tests.conftest import require_lake

    monkeypatch.setattr("tests.conftest.shutil.which", lambda _: None)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HYPOMNESIS_REQUIRE_LEAN", "1")
    with pytest.raises(pytest.fail.Exception, match="lake missing"):
        require_lake()
