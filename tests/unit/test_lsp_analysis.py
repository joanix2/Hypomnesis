"""Compiler-backed editor checks, including unsaved M2 sources and Unicode positions."""

import json
from pathlib import Path

import pytest

from hypomnesis.language.errors import HypomnesisError
from hypomnesis.lsp.analysis import analyze, language_root
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("source", ["let x = (1 +", "let x = true + 1", "let x = missing"])
def test_messages_match_the_real_compiler(tmp_path, source):
    with pytest.raises(HypomnesisError) as caught:
        Session().check(source)
    [issue] = analyze(tmp_path / "p.hyp", source, tmp_path, None, {})
    assert issue.message == caught.value.message
    assert issue.code == caught.value.stage_id
    assert issue.range.start.line == caught.value.span.line - 1


def test_edited_programs_are_never_evaluated(tmp_path):
    assert analyze(tmp_path / "p.hyp", "let x = 1 / 0", tmp_path, None, {}) == []


def test_utf16_columns_count_surrogate_pairs(tmp_path):
    source = 'let x = ("😀", true + 1)'
    [issue] = analyze(tmp_path / "p.hyp", source, tmp_path, None, {})
    offset = source.index("true")
    assert issue.range.start.character == len(source[:offset].encode("utf-16-le")) // 2
    assert issue.range.end.character == issue.range.start.character + 4


def test_context_discovery_for_actual_m1_and_m2():
    m2 = ROOT / "languages" / "mecanique"
    assert language_root(m2 / "plaque.hyp", ROOT, None) == m2
    m1 = ROOT / "programs" / "mecanique" / "plaque_120x80.hyp"
    assert language_root(m1, ROOT, None) == m2
    assert analyze(m1, m1.read_text(), ROOT, None, {}) == []
    assert analyze(m2 / "plaque.hyp", (m2 / "plaque.hyp").read_text(), ROOT, None, {}) == []


def make_language(root):
    root.mkdir()
    (root / "langage.json").write_text(
        json.dumps(
            {
                "name": "test",
                "version": "0.1.0",
                "description": "Test",
                "sources": ["a.hyp", "b.hyp"],
                "procedure": {"kind": "program", "entry": "main"},
            }
        )
    )
    (root / "a.hyp").write_text("let x = 1")
    (root / "b.hyp").write_text("let y = x + 1")
    return root


def test_unsaved_dependency_and_target_overlay(tmp_path):
    root = make_language(tmp_path / "m2")
    path = root / "b.hyp"
    assert analyze(path, "let y = x + 1", tmp_path, None, {}) == []
    [issue] = analyze(path, "let y = x + 1", tmp_path, None, {str(root / "a.hyp"): "let x = true"})
    assert issue.code == "type"
    # The current M2 source is not loaded twice from its on-disk contents.
    assert analyze(root / "a.hyp", "let x = true", tmp_path, None, {}) == []


def test_explicit_context_and_configuration_errors(tmp_path):
    root = make_language(tmp_path / "m2")
    path = tmp_path / "p.hyp"
    assert analyze(path, "let z = y", tmp_path, "m2", {}) == []
    [issue] = analyze(path, "let z = y", tmp_path, "missing", {})
    assert issue.code == "configuration"
    assert "langage.json" in issue.message
    (root / "a.hyp").write_text("let x = missing")
    [issue] = analyze(path, "let z = y", tmp_path, "m2", {})
    assert str(root / "a.hyp") in issue.message
    assert issue.range.start.line == 0


def test_invalid_manifest_is_not_a_success(tmp_path):
    root = make_language(tmp_path / "m2")
    (root / "langage.json").write_text("{}")
    [issue] = analyze(tmp_path / "p.hyp", "let x = 1", tmp_path, "m2", {})
    assert issue.code == "configuration"
    assert "manifeste invalide" in issue.message
