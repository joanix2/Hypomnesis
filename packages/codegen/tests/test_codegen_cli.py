"""CLI boundary and argument contract of the optional generation package."""

from pathlib import Path

import pytest

from hypomnesis_codegen.cli import main

LANGUAGE = Path(__file__).resolve().parents[3] / "demo" / "languages" / "ventilation"


def test_help_lists_generation_commands_only(capsys):
    assert main(["--help"]) == 0
    help_text = capsys.readouterr().out
    for command in ("decrire", "benchmark-llm", "graphiques-llm"):
        assert command in help_text


@pytest.mark.parametrize("command", ["run", "check", "repl", "lancer", "plugins"])
def test_core_commands_are_not_in_codegen(command):
    assert main([command]) == 2


def test_decrire_refuses_an_absent_language_with_status_1(tmp_path, capsys):
    assert main(["decrire", str(tmp_path / "absent")]) == 1
    assert "refusé :" in capsys.readouterr().err


def test_decrire_unknown_format_is_refused():
    assert main(["decrire", str(LANGUAGE), "--format", "xml"]) == 2


def test_benchmark_requires_models():
    assert main(["benchmark-llm", str(LANGUAGE)]) == 2
