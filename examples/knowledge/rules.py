"""Run a pure Hypomnesis business rule over observed and estimated inputs."""

from pathlib import Path

from hypomnesis.engine.rules import RuleEngine, language_rule
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.provenance import Support
from hypomnesis.session import Session


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    session = Session()
    session.load((root / "demo/examples/knowledge/regles.hyp").read_text())
    base = KnowledgeBase()
    base.observe("largeur", 120, "plan")
    base.estimate("hauteur", 80, "estimateur", 0.6)
    rule = language_rule(session, "surface", "surface", ("largeur", "hauteur"), "surface")
    report = RuleEngine(base, (rule,)).run(budget=10)
    assert report.status == "fixed_point"
    assert base.support("surface") == Support.ESTIMATED
    print(base.value("surface"), base.support("surface").name)


if __name__ == "__main__":
    main()
