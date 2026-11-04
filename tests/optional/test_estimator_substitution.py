import pytest
from examples.mechanics.substitution import PLUGINS, PROGRAM, configure, run_substitution

from hypomnesis.backends.python import BackendError
from hypomnesis.epistemics.provenance import Support


def test_real_rule_and_regression_plugins_share_one_unchanged_program(tmp_path):
    source = PROGRAM.read_text()
    reports = [
        run_substitution(PLUGINS / f"epaisseur-{provider}-1.0.0.json", tmp_path / provider)
        for provider in ("regle", "regression")
    ]
    assert all(r["program"] == source for r in reports)
    assert PROGRAM.read_text() == source
    assert all(r["result"] == "Valide" and not r["stopped"] for r in reports)
    assert all(
        r["knowledge"]["epaisseur.estimation"]["support"] == Support.ESTIMATED.label
        for r in reports
    )
    estimates = [r["knowledge"]["epaisseur.estimation"]["value"] for r in reports]
    assert estimates[0] == 3.2
    assert 3.15 < estimates[1] < 3.25 and estimates[1] != estimates[0]
    assert all(r["knowledge"]["demande.epaisseur"]["value"] == 3.0 for r in reports)
    assert all(r["knowledge"]["demande.valide"]["value"] is True for r in reports)
    for report in reports:
        identifier = report["estimator_plugin"]["id"]
        nodes = report["provenance_graph"]["nodes"]
        assert any(identifier in n.get("origin", "") for n in nodes)
        assert any(s["name"] == "extension.process" for s in report["plugin_trace"]["spans"])


def test_regression_refuses_extrapolation_without_rule_fallback():
    language, backend = configure(PLUGINS / "epaisseur-regression-1.0.0.json")
    language.load_program(
        'let request = { Plaque.nom = "petite"; largeur = 1.0; hauteur = 2.0; '
        "epaisseur = None; masse_max = 0.5 }"
    )
    with pytest.raises(BackendError, match=r"estimator\.out_of_domain") as error:
        backend.invoke(language.session.value("request"))
    assert error.value.extension == "mechanics.thickness.regression"
    assert error.value.phase == "call"
