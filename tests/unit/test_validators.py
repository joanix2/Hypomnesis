import json
from copy import deepcopy
from pathlib import Path

import pytest

from hypomnesis.capabilities.protocols import Validator
from hypomnesis.engine.language import load_language
from hypomnesis.engine.validators import LanguageValidator
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.provenance import Support
from hypomnesis.runtime.values import iter_list
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/mecanique"


@pytest.fixture(scope="module")
def validator():
    return LanguageValidator(
        load_language(LANGUAGE).session, "Plaque.verifier_proposition", "Plaque.proposition"
    )


def proposal(validator, *, thickness=3.0, width=120.0, height=80.0, mass=0.5):
    return validator.codec.decode(
        {
            "demande": {
                "nom": "test",
                "largeur": width,
                "hauteur": height,
                "epaisseur": {"tag": "None"},
                "masse_max": mass,
            },
            "epaisseur_proposee": thickness,
        }
    )


def test_accepted_proposal_has_replayable_certificate_without_changing_its_data(validator):
    assert isinstance(validator, Validator)
    value = proposal(validator)
    result = validator.validate(value)
    assert result.ok and result.value == value and result.certificate is not None
    witness = json.loads(json.dumps(result.certificate.body, allow_nan=False))
    replay = validator.recheck(witness)
    assert replay.ok and replay.value is True
    assert witness["violations"] == [] and witness["input"]["epaisseur_proposee"] == 3.0


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"thickness": 0.0}, "minimum"),
        ({"thickness": -1.0}, "minimum"),
        ({"thickness": 0.5}, "minimum"),
        ({"thickness": 1.0}, "élancée"),
        ({"thickness": 10.0}, "masse supérieure"),
        ({"width": 0.0}, "positives"),
        ({"height": -1.0}, "positives"),
        ({"mass": 0.0}, "positives"),
    ],
)
def test_every_geometric_rejection_has_an_independently_replayed_counterexample(
    validator, changes, message
):
    result = validator.validate(proposal(validator, **changes))
    assert not result.ok and result.value is None and result.certificate is None
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "validator.rejected" and message in diagnostic.message
    witness = json.loads(json.dumps(diagnostic.data["counterexample"], allow_nan=False))
    fresh = load_language(LANGUAGE).session
    independent = LanguageValidator(fresh, "Plaque.verifier_proposition", "Plaque.proposition")
    decoded = independent.codec.decode(witness["input"])
    actual = fresh.interpreter.apply(fresh.value("Plaque.verifier_proposition"), [decoded])
    assert list(iter_list(actual)) == witness["violations"] and witness["violations"]
    replay = independent.recheck(witness)
    assert replay.ok and replay.value is False


@pytest.mark.parametrize("change", ["input", "violations", "checker", "input_type", "extra"])
def test_tampering_is_not_trusted_or_allowed_to_select_the_checker(validator, change):
    rejected = validator.validate(proposal(validator, thickness=0.5))
    witness = deepcopy(rejected.diagnostics[0].data["counterexample"])
    if change == "input":
        witness["input"]["epaisseur_proposee"] = 3.0
    elif change == "violations":
        witness["violations"] = []
    elif change == "extra":
        witness["extra"] = True
    else:
        witness[change] = "untrusted"
    replay = validator.recheck(witness)
    assert not replay.ok and replay.value is None
    assert replay.diagnostics[0].code == "validator.evidence"


def test_bad_input_and_checker_errors_are_not_fabricated_mathematical_refutations(validator):
    result = validator.validate(1)
    assert not result.ok and result.diagnostics[0].code == "validator.input"
    assert "counterexample" not in result.diagnostics[0].data
    session = Session()
    session.load('let broken (_ : int) : string list = failwith "checker failed"')
    broken = LanguageValidator(session, "broken", "int")
    result = broken.validate(1)
    assert not result.ok and result.diagnostics[0].code == "validator.checker"
    assert "checker failed" in result.diagnostics[0].message
    assert result.certificate is None


def test_checker_must_be_closed_and_have_the_expected_pure_signature():
    session = Session()
    session.load("let wrong (x : int) = x + 1")
    with pytest.raises(ValueError, match="string list"):
        LanguageValidator(session, "wrong", "int")


def test_replay_rejects_malformed_typed_payload(validator):
    accepted = validator.validate(proposal(validator))
    witness = deepcopy(accepted.certificate.body)
    witness["input"]["demande"]["largeur"] = "120"
    assert not validator.recheck(witness).ok


def test_accepting_an_estimated_input_does_not_promote_its_support(validator):
    base = KnowledgeBase()
    base.estimate("proposal", validator.codec.encode(proposal(validator)), "model@1.0", 0.6)
    result = validator.validate(validator.codec.decode(base.value("proposal")))
    assert result.ok
    base.derive("valid", result.ok, "geometric validation", ["proposal"])
    assert base.support("valid") == Support.ESTIMATED
