"""Host-selected estimator proposes a typed hole; it never certifies a design."""

import json
from pathlib import Path

from hypomnesis.backends.sklearn import RegressionEstimator
from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.metavariables import MetaVar, propose
from hypomnesis.session import Session


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    data = root / "demo/languages/mecanique/modeles/epaisseur-1.0.0.json"
    estimator = RegressionEstimator(**json.loads(data.read_text()))
    result = estimator.estimate({"petit_cote_mm": 80.0})
    if not result.ok or result.value is None:
        raise RuntimeError(f"estimator failed: {result.diagnostics}")
    prediction = result.value
    base = KnowledgeBase()
    fact = base.estimate("demande.epaisseur", prediction.value, prediction.origin, confidence=0.6)
    hole = MetaVar(fact.key, TypeCodec(Session().checker, "float"))
    hole = propose(hole, fact.value, base.support(fact.key), fact.provenance)
    print(hole.state, hole.proposals[0].grade.name, prediction.origin)


if __name__ == "__main__":
    main()
