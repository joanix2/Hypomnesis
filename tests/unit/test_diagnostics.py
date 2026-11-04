"""Structured diagnostics: ``HypomnesisError.to_diagnostic`` and ``check --format json``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.language.errors import (
    DIAGNOSTICS_SCHEMA_ID,
    DIAGNOSTICS_VERSION,
    EvaluationError,
    HypomnesisError,
    NameResolutionError,
    ParseError,
    Span,
    TypeCheckError,
    diagnostics_document,
)

ROOT = Path(__file__).resolve().parents[2]
MECANIQUE = ROOT / "demo" / "languages" / "mecanique"

UNKNOWN_FIELD = """let demande = {
  Plaque.nom = "p";
  largeur = 1.0;
  hauteur = 2.0;
  epaisseur = None;
  masse_max = 0.5;
  inconnu = 3;
}
"""


def run_json(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict]:
    """Run the CLI and return its status with the (schema-validated) stdout document."""
    status = main(argv)
    document = json.loads(capsys.readouterr().out)
    issues = SchemaRegistry.with_builtin_schemas().issues(DIAGNOSTICS_SCHEMA_ID, document)
    assert issues == []
    return status, document


def source(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "prog.hyp"
    path.write_text(text, encoding="utf-8")
    return path


def test_schema_is_a_builtin_contract():
    assert DIAGNOSTICS_SCHEMA_ID in SchemaRegistry.with_builtin_schemas()
    assert DIAGNOSTICS_SCHEMA_ID.endswith(f"/{DIAGNOSTICS_VERSION}")


def test_syntax_error_diagnostic(tmp_path, capsys):
    path = source(tmp_path, "let x = (1 +\n")
    status, document = run_json(["check", "--format", "json", str(path)], capsys)
    assert status == 1
    assert document["version"] == DIAGNOSTICS_VERSION
    [diagnostic] = document["diagnostics"]
    assert diagnostic["stage"] == "syntax"
    assert diagnostic["severity"] == "error"
    assert diagnostic["file"] == str(path)
    assert (diagnostic["line"], diagnostic["column"]) == (1, 12)
    assert (diagnostic["end_line"], diagnostic["end_column"]) == (1, 13)
    assert diagnostic["message"].startswith("unexpected end of input")


def test_type_error_diagnostic_covers_the_offending_expression(tmp_path, capsys):
    path = source(tmp_path, "let x = 1\nlet y = x +. 2.0\n")
    status, document = run_json(["check", "--format", "json", str(path)], capsys)
    assert status == 1
    [diagnostic] = document["diagnostics"]
    assert diagnostic["stage"] == "type"
    assert (diagnostic["line"], diagnostic["column"]) == (2, 9)
    assert (diagnostic["end_line"], diagnostic["end_column"]) == (2, 10)


def test_unknown_field_in_a_language_context(tmp_path, capsys):
    path = source(tmp_path, UNKNOWN_FIELD)
    argv = ["check", "--format", "json", "--langage", str(MECANIQUE), str(path)]
    status, document = run_json(argv, capsys)
    assert status == 1
    [diagnostic] = document["diagnostics"]
    assert diagnostic["stage"] == "type"
    assert "field inconnu does not belong to type demande" in diagnostic["message"]
    # The span is the record expression: it opens at the brace and closes after the last one.
    assert (diagnostic["line"], diagnostic["column"]) == (1, 15)
    assert (diagnostic["end_line"], diagnostic["end_column"]) == (8, 2)


def test_without_the_language_the_same_program_is_a_name_error(tmp_path, capsys):
    path = source(tmp_path, UNKNOWN_FIELD)
    status, document = run_json(["check", "--format", "json", str(path)], capsys)
    assert status == 1
    assert document["diagnostics"][0]["stage"] in {"name", "type"}


def test_valid_program_gives_an_empty_document(tmp_path, capsys):
    path = source(tmp_path, "let x = 1 + 2\n")
    status, document = run_json(["check", "--format", "json", str(path)], capsys)
    assert status == 0
    assert document == {"version": DIAGNOSTICS_VERSION, "diagnostics": []}


def test_valid_program_in_a_language_context(capsys):
    program = ROOT / "demo" / "programs" / "mecanique" / "plaque_120x80.hyp"
    argv = ["check", "--format", "json", "--langage", str(MECANIQUE), str(program)]
    status, document = run_json(argv, capsys)
    assert (status, document["diagnostics"]) == (0, [])


def test_text_output_is_unchanged_by_default(tmp_path, capsys):
    path = source(tmp_path, "let x = 1\nlet y = x +. 2.0\n")
    assert main(["check", str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"{path}:2:9: type error: This argument has type int" in captured.err
    explicit = main(["check", "--format", "text", str(path)])
    assert explicit == 1
    assert capsys.readouterr().err == captured.err


def test_text_signatures_are_still_printed(tmp_path, capsys):
    path = source(tmp_path, "let x = 1\n")
    assert main(["check", str(path)]) == 0
    assert "x" in capsys.readouterr().out


def test_language_option_rejects_a_folder_that_is_not_a_language(tmp_path, capsys):
    path = source(tmp_path, "let x = 1\n")
    assert main(["check", "--langage", str(tmp_path), str(path)]) == 1
    assert "langage.json" in capsys.readouterr().err


def test_unknown_format_is_a_usage_error(tmp_path):
    path = source(tmp_path, "let x = 1\n")
    assert main(["check", "--format", "xml", str(path)]) != 0


@pytest.mark.parametrize(
    ("error", "stage"),
    [
        (ParseError, "syntax"),
        (NameResolutionError, "name"),
        (TypeCheckError, "type"),
        (EvaluationError, "runtime"),
        (HypomnesisError, "error"),
    ],
)
def test_every_error_class_renders_a_valid_diagnostic(error, stage):
    diagnostic = error("boom", Span(3, 4, 3, 9)).to_diagnostic("a.hyp")
    assert diagnostic["stage"] == stage
    assert diagnostic["message"] == "boom"
    document = diagnostics_document([diagnostic])
    assert SchemaRegistry.with_builtin_schemas().issues(DIAGNOSTICS_SCHEMA_ID, document) == []


def test_unknown_subclass_is_rendered_generically():
    class DescriptionError(HypomnesisError):
        stage = "description error"

    diagnostic = DescriptionError("missing description", Span(1, 1, 1, 5)).to_diagnostic("m.hyp")
    assert diagnostic["stage"] == "error"
    assert (diagnostic["line"], diagnostic["end_column"]) == (1, 5)


def test_error_without_span_has_null_positions():
    diagnostic = TypeCheckError("boom").to_diagnostic("a.hyp")
    assert [diagnostic[k] for k in ("line", "column", "end_line", "end_column")] == [None] * 4
    document = diagnostics_document([diagnostic])
    assert SchemaRegistry.with_builtin_schemas().issues(DIAGNOSTICS_SCHEMA_ID, document) == []


def test_schema_rejects_malformed_documents():
    registry = SchemaRegistry.with_builtin_schemas()
    good = TypeCheckError("boom", Span(1, 1, 1, 2)).to_diagnostic("a.hyp")
    for bad in (
        {"version": "2.0.0", "diagnostics": []},
        {"version": DIAGNOSTICS_VERSION, "diagnostics": [{**good, "severity": "fatal"}]},
        {"version": DIAGNOSTICS_VERSION, "diagnostics": [{**good, "line": 0}]},
        {"version": DIAGNOSTICS_VERSION, "diagnostics": [{**good, "extra": 1}]},
    ):
        assert registry.issues(DIAGNOSTICS_SCHEMA_ID, bad)
