import itertools
import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from hypomnesis.cli import main
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.language.errors import DIAGNOSTICS_SCHEMA_ID, EvaluationError, TypeCheckError
from hypomnesis.lsp.analysis import analyze
from hypomnesis.session import Session


def warnings(source):
    return Session().check(source).warnings


@pytest.mark.parametrize(
    ("source", "example"),
    [
        ("let f x = match x with Some y -> y", "None"),
        ("let f = function None -> 0 | Some true -> 1", "Some (false)"),
        ("let f = function _ :: _ -> 0", "[]"),
        ("let f = function [] -> 0", "::"),
        ("let f = function 0 -> 0", "1"),
        ('let f = function "" -> 0', '"a"'),
        ("let f = function 0.0 -> 0", "1.0"),
        ("let f = function true when true -> 0 | false -> 1", "true"),
        ("let f (Some x) = x", "None"),
        ("let (Some x) = None", "None"),
        ("let f () = let (Some x) = None in x", "None"),
    ],
)
def test_missing_patterns_have_positioned_witnesses(source, example):
    [warning] = warnings(source)
    assert "non-exhaustive" in warning.message and example in warning.message
    assert warning.span is not None and warning.span.line == 1
    assert warning.to_diagnostic()["severity"] == "warning"


@pytest.mark.parametrize(
    "source",
    [
        "let f = function None -> 0 | Some _ -> 1",
        "let f = function [] -> 0 | _ :: _ -> 1",
        "let f = function [] -> 0 | [_] -> 1 | _ :: _ :: _ -> 2",
        "let f = function (Some true | Some false) -> 0 | None -> 1",
        "let f = function (Some _ as o) -> 0 | None -> 1",
        "let f = function _ when false -> 0 | _ -> 1",
        "let f () = 0",
        "type r = { a : bool; b : bool }\nlet f = function {a = true} -> 0 | {a = false} -> 1",
        "type tree = Leaf | Branch of tree * tree\nlet f = function Leaf -> 0 | Branch _ -> 1",
        "type choice = bool\nlet f (x : choice) = match x with true -> 0 | false -> 1",
        "type 'a box = Box of 'a\nlet f = function Box true -> 0 | Box false -> 1",
    ],
)
def test_complete_patterns_do_not_warn(source):
    assert warnings(source) == []


@pytest.mark.parametrize(
    "source",
    [
        "let f = function _ -> 0 | None -> 1",
        "let f = function None -> 0 | Some _ -> 1 | Some true -> 2",
        "let f = function _ -> 0 | _ when false -> 1",
        "let f = function (None | Some _) -> 0 | Some true -> 1",
    ],
)
def test_redundant_arms_are_positioned(source):
    [warning] = warnings(source)
    assert "unreachable" in warning.message
    assert warning.span is not None and warning.span.column > 20


def test_duplicate_record_fields_cannot_hide_a_contradictory_pattern():
    with pytest.raises(TypeCheckError, match="field a is defined several times"):
        Session().check("type r = { a : bool }\nlet f = function {a = true; a = false} -> 0")


PAIRS = set(itertools.product([False, True], repeat=2))
PATTERNS = [
    ("_", PAIRS),
    ("(true, _)", {(True, False), (True, True)}),
    ("(_, false)", {(False, False), (True, False)}),
] + [(f"({str(a).lower()}, {str(b).lower()})", {(a, b)}) for a, b in sorted(PAIRS)]


@settings(max_examples=80, derandomize=True, deadline=None, database=None)
@given(st.lists(st.integers(0, len(PATTERNS) - 1), min_size=1, max_size=8))
def test_matrix_results_match_finite_runtime_domain(_prelude_session, indices):
    source = "let f (pair : bool * bool) = match pair with " + " | ".join(
        f"{PATTERNS[index][0]} -> {arm}" for arm, index in enumerate(indices)
    )
    session = Session()
    result = session.load(source)
    covered = set()
    redundant = 0
    for index in indices:
        matched = PATTERNS[index][1]
        redundant += matched <= covered
        covered |= matched
    assert sum("unreachable" in w.message for w in result.warnings) == redundant
    assert sum("non-exhaustive" in w.message for w in result.warnings) == (covered != PAIRS)
    for a, b in PAIRS:
        expr = f"f ({str(a).lower()}, {str(b).lower()})"
        if (a, b) not in covered:
            with pytest.raises(EvaluationError, match="Match_failure"):
                session.eval(expr)
        else:
            session.eval(expr)


