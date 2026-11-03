"""Le vérificateur Lean (`hypomnesis-check`, HYP-026) sur des certificats réels.

Ignoré si l'exécutable n'est pas construit : `cd formal && lake build hypomnesis-check`.
"""

import json
import subprocess
from pathlib import Path

import pytest

from hypomnesis.certify import session_certificate
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "formal" / ".lake" / "build" / "bin" / "hypomnesis-check"
EXAMPLES = ROOT / "examples"

pytestmark = pytest.mark.skipif(not EXE.exists(), reason="hypomnesis-check non construit")


def certificate(*paths: Path) -> dict:
    session = Session()
    for path in paths:
        session.load(path.read_text())
    return session_certificate(session)


def run(command: str, cert: dict, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "cert.json"
    path.write_text(json.dumps(cert))
    return subprocess.run(
        [str(EXE), command, str(path)], capture_output=True, text=True, timeout=120, check=False
    )


def test_certifiable_example_is_accepted(tmp_path):
    result = run("check", certificate(EXAMPLES / "basics" / "certifiable.hyp"), tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("accepté")


def test_lean_semantics_computes_the_same_values(tmp_path):
    result = run("eval", certificate(EXAMPLES / "basics" / "certifiable.hyp"), tmp_path)
    assert result.returncode == 0, result.stderr
    # Racines dans l'ordre du programme : …, total = 30, …, biggest = 10, …, f5 = 120.
    for expected in ("30", "10", "120"):
        assert expected in result.stdout
    assert "#1 (1, #1 (4, #1 (9, #1 (16, #0 ()))))" in result.stdout  # squares


def test_altered_certificate_is_rejected(tmp_path):
    cert = certificate(EXAMPLES / "basics" / "certifiable.hyp")
    literal = cert["definitions"][-1]["value"]["expr"]["app"]["args"][0]
    assert literal == {"lit": {"kind": "int", "value": 5}}
    literal["lit"] = {"kind": "bool", "value": True}  # fact true
    result = run("check", cert, tmp_path)
    assert result.returncode == 1
    assert "rejeté" in result.stderr


def test_program_outside_the_fragment_is_reported(tmp_path):
    result = run("check", certificate(EXAMPLES / "basics" / "tour.hyp"), tmp_path)
    assert result.returncode == 2
    assert "hors du fragment" in result.stderr


def test_malformed_certificate(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{pas du json")
    result = subprocess.run(
        [str(EXE), "check", str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 3
