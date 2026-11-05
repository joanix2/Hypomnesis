"""Machine execution results preserve refusal, partial execution, and clean stdout."""

import json
import shutil
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import SchemaRegistry

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/ventilation"
PROGRAM = ROOT / "demo/programs/ventilation/salle_serveurs.hyp"
SCHEMA_ID = "https://schemas.example.org/hypomnesis/cli-execution/1.0.0"


def output(capsys):
    captured = capsys.readouterr()
    document = json.loads(captured.out)
    SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, document)
    return document, captured.err


@pytest.mark.parametrize("kind", ["language", "program", "environment"])
def test_execution_refusals_are_structured(kind, tmp_path, capsys):
    language, program = LANGUAGE, PROGRAM
    extra = []
    if kind == "language":
        language = tmp_path / "absent"
    elif kind == "program":
        program = tmp_path / "wrong.hyp"
        program.write_text("let procedure = 1 + true", encoding="utf-8")
    else:
        extra = ["--env", "missing-separator"]
    assert (
        main(
            [
                "lancer",
                str(language),
                str(program),
                "--format",
                "json",
                "--sortie",
                str(tmp_path / "out"),
                *extra,
            ]
        )
        == 1
    )
    result, _ = output(capsys)
    assert result["status"] == "error" and result["report"] is None
    assert result["diagnostics"][0]["severity"] == "error"
    if kind == "program":
        assert result["diagnostics"][0]["stage"] == "type"


def test_missing_program_has_a_structured_usage_refusal(capsys):
    assert main(["lancer", str(LANGUAGE), "--format", "json"]) == 64
    result, _ = output(capsys)
    assert result["status"] == "error"
    assert "requis" in result["diagnostics"][0]["message"]


def test_python_adapter_logs_do_not_pollute_json_stdout(tmp_path, capsys):
    language = tmp_path / "language"
    shutil.copytree(LANGUAGE, language)
    adapter = language / "adaptateurs/piece.py"
    adapter.write_text(
        adapter.read_text(encoding="utf-8") + '\nprint("adapter debug message")\n',
        encoding="utf-8",
    )
    assert (
        main(
            [
                "lancer",
                str(language),
                str(PROGRAM),
                "--mode",
                "dry-run",
                "--format",
                "json",
                "--sortie",
                str(tmp_path / "out"),
            ]
        )
        == 0
    )
    result, logs = output(capsys)
    assert result["status"] == "ok" and "adapter debug message" in logs


def test_budget_exhaustion_is_a_partial_report_not_a_success(tmp_path, capsys):
    program = tmp_path / "infinite.hyp"
    program.write_text(
        'let rec loop () = Effect.note "tick" >>= fun () -> loop ()\nlet procedure = loop ()',
        encoding="utf-8",
    )
    assert (
        main(
            [
                "lancer",
                str(LANGUAGE),
                str(program),
                "--format",
                "json",
                "--sortie",
                str(tmp_path / "out"),
            ]
        )
        == 1
    )
    result, _ = output(capsys)
    assert result["status"] == "stopped"
    assert result["report"]["steps"] == 1001 and len(result["report"]["notes"]) == 1000
    assert "1000" in result["report"]["stopped"]
    assert result["diagnostics"] and result["report"]["result"] is None