def test_warning_history_does_not_repeat_in_results_and_failed_phrases_do_not_leak():
    session = Session()
    assert not session.warnings
    assert len(session.check("let f = function Some x -> x").warnings) == 1
    with pytest.raises(TypeCheckError):
        session.check("let f = function true -> 0 | false -> false")
    assert not session.check("let answer = 42").warnings
    assert len(session.warnings) == 1


@pytest.mark.parametrize("strict", [False, True])
def test_cli_warning_json_and_strict_refusal_before_certificate(tmp_path, capsys, strict):
    path = tmp_path / "partial.hyp"
    path.write_text("let f = function Some x -> x")
    certificate = tmp_path / "certificate.json"
    args = ["check", str(path), "--format", "json", "--emit-certificate", str(certificate)]
    if strict:
        args.append("--strict")
    assert main(args) == int(strict)
    document = json.loads(capsys.readouterr().out)
    assert SchemaRegistry.with_builtin_schemas().issues(DIAGNOSTICS_SCHEMA_ID, document) == []
    [warning] = document["diagnostics"]
    assert warning["severity"] == ("error" if strict else "warning")
    assert warning["file"] == str(path) and "None" in warning["message"]
    assert certificate.exists() is not strict


def test_lsp_warning_uses_editor_severity_and_target_position(tmp_path):
    path = tmp_path / "partial.hyp"
    [warning] = analyze(path, "\nlet f = function Some x -> x", tmp_path, None, {})
    assert warning.severity.name == "Warning"
    assert warning.range.start.line == 1 and "None" in warning.message


def test_prelude_and_all_examples_are_warning_free():
    root = Path(__file__).resolve().parents[2] / "demo/examples"
    examples = sorted(root.rglob("*.hyp"))
    assert len(examples) >= 6
    for path in examples:
        session = Session()
        assert not session.warnings
        if path.name == "plate.hyp":
            assert not session.check((root / "mechanics/units.hyp").read_text()).warnings
        assert not session.check(path.read_text()).warnings, path


@pytest.mark.parametrize("as_entry", [False, True])
@pytest.mark.parametrize("strict", [False, True])
def test_m2_warnings_keep_their_own_filename(tmp_path, capsys, as_entry, strict):
    root = tmp_path / "language"
    root.mkdir()
    entry = root / "langage.hyp"
    entry.write_text('language sample = { version = "1"; sources = ["partial.hyp"] }')
    partial = root / "partial.hyp"
    partial.write_text("(** Une fonction partielle. *)\nlet f = function Some x -> x")
    program = tmp_path / "program.hyp"
    program.write_text("let x = 1")
    args = (
        ["check", str(entry), "--format", "json"]
        if as_entry
        else ["check", "--langage", str(root), str(program), "--format", "json"]
    )
    if strict:
        args.append("--strict")
    assert main(args) == int(strict)
    [warning] = json.loads(capsys.readouterr().out)["diagnostics"]
    assert warning["file"] == str(partial) and warning["line"] == 2
    assert warning["severity"] == ("error" if strict else "warning")
    [editor] = analyze(partial, partial.read_text(), tmp_path, None, {})
    assert editor.severity.name == "Warning" and editor.range.start.line == 1
    assert analyze(program, program.read_text(), tmp_path, str(root), {}) == []


def test_text_warning_strict_refusal_and_warning_before_later_error(tmp_path, capsys):
    partial = tmp_path / "partial.hyp"
    partial.write_text("let f = function Some x -> x")
    broken = tmp_path / "broken.hyp"
    broken.write_text("let bad = unknown")
    assert main(["check", str(partial), "--strict"]) == 1
    text = capsys.readouterr()
    assert "None" in text.err and "mode strict" in text.err
    assert main(["check", str(partial), str(broken), "--format", "json"]) == 1
    issues = json.loads(capsys.readouterr().out)["diagnostics"]
    assert [issue["severity"] for issue in issues] == ["warning", "error"]
    assert [issue["file"] for issue in issues] == [str(partial), str(broken)]
