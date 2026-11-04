import json
import sys

import pytest
from examples.mechanics.substitution import PLUGINS, PROGRAM, configure, run_substitution

from hypomnesis.epistemics.provenance import Support


def test_rule_plugin_executes_the_unchanged_program(tmp_path):
    source = PROGRAM.read_text()
    report = run_substitution(PLUGINS / "epaisseur-regle-1.0.0.json", tmp_path, mode="simulate")
    assert report["program"] == source == PROGRAM.read_text()
    assert report["result"] == "Valide"
    assert report["stopped"] == ""
    estimate = report["knowledge"]["epaisseur.estimation"]
    assert estimate["value"] == 3.2 and estimate["support"] == Support.ESTIMATED.label
    assert report["knowledge"]["demande.epaisseur"]["value"] == 3.0
    assert any(s["name"] == "extension.process" for s in report["plugin_trace"]["spans"])
    assert report["commands"] and not list(tmp_path.glob("plaque-plugins.*"))


def test_static_preparation_never_starts_either_provider(monkeypatch):
    import subprocess

    def forbidden(*args, **kwargs):
        raise AssertionError("static preparation started a provider")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    for config in sorted(PLUGINS.glob("*.json")):
        language, backend = configure(config)
        language.session.check(PROGRAM.read_text())
        assert not backend.tracer.spans
        assert "demo.languages.mecanique.adaptateurs.estimateurs" not in sys.modules


def test_wrong_capability_is_rejected_before_registration(tmp_path):
    manifest = json.loads((PLUGINS / "epaisseur-regle-1.0.0.json").read_text())
    manifest["role"] = "Solver"
    config = tmp_path / "wrong-role.json"
    config.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="expected an Estimator"):
        configure(config)
