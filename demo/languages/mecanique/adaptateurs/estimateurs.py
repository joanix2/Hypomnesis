"""Contractual worker boundaries; all mechanics features and rules remain M2."""

import json
from pathlib import Path

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.engine.language import load_language

LANGUAGE = Path(__file__).resolve().parents[1]


def rule(payload):
    language = load_language(LANGUAGE)
    demand = TypeCodec(language.session.checker, "Plaque.demande").decode(payload)
    return language.function("Plaque.estimer_regle")(demand)


def regression(payload):
    from hypomnesis.backends.sklearn import RegressionEstimator

    language = load_language(LANGUAGE)
    demand = TypeCodec(language.session.checker, "Plaque.demande").decode(payload)
    features = {"petit_cote_mm": language.function("Plaque.petit_cote")(demand)}
    model = RegressionEstimator(
        **json.loads((LANGUAGE / "modeles/epaisseur-1.0.0.json").read_text())
    )
    result = model.estimate(features)
    if not result.ok or result.value is None:
        raise ValueError("; ".join(f"{d.code}: {d.message}" for d in result.diagnostics))
    return result.value.value
