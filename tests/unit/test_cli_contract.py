"""CLI contract: exit codes and option parsing, independent of the argument-parsing library."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hypomnesis import __version__
from hypomnesis.cli import main

ROOT = Path(__file__).resolve().parents[2]
VENTILATION = ROOT / "demo" / "languages" / "ventilation"
PROGRAM = ROOT / "demo" / "programs" / "ventilation" / "salle_serveurs.hyp"


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


def test_lancer_default_results_stay_under_demo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert code(["lancer", str(VENTILATION), str(PROGRAM)]) == 0
    assert (tmp_path / "demo" / "sortie" / "rapport.json").is_file()
    assert not (tmp_path / "sortie").exists()


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


def test_lancer_refuses_an_absent_language_with_status_1(tmp_path, capsys):
    assert code(["lancer", str(tmp_path / "absent"), str(PROGRAM)]) == 1
    assert "refusé :" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["decrire", "benchmark-llm", "graphiques-llm"])
def test_codegen_commands_are_not_in_the_core_cli(command):
    assert code([command]) == 2


def test_plugins_list_uses_only_explicit_manifests(tmp_path, capsys, extension_manifest):
    (tmp_path / "manifest.json").write_text(json.dumps(extension_manifest()))
    assert code(["plugins", "list"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == []
    assert output.err == ""


def test_plugins_list_files_directory_and_role(tmp_path, capsys, extension_manifest):
    directory = tmp_path / "manifests"
    directory.mkdir()
    manifests = [
        extension_manifest("a", "1.0.0", "Observer"),
        extension_manifest("a", "2.0.0", "Solver"),
        extension_manifest("b", "1.0.0", "Solver", description="Métadonnées lisibles"),
    ]
    for index, manifest in enumerate(manifests[:2]):
        (directory / f"{index}.json").write_text(json.dumps(manifest))
    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps(manifests[2]))
    (directory / "ignored.py").write_text("raise AssertionError('must not execute')")
    paths = ["--manifest", str(directory), "--manifest", str(extra)]
    assert code(["plugins", "list", *paths]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == [manifests[1], manifests[0], manifests[2]]
    assert "\n  {" in output.out
    assert "Métadonnées lisibles" in output.out
    assert output.err == ""
    assert code(["plugins", "list", *paths, "--role", "Solver"]) == 0
    assert json.loads(capsys.readouterr().out) == [manifests[1], manifests[2]]


def test_plugins_show_latest_or_exact_version(tmp_path, capsys, extension_manifest):
    old, latest = extension_manifest(), extension_manifest(version="2.0.0")
    for name, manifest in (("old", old), ("latest", latest)):
        (tmp_path / f"{name}.json").write_text(json.dumps(manifest))
    args = ["plugins", "show", "sample", "--manifest", str(tmp_path)]
    assert code(args) == 0
    assert json.loads(capsys.readouterr().out) == latest
    assert code([*args, "--version", "1.0.0"]) == 0
    assert json.loads(capsys.readouterr().out) == old
    assert code([*args, "--version", "9.0.0"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "refusé :" in output.err and "9.0.0" in output.err


@pytest.mark.parametrize("command", ["list", "show"])
def test_plugins_inspection_neither_resolves_nor_imports(
    command, tmp_path, capsys, extension_manifest, trapped_backend
):
    manifest = extension_manifest(dependencies=[("absent", ">=1.0.0,<2")])
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    args = ["plugins", command, *(["sample"] if command == "show" else [])]
    assert code([*args, "--manifest", str(path)]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == (manifest if command == "show" else [manifest])
    assert output.err == ""
    assert not trapped_backend.exists()


@pytest.mark.parametrize("content", ["not JSON", "[]", '{"id": "invalid"}'])
def test_plugins_invalid_manifest_has_no_partial_output(
    content, tmp_path, capsys, extension_manifest
):
    (tmp_path / "a.json").write_text(json.dumps(extension_manifest()))
    (tmp_path / "z.json").write_text(content)
    assert code(["plugins", "list", "--manifest", str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "refusé :" in output.err


def test_plugins_conflicting_duplicate_is_refused(tmp_path, capsys, extension_manifest):
    (tmp_path / "a.json").write_text(json.dumps(extension_manifest()))
    (tmp_path / "b.json").write_text(json.dumps(extension_manifest(description="different")))
    assert code(["plugins", "list", "--manifest", str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "different content" in output.err


def test_plugins_unknown_id_and_role_are_application_errors(capsys):
    assert code(["plugins", "show", "absent"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "refusé :" in output.err and "absent" in output.err
    assert code(["plugins", "list", "--role", "Wizard"]) == 1
    assert "unknown role" in capsys.readouterr().err


def test_plugins_missing_file_and_invalid_usage_exit_2(tmp_path, capsys):
    assert code(["plugins", "list", "--manifest", str(tmp_path / "absent.json")]) == 2
    assert code(["plugins", "show"]) == 2
    assert code(["plugins", "list", "--unknown"]) == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("args", [["plugins", "--help"], ["plugins", "show", "--help"]])
def test_plugins_help_succeeds(args, capsys):
    assert code(args) == 0
    assert "Usage:" in capsys.readouterr().out
