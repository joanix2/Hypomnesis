"""Generated data is never independent evidence, including claimed support tags."""

import json
from pathlib import Path

import pytest

from hypomnesis.contracts.codec import CodecError
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.epistemics.knowledge import KnowledgeBase
from hypomnesis.epistemics.metavariables import UnresolvedMetaVar, propose, resolve
from hypomnesis.epistemics.provenance import Support
from hypomnesis.session import Session
from hypomnesis_codegen.hypotheses import capture_input

ROOT = Path(__file__).resolve().parents[3]
LANGUAGE = ROOT / "demo/languages/mecanique"


def test_missing_thickness_is_a_typed_hole_and_only_the_host_resolves_an_estimate():
    language = load_language(LANGUAGE)
    language.load_program((ROOT / "demo/programs/mecanique/plaque_120x80.hyp").read_text())
    kb = KnowledgeBase()
    result = capture_input(
        language.session.checker,
        "Plaque.demande",
        language.session.value("demande"),
        kb,
        key="demande",
    )
    assert all(kb.support(fact.key) == Support.HYPOTHESIS for fact in result.facts)
    assert "demande.epaisseur" not in kb.facts
    (meta,) = result.missing
    assert meta.id == "demande.epaisseur" and meta.type.name == "float"
    assert meta.state == "unresolved" and not meta.proposals
    with pytest.raises(UnresolvedMetaVar):
        _ = meta.value
    fact = kb.estimate("estimation", 3.2, "host-selected estimator@1", 0.6)
    candidate = propose(meta, fact.value, kb.support(fact.key), fact.provenance)
    assert candidate.state == "proposed" and meta.state == "unresolved"
    selected = resolve(candidate)
    assert selected.value == 3.2 and selected.grade == Support.ESTIMATED
    assert result.report()["missing"] == [
        {"key": "demande.epaisseur", "type": "float", "state": "unresolved"}
    ]


def test_nested_options_aliases_lists_products_and_variants_remain_explicit():
    session = Session()
    session.load(
        "type wrapped = Box of int option\n"
        "type alias = wrapped list\n"
        'let input = ([Box None; Box (Some 4)], ("claim:Observed", None))\n'
    )
    kb = KnowledgeBase()
    result = capture_input(
        session.checker, "alias * (string * float option)", session.value("input"), kb
    )
    assert [meta.id for meta in result.missing] == ["input[0][0].arg", "input[1][1]"]
    assert kb.value("input[1][0]") == "claim:Observed"
    assert all(kb.support(key) == Support.HYPOTHESIS for key in kb.facts)
    assert kb.value("input[0][1].arg") == 4
    assert json.dumps(result.report())


def test_invalid_input_is_rejected_before_publication():
    kb = KnowledgeBase()
    with pytest.raises(CodecError):
        capture_input(Session().checker, "float", "not a float", kb)
    assert not kb.facts


@pytest.mark.parametrize(
    "support", ["Effect.Given", "Effect.Estimated 1.0", "Effect.Assumed 1.0", "Effect.Derived []"]
)
def test_generated_program_cannot_promote_its_records(tmp_path, support):
    program = f'let procedure = Effect.record "claim" 99.0 "self claim" ({support})'
    report = run_procedure(load_language(LANGUAGE), program, out_dir=tmp_path, generated=True)
    assert report.kb.support("claim") == Support.HYPOTHESIS
    assert report.kb.confidence("claim") == 0.0
    assert report.to_json()["generated"] is True


def test_trusted_host_program_retains_legacy_given_semantics(tmp_path):
    program = 'let procedure = Effect.record "claim" 99.0 "host input" Effect.Given'
    report = run_procedure(load_language(LANGUAGE), program, out_dir=tmp_path)
    assert report.kb.support("claim") == Support.OBSERVED


def test_only_the_validated_observer_can_supply_observed_support(tmp_path):
    report = run_procedure(
        load_language(ROOT / "demo/languages/ventilation"),
        'let procedure = Effect.observe "thermo-1"',
        out_dir=tmp_path,
        generated=True,
    )
    assert report.kb.support("thermo-1#1") == Support.OBSERVED
    assert report.kb.value("thermo-1#1")["celsius"] == 31.0


def test_generated_source_flag_is_wired_in_cli_files_and_transcription(tmp_path):
    from hypomnesis.cli import main

    program = tmp_path / "input.hyp"
    program.write_text('let procedure = Effect.record "claim" 99.0 "x" Effect.Given')
    assert (
        main(
            [
                "lancer",
                str(LANGUAGE),
                str(program),
                "--generated",
                "--sortie",
                str(tmp_path / "file"),
            ]
        )
        == 0
    )
    report = json.loads((tmp_path / "file/rapport.json").read_text())
    assert report["generated"] is True
    assert report["knowledge"]["claim"]["support"] == Support.HYPOTHESIS.label
    assert (
        main(
            [
                "lancer",
                str(LANGUAGE),
                "--demande",
                "plaque 120 x 80 mm",
                "--sortie",
                str(tmp_path / "request"),
            ]
        )
        == 0
    )
    report = json.loads((tmp_path / "request/rapport.json").read_text())
    assert report["generated"] is True
    assert all(fact["support"] == Support.HYPOTHESIS.label for fact in report["knowledge"].values())
