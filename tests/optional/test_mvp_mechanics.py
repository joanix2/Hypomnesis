"""True offline E2E: optional Codegen + sklearn, symbolic core and file effects."""

import json
from pathlib import Path

import pytest
from examples.mechanics.mvp import LANGUAGE, RESPONSE, run_mvp

from hypomnesis.engine.language import load_language
from hypomnesis.engine.validators import LanguageValidator


def test_ten_steps_are_real_persistent_and_linked_to_evidence(tmp_path):
    report = run_mvp(tmp_path)
    persisted = json.loads((tmp_path / "rapport_mvp.json").read_text())
    assert persisted == report and report["status"] == "completed"
    assert [step["number"] for step in report["steps"]] == list(range(1, 11))
    spans = {span["name"]: span for span in report["trace"]["spans"]}
    assert all(step["span"] in spans for step in report["steps"])
    assert all(span["status"] == "ok" for span in spans.values())
    assert spans["actuator.execute"]["parent_id"] == spans["command.dispatch"]["span_id"]
    for step in report["steps"]:
        assert step["evidence"] in report["knowledge"] or step["evidence"] == "metrics"
    assert report["solution"]["assignment"] == [["epaisseur", {"tag": "Rational", "arg": [3, 1]}]]
    assert report["input"]["missing"] == [
        {"key": "demande.epaisseur", "type": "float", "state": "unresolved"}
    ]
    meta = report["metavariable"]
    assert meta["state"] == "resolved" and meta["selection"] == 1
    assert meta["proposals"][0]["grade"] == "ESTIMATED"
    assert meta["proposals"][1]["value"] == 3.0
    assert meta["coherence"] == "conflict"
    geometry = json.loads((tmp_path / "plaque-support.json").read_text())
    assert (
        geometry
        == report["result"]["geometry"]
        == {
            "name": "plaque-support",
            "width_mm": 120.0,
            "height_mm": 80.0,
            "thickness_mm": 3.0,
        }
    )
    transcript = [json.loads(line) for line in Path(report["transport"]).read_text().splitlines()]
    assert len(transcript) == 2
    assert transcript[0]["payload"]["part"] == geometry
    assert transcript[1]["payload"]["status"] == "written"
    assert report["knowledge"]["export.result"]["support"] == "OBSERVED"
    assert report["knowledge"]["demande.valide"]["support"] == "HYPOTHESIS"
    assert report["result"]["support"] == "HYPOTHESIS"
    origins = [node.get("origin", "") for node in report["provenance_graph"]["nodes"]]
    assert any("plaque-epaisseur-synthetique@1.0.0" in origin for origin in origins)
    assert report["metrics"]["model_mode"] == "recorded-fixture"
    assert report["metrics"]["tokens_measured"] is False
    assert report["metrics"]["commands"] == 1
    assert report["journal"]
    validator = LanguageValidator(
        load_language(LANGUAGE).session, "Plaque.verifier_proposition", "Plaque.proposition"
    )
    assert validator.recheck(report["validation"]).value is True


def test_centimetres_are_normalized_by_m2_not_by_a_python_formula(tmp_path):
    response = (
        RESPONSE.read_text()
        .replace("largeur = 120.0", "largeur = 12.0")
        .replace("hauteur = 80.0", "hauteur = 8.0")
    )
    report = run_mvp(tmp_path, response=response, source_unit="cm")
    assert report["result"]["geometry"]["width_mm"] == 120.0
    assert report["result"]["geometry"]["height_mm"] == 80.0
    assert report["estimator"]["features"] == {"petit_cote_mm": 80.0}
    assert report["knowledge"]["demande.largeur"]["value"] == 12.0


def test_candidate_cannot_replace_the_host_selected_m2_validator(tmp_path):
    response = RESPONSE.read_text() + (
        '\nmodule Plaque = struct\nlet verifier_proposition p = ["poisoned"]\nend\n'
    )
    report = run_mvp(tmp_path, response=response)
    assert report["status"] == "completed"
    assert report["validation"]["violations"] == []


def test_software_failure_is_not_reported_as_a_successful_export(tmp_path, monkeypatch):
    from dataclasses import replace

    import examples.mechanics.mvp as mvp

    original = mvp.trace_actuator

    def broken_action(action, tracer):
        def fail(payload):
            raise OSError("fixture disk failure")

        return original(replace(action, execute=fail), tracer)

    monkeypatch.setattr(mvp, "trace_actuator", broken_action)
    with pytest.raises(RuntimeError, match="Failed"):
        run_mvp(tmp_path)
    report = json.loads((tmp_path / "rapport_mvp.json").read_text())
    assert report["commands"][0]["state"] == "Failed"
    assert report["status"] == "failed"
    assert not (tmp_path / "plaque-support.json").exists()
    assert "export.result" not in report["knowledge"]


def test_invalid_export_path_is_rejected_by_the_existing_dispatcher(tmp_path):
    response = RESPONSE.read_text().replace('"plaque-support"', '"../escape"')
    with pytest.raises(RuntimeError, match="Rejected"):
        run_mvp(tmp_path / "run", response=response)
    assert not (tmp_path / "escape.json").exists()
    report = json.loads((tmp_path / "run/rapport_mvp.json").read_text())
    assert not any(span["name"] == "actuator.execute" for span in report["trace"]["spans"])


def test_denied_permission_prevents_geometry_export_but_preserves_failure_trace(tmp_path):
    with pytest.raises(RuntimeError, match="Rejected"):
        run_mvp(tmp_path, permissions=frozenset())
    report = json.loads((tmp_path / "rapport_mvp.json").read_text())
    assert report["status"] == "failed"
    assert not (tmp_path / "plaque-support.json").exists()
    assert report["commands"][0]["state"] == "Rejected"
    assert not any(span["name"] == "actuator.execute" for span in report["trace"]["spans"])
    assert report["trace"]["spans"][0]["status"] == "error"


@pytest.mark.parametrize(
    ("response", "unit", "error"),
    [
        ("let procedure = 3", "mm", "procédure"),
        (
            RESPONSE.read_text().replace("epaisseur = None", "epaisseur = Some 4.0"),
            "mm",
            "not invented",
        ),
        (RESPONSE.read_text(), "inch", "unsupported source unit"),
        (RESPONSE.read_text().replace("largeur = 120.0", "largeur = 1.0"), "mm", "out_of_domain"),
        (RESPONSE.read_text().replace("masse_max = 0.5", "masse_max = 0.0001"), "mm", "unsat"),
    ],
)
def test_invalid_requests_stop_before_any_export(tmp_path, response, unit, error):
    with pytest.raises((ValueError, RuntimeError), match=error):
        run_mvp(tmp_path, response=response, source_unit=unit)
    report = json.loads((tmp_path / "rapport_mvp.json").read_text())
    assert report["status"] == "failed" and report["error"]
    assert not (tmp_path / "plaque-support.json").exists()
    assert not any(span["name"] == "actuator.execute" for span in report["trace"]["spans"])
