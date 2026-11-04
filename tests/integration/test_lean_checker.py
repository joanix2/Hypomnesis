"""Le vérificateur Lean (`hypomnesis-check`, HYP-026) sur des certificats réels.

Ignoré si l'exécutable n'est pas construit : `cd formal && lake build hypomnesis-check`.
"""

import json
import subprocess
from pathlib import Path

import pytest

from hypomnesis.certify import session_certificate
from hypomnesis.cli import main
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "formal" / ".lake" / "build" / "bin" / "hypomnesis-check"
EXAMPLES = ROOT / "demo" / "examples"

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


def test_cli_certifies_real_example_with_one_final_json_document(capsys):
    assert (
        main(
            [
                "check",
                str(EXAMPLES / "basics/certifiable.hyp"),
                "--certify",
                "--checker",
                str(EXE),
                "--format",
                "json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert json.loads(captured.out)["diagnostics"] == []
    assert "accepté" in captured.err


def test_cli_refuses_injected_miselaboration(tmp_path, capsys, monkeypatch):
    import hypomnesis.certify as module

    original = module.session_certificate

    def altered(session):
        document = original(session)
        document["definitions"][-1]["value"]["expr"]["app"]["args"][0]["lit"] = {
            "kind": "bool",
            "value": True,
        }
        return document

    monkeypatch.setattr(module, "session_certificate", altered)
    path = tmp_path / "altered.json"
    assert (
        main(
            [
                "check",
                str(EXAMPLES / "basics/certifiable.hyp"),
                "--certify",
                "--emit-certificate",
                str(path),
                "--checker",
                str(EXE),
                "--format",
                "json",
            ]
        )
        == 1
    )
    diagnostics = json.loads(capsys.readouterr().out)["diagnostics"]
    assert diagnostics and "rejeté" in diagnostics[0]["message"]
    assert path.is_file()


CASES = (
    (("basics/certifiable.hyp",), 0),
    (("basics/tour.hyp",), 2),
    (("knowledge/plaque.hyp",), 0),
    (("knowledge/regles.hyp",), 0),
    (("mechanics/units.hyp",), 0),
    (("mechanics/units.hyp", "mechanics/plate.hyp"), 0),
)


def test_every_example_has_an_explicit_certification_expectation():
    assert {name for names, _ in CASES for name in names} == {
        str(path.relative_to(EXAMPLES)) for path in EXAMPLES.rglob("*.hyp")
    }


@pytest.mark.parametrize(("names", "status"), CASES, ids=lambda value: str(value))
def test_all_examples_are_examined_without_claiming_unsupported_forms_are_certified(
    tmp_path, names, status
):
    result = run("check", certificate(*(EXAMPLES / name for name in names)), tmp_path)
    assert result.returncode == status, result.stderr
    if status == 2:
        assert "hors du fragment" in result.stderr


@pytest.mark.parametrize(
    "source",
    [
        """
        type account = { owner : int; balance : int }
        let deposit amount acc = { acc with balance = acc.balance + amount }
        let alice = { balance = 100; owner = 77 }
        let updated = deposit 50 alice
        let answer =
          match updated with
          | { balance = b; owner = o } ->
            if b = 150 && o = 77 && alice.balance = 100 then 99991 else 99992
        """,
        """
        type account = { owner : int; balance : int }
        let value = Some { owner = 77; balance = 150 }
        let answer = match value with
          | Some { balance = b; owner = o } -> if b = 150 && o = 77 then 99991 else 99992
          | None -> 99992
        """,
        """
        type 'a box = { payload : 'a; label : int }
        let get b = b.payload
        let a = get { label = 2; payload = 41 }
        let b = get { label = 3; payload = true }
        let answer = if a = 41 && b then 99991 else 99992
        """,
        """
        type node = { value : int; next : node option }
        let n = { next = None; value = 17 }
        let answer = match n with
          | { value = v } -> if v = 17 then 99991 else 99992
        """,
        """
        type item = { first : int; second : int; third : int }
        let f x =
          let n = 4 in
          let a = { third = n + 2; first = x; second = n + 1 } in
          let b = { a with third = a.second + n; first = a.third + x } in
          match (b, a) with
          | ({ third = t; first = f }, { second = s }) ->
            if t = 9 && f = 13 && s = 5 then 99991 else 99992
        let answer = f 7
        """,
        """
        type account = { owner : int; balance : int }
        let account = { balance = 150; owner = 77 }
        let answer = match account with
          | { balance = b; owner = o } when b < 0 -> 99992
          | { balance = b; owner = o } when o = 77 -> if b = 150 then 99991 else 99992
          | _ -> 99992
        """,
    ],
)
def test_nominal_records_updates_and_patterns_have_matching_lean_semantics(tmp_path, source):
    session = Session()
    session.load(source)
    assert session.value("answer") == 99991
    result = run("eval", session_certificate(session), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "99991" in result.stdout and "99992" not in result.stdout


@pytest.mark.parametrize("mutation", ["unknown", "duplicate", "missing", "value_type", "nominal"])
def test_record_certificate_mutations_are_rejected(tmp_path, mutation):
    session = Session()
    session.load(
        "module A = struct type t = { x : int; y : bool } end\n"
        "module B = struct type t = { x : int; y : bool } end\n"
        "let value = { A.x = 3; y = true }\n"
    )
    document = session_certificate(session)
    record = document["definitions"][-1]["value"]["expr"]["record"]
    fields = record["fields"]
    if mutation == "unknown":
        fields[0]["name"] = "unknown"
    elif mutation == "duplicate":
        fields.append(fields[0])
    elif mutation == "missing":
        fields.pop()
    elif mutation == "value_type":
        fields[0]["value"] = {"lit": {"kind": "bool", "value": False}}
    else:
        record["type"] = "B.t"
    result = run("check", document, tmp_path)
    assert result.returncode in (1, 3), result.stderr


@pytest.mark.parametrize(
    "source",
    [
        "let answer = if 0.1 +. 0.2 <> 0.3 then 99991 else 99992",
        "let answer = if 1e-323 /. 5e-324 = 2.0 then 99991 else 99992",
        "let answer = if 1.0 /. (-.0.0) < 0.0 then 99991 else 99992",
        "let n = 0.0 /. 0.0\n"
        "let answer = if n <> n && n <= 0.0 && not (n >= 0.0) && n <= n && not (n < n) "
        "&& compare n n = 0 && compare n 0.0 < 0 then 99991 else 99992",
        "let huge = 1e308 *. 1e308\n"
        "let answer = if huge > 1e308 && huge = 1.0 /. 0.0 then 99991 else 99992",
        'let answer = match "été" ^ "☀" with "été☀" -> 99991 | _ -> 99992',
        "let answer = match 1.5 with 1.0 -> 99992 | 1.5 -> 99991 | _ -> 99992",
        "let answer = if (-7) / 3 = -2 && (-7) mod 3 = -1 then 99991 else 99992",
    ],
)
def test_scalar_semantics_agree_with_python(tmp_path, source):
    session = Session()
    session.load(source)
    assert session.value("answer") == 99991
    result = run("eval", session_certificate(session), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "99991" in result.stdout and "99992" not in result.stdout


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("let answer = 1 / 0", "Division_by_zero"),
        ("let answer = 1 mod 0", "Division_by_zero"),
        ('let answer = 1 + failwith "explicite"', "Failure: explicite"),
    ],
)
def test_primitive_errors_remain_distinct_from_stuck_and_match_failure(tmp_path, source, expected):
    session = Session()
    session.check(source)
    result = run("eval", session_certificate(session), tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize("bits", [-1, 2**64, 0x7FF8000000000000, 0x3FF0000000000000])
def test_float_literal_bits_are_checked(tmp_path, bits):
    session = Session()
    session.check("let x = 0.5")
    document = session_certificate(session)
    document["definitions"][-1]["value"]["expr"]["lit"]["bits"] = bits
    result = run("check", document, tmp_path)
    assert result.returncode == 3, result.stderr


def test_native_signatures_are_not_trusted_from_the_certificate(tmp_path):
    session = Session()
    session.check("let x = 1.0 +. 2.0")
    document = session_certificate(session)
    native = next(
        d["native"]
        for d in document["definitions"]
        if d.get("native", {}).get("symbol") == "float.add"
    )
    native["symbol"] = "int.add"
    result = run("check", document, tmp_path)
    assert result.returncode == 2, result.stderr
