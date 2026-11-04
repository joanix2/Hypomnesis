"""The optional estimator suite is excluded only from the core-only CI job."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.backends.sklearn import RegressionEstimator
from hypomnesis.capabilities.protocols import Estimator
from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.metavariables import MetaVar, propose
from hypomnesis.epistemics.provenance import Support
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "demo/languages/mecanique/modeles/epaisseur-1.0.0.json"


@pytest.fixture(scope="module")
def estimator():
    return RegressionEstimator(**json.loads(DATA.read_text()))


def test_model_is_reproducible_accurate_on_documented_data_and_never_resolves_hole(estimator):
    duplicate = RegressionEstimator(**json.loads(DATA.read_text()))
    assert isinstance(estimator, Estimator)
    prediction = estimator.estimate({"petit_cote_mm": 80.0})
    assert prediction.ok and prediction.value is not None
    assert prediction == duplicate.estimate({"petit_cote_mm": 80.0})
    value = prediction.value
    assert 3.15 < value.value < 3.25
    assert 0.0 < value.validation_rmse < 0.04
    assert prediction.certificate.body["version"] == value.version == "1.0.0"
    base = KnowledgeBase()
    fact = base.estimate("epaisseur", value.value, value.origin, 0.6)
    assert base.support("epaisseur") == Support.ESTIMATED
    source = base.sources[base.source_id("epaisseur")]
    assert value.model in source.origin and value.version in source.origin
    assert "validation_rmse=" in source.origin
    hole = MetaVar("epaisseur", TypeCodec(Session().checker, "float"))
    proposed = propose(hole, fact.value, base.support("epaisseur"), fact.provenance)
    assert proposed.state == "proposed" and proposed.grade is None
    assert proposed.proposals[0].grade == Support.ESTIMATED and hole.state == "unresolved"


@given(value=st.floats(min_value=25, max_value=300, allow_nan=False, allow_infinity=False))
def test_predictions_inside_domain_are_finite(value):
    model = RegressionEstimator(**json.loads(DATA.read_text()))
    result = model.estimate({"petit_cote_mm": value})
    assert result.ok and math.isfinite(result.value.value)
    assert result.certificate.body["uncertainty"]["kind"] == "held-out-rmse"


@pytest.mark.parametrize("value", [24.9, 300.1, -1.0])
def test_extrapolation_is_an_explicit_failure(estimator, value):
    result = estimator.estimate({"petit_cote_mm": value})
    assert not result.ok and result.value is None and result.certificate is None
    assert result.diagnostics[0].code == "estimator.out_of_domain"
    assert result.diagnostics[0].data["domain"] == ((25.0, 300.0),)


@pytest.mark.parametrize("value", [True, None, "80", float("nan"), float("inf"), 10**400])
def test_invalid_numbers_are_not_coerced_or_replaced(estimator, value):
    result = estimator.estimate({"petit_cote_mm": value})
    assert not result.ok and result.value is None
    assert result.diagnostics[0].code == "estimator.input"


@pytest.mark.parametrize("query", [{}, {"other": 80}, {"petit_cote_mm": 80, "other": 1}, []])
def test_feature_set_is_exact(estimator, query):
    result = estimator.estimate(query)
    assert not result.ok and result.diagnostics[0].code == "estimator.features"


@pytest.mark.parametrize(
    "changes",
    [
        {"features": []},
        {"features": ["x", "x"]},
        {"version": ""},
        {"training": [[1, True], [2, 3]]},
        {"training": [[1, 2]]},
        {"training": [[1, 2], [1, 3]]},
        {"validation": []},
        {"validation": [[25.0, 1.0]]},
        {"validation": [[500.0, 20.0]]},
    ],
)
def test_invalid_training_configuration_is_refused(changes):
    document = json.loads(DATA.read_text())
    document.update(changes)
    with pytest.raises(ValueError):
        RegressionEstimator(**document)


def test_importing_backend_does_not_import_optional_libraries():
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import hypomnesis.backends.sklearn; "
            "assert 'sklearn' not in sys.modules and 'numpy' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr


def test_backend_is_multifeature_and_not_domain_specific():
    model = RegressionEstimator(
        model="generic",
        version="1",
        features=("a", "b"),
        training=((0, 0, 1), (1, 0, 3), (0, 1, 4), (1, 1, 6)),
        validation=((0.5, 0.5, 3.5),),
    )
    result = model.estimate({"a": 0.25, "b": 0.75})
    assert result.ok and result.value.value == pytest.approx(3.75)
    assert result.value.validation_rmse == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("response", ["raise", "nan"])
def test_model_failures_become_explicit_diagnostics(monkeypatch, response):
    model = RegressionEstimator(**json.loads(DATA.read_text()))

    def predict(_):
        if response == "raise":
            raise ValueError("prediction failed")
        return [float("nan")]

    monkeypatch.setattr(model._model, "predict", predict)
    result = model.estimate({"petit_cote_mm": 80})
    assert not result.ok and result.value is None
    assert result.diagnostics[0].code == "estimator.predict"
