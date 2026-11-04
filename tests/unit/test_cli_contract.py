"""CLI contract: exit codes and option parsing, independent of the argument-parsing library."""

from __future__ import annotations

from pathlib import Path

import pytest

from hypomnesis import __version__
from hypomnesis.cli import main

ROOT = Path(__file__).resolve().parents[2]
VENTILATION = ROOT / "languages" / "ventilation"
PROGRAM = ROOT / "programs" / "ventilation" / "salle_serveurs.hyp"


def code(argv: list[str]) -> int:
    """Exit status of ``main``, whether it returns it or exits (usage errors)."""
    try:
        return main(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1


def test_version_flag(capsys):
    assert code(["--version"]) == 0
    assert f"hypomnesis {__version__}" in capsys.readouterr().out


def test_run_and_check_succeed_on_a_valid_file(tmp_path, capsys):
    good = tmp_path / "good.hyp"
    good.write_text("let x = 1 + 2")
    assert code(["run", str(good)]) == 0
    assert "val x" in capsys.readouterr().out
    assert code(["check", str(good)]) == 0


def test_run_reports_a_type_error_with_status_1(tmp_path, capsys):
    bad = tmp_path / "bad.hyp"
    bad.write_text("let x = 1 +. 2.0")
    assert code(["run", str(bad)]) == 1
    assert "bad.hyp:1:9: type error" in capsys.readouterr().err


def test_check_accepts_several_files_in_order(tmp_path, capsys):
    first, second = tmp_path / "a.hyp", tmp_path / "b.hyp"
    first.write_text("let x = 1")
    second.write_text("let y = x + 1")
    assert code(["check", str(first), str(second)]) == 0
    assert "y" in capsys.readouterr().out


def test_emit_certificate_writes_a_file(tmp_path):
    good = tmp_path / "good.hyp"
    good.write_text("let x = 1")
    certificate = tmp_path / "cert.json"
    assert code(["check", str(good), "--emit-certificate", str(certificate)]) == 0
    assert certificate.read_text(encoding="utf-8").startswith("{")


def test_missing_source_file_is_refused(tmp_path):
    assert code(["run", str(tmp_path / "absent.hyp")]) != 0
    assert code(["check", str(tmp_path / "absent.hyp")]) != 0


def test_unknown_command_and_missing_command_are_refused():
    assert code(["inconnu"]) != 0
    assert code([]) != 0


def test_lancer_without_program_nor_request_exits_64(tmp_path, capsys):
    assert code(["lancer", str(VENTILATION), "--sortie", str(tmp_path)]) == 64
    assert "requis" in capsys.readouterr().err


def test_lancer_unknown_mode_is_refused_before_loading(tmp_path, capsys):
    argv = [
        "lancer",
        str(VENTILATION),
        str(PROGRAM),
        "--mode",
        "inconnu",
        "--sortie",
        str(tmp_path),
    ]
    assert code(argv) != 0
    assert "hypothèse réfutée" not in capsys.readouterr().out


def test_lancer_repeated_env_options(tmp_path, capsys):
    argv = ["lancer", str(VENTILATION), str(PROGRAM), "--sortie", str(tmp_path)]
    assert code([*argv, "--env", "a=1", "--env", "panne=1"]) == 0
    assert "hypothèse réfutée" in capsys.readouterr().out


@pytest.mark.parametrize("mode", ["simulate", "dry-run", "production"])
def test_lancer_accepts_every_mode(mode, tmp_path):
    argv = ["lancer", str(VENTILATION), str(PROGRAM), "--mode", mode, "--sortie", str(tmp_path)]
    assert code(argv) in (0, 1)  # production may be refused by the language's permissions


def test_lancer_without_permission_is_accepted(tmp_path):
    argv = [
        "lancer",
        str(VENTILATION),
        str(PROGRAM),
        "--sans-permission",
        "--sortie",
        str(tmp_path),
    ]
    assert code(argv) in (0, 1)


def test_lancer_and_decrire_refuse_an_absent_language_with_status_1(tmp_path, capsys):
    assert code(["lancer", str(tmp_path / "absent"), str(PROGRAM)]) == 1
    assert "refusé :" in capsys.readouterr().err
    assert code(["decrire", str(tmp_path / "absent")]) == 1
    assert "refusé :" in capsys.readouterr().err


def test_decrire_unknown_format_is_refused():
    assert code(["decrire", str(VENTILATION), "--format", "xml"]) != 0


def test_benchmark_requires_models():
    assert code(["benchmark-llm", str(VENTILATION)]) != 0
