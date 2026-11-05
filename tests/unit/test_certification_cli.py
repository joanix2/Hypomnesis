import json
import shlex
import sys

import pytest

from hypomnesis import certify
from hypomnesis.certify import CertificateError
from hypomnesis.certify.checker import (
    CertificationError,
    check_certificate,
    checker_path,
)
from hypomnesis.cli import main


def checker(tmp_path, *, code=0, delay=False):
    executable = tmp_path / "fake-checker"
    command = (
        f"exec {shlex.quote(sys.executable)} -c 'import time; time.sleep(10)'"
        if delay
        else f"echo checker-message\nexit {code}"
    )
    executable.write_text(f"#!/bin/sh\n{command}\n")
    executable.chmod(0o755)
    return executable


def source(tmp_path):
    path = tmp_path / "program.hyp"
    path.write_text("let answer = 42")
    return path


def test_missing_explicit_checker_has_no_fallback(tmp_path):
    with pytest.raises(CertificationError, match="introuvable"):
        checker_path(tmp_path / "missing")


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (1, "rejeté"),
        (2, "hors du fragment"),
        (3, "mal formé"),
        (7, "échec"),
    ],
)
def test_checker_exit_status_is_never_a_success(tmp_path, code, message):
    executable = checker(tmp_path, code=code)
    with pytest.raises(CertificationError, match=message):
        check_certificate(tmp_path / "cert.json", checker=executable)


def test_checker_timeout_is_explicit_and_bounded(tmp_path):
    executable = checker(tmp_path, delay=True)
    with pytest.raises(CertificationError, match="délai"):
        check_certificate(tmp_path / "cert.json", checker=executable, timeout_seconds=0.1)


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf")])
def test_invalid_timeout_is_refused_before_execution(tmp_path, timeout):
    with pytest.raises(CertificationError, match="positif"):
        check_certificate(tmp_path / "cert.json", timeout_seconds=timeout)


def test_cli_certification_refusal_emits_one_final_nonempty_diagnostics_document(tmp_path, capsys):
    path = source(tmp_path)
    executable = checker(tmp_path, code=2)
    assert (
        main(
            [
                "check",
                str(path),
                "--certify",
                "--checker",
                str(executable),
                "--format",
                "json",
            ]
        )
        == 1
    )
    result = json.loads(capsys.readouterr().out)
    assert result["diagnostics"] and "hors du fragment" in result["diagnostics"][0]["message"]


def test_export_failure_also_has_no_premature_success(tmp_path, capsys, monkeypatch):
    def fail(_):
        raise CertificateError("export failed")

    monkeypatch.setattr(certify, "session_certificate", fail)
    assert (
        main(
            [
                "check",
                str(source(tmp_path)),
                "--emit-certificate",
                str(tmp_path / "cert.json"),
                "--format",
                "json",
            ]
        )
        == 1
    )
    assert "export failed" in json.loads(capsys.readouterr().out)["diagnostics"][0]["message"]


def test_certificate_write_failure_is_a_cli_diagnostic(tmp_path, capsys):
    assert (
        main(
            [
                "check",
                str(source(tmp_path)),
                "--emit-certificate",
                str(tmp_path / "missing/cert.json"),
                "--format",
                "json",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["diagnostics"]


def test_language_entry_exports_its_actual_session_not_the_unused_initial_prelude(tmp_path, capsys):
    path = tmp_path / "langage.hyp"
    path.write_text(
        'language sample = struct let version = "1.0.0" end\n(** Answer. *)\nlet answer = 42'
    )
    certificate = tmp_path / "cert.json"
    assert (
        main(
            [
                "check",
                str(path),
                "--emit-certificate",
                str(certificate),
                "--certify",
                "--checker",
                str(checker(tmp_path)),
                "--format",
                "json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []
    document = json.loads(certificate.read_text())
    assert document["definitions"][-1]["value"]["targets"][0]["name"] == "answer"
    assert document["program_start"] < len(document["definitions"])


def test_temporary_certificate_is_removed_after_verification(tmp_path, capsys, monkeypatch):
    import hypomnesis.certify.checker as module

    paths = []

    def verify(path, **_):
        assert path.is_file()
        paths.append(path)
        return "accepted"

    monkeypatch.setattr(module, "check_certificate", verify)
    assert main(["check", str(source(tmp_path)), "--certify", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []
    assert len(paths) == 1 and not paths[0].exists()


def test_checker_flag_requires_certification(tmp_path, capsys):
    assert (
        main(
            [
                "check",
                str(source(tmp_path)),
                "--checker",
                str(checker(tmp_path)),
                "--format",
                "json",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["diagnostics"]
