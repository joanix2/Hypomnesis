"""Certificats JSON de la Core IR élaborée (HYP-025)."""

import json
from pathlib import Path

import pytest

from hypomnesis.certify import (
    CERTIFICATE_SCHEMA_ID,
    CertificateError,
    export_certificate,
    load_definitions,
    session_certificate,
)
from hypomnesis.cli import main
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.runtime.interpreter import Interpreter
from hypomnesis.runtime.values import Function, show
from hypomnesis.session import Session, run_deep

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
PROGRAMS = {
    "prélude seul": [],
    "tour": [EXAMPLES / "basics" / "tour.hyp"],
    "mécanique": [EXAMPLES / "mechanics" / "units.hyp", EXAMPLES / "mechanics" / "plate.hyp"],
}


@pytest.fixture(scope="module")
def registry() -> SchemaRegistry:
    return SchemaRegistry.with_builtin_schemas()


def session_for(paths: list[Path]) -> Session:
    session = Session()
    for path in paths:
        session.load(path.read_text())
    return session


def certificate_of(source: str) -> dict:
    session = Session()
    session.load(source)
    return session_certificate(session)


def user_definitions(source: str) -> list[dict]:
    """Les définitions du programme, sans celles du prélude."""
    prelude = len(Session().definitions)
    return certificate_of(source)["definitions"][prelude:]


@pytest.mark.parametrize("paths", PROGRAMS.values(), ids=PROGRAMS.keys())
def test_certificate_is_valid_against_its_schema(paths, registry):
    certificate = session_certificate(session_for(paths))
    assert registry.issues(CERTIFICATE_SCHEMA_ID, certificate) == []


@pytest.mark.parametrize("paths", PROGRAMS.values(), ids=PROGRAMS.keys())
def test_round_trip_loses_nothing(paths):
    session = session_for(paths)
    certificate = session_certificate(session)
    reloaded = load_definitions(json.loads(json.dumps(certificate)))
    types = session.checker.types_by_qname.values()
    again = export_certificate(types, reloaded, program_start=certificate["program_start"])
    assert again == certificate


@pytest.mark.parametrize("paths", PROGRAMS.values(), ids=PROGRAMS.keys())
def test_reloaded_program_computes_the_same_values(paths):
    session = session_for(paths)
    reloaded = load_definitions(session_certificate(session))
    interpreter = Interpreter(session.natives)
    run_deep(lambda: interpreter.execute(reloaded))
    compared = 0
    for qname, value in session.interpreter.globals.items():
        if not isinstance(value, Function):
            assert show(interpreter.globals[qname]) == show(value), qname
            compared += 1
    assert compared > 0


def test_locals_are_de_bruijn_indices():
    (definition,) = user_definitions("let first x y = x")
    lam = definition["value"]["expr"]["lam"]
    assert len(lam["params"]) == 2
    assert lam["body"]["local"]["index"] == 1


def test_or_patterns_share_slots():
    source = "type t = A of int | B of int\nlet get v = match v with A x | B x -> x"
    (definition,) = user_definitions(source)
    case = definition["value"]["expr"]["lam"]["body"]["match"]["cases"][0]
    left, right = case["pattern"]["or"]
    assert left["ctor"]["arg"] == right["ctor"]["arg"] == {"bind": 0}
    assert case["body"]["local"]["index"] == 0


def test_polymorphism_is_explicit():
    (definition,) = user_definitions("let pair = let id x = x in (id 1, id true)")
    let = definition["value"]["expr"]["let"]
    assert let["forall"] == ["a0"]
    uses = [item["app"]["fn"]["local"]["type_args"] for item in let["body"]["tuple"]]
    assert uses == [[{"con": "int", "args": []}], [{"con": "bool", "args": []}]]


def test_literals_keep_their_kind():
    (definition,) = user_definitions('let xs = (1, 1.0, true, "s", ())')
    kinds = [item["lit"]["kind"] for item in definition["value"]["expr"]["tuple"]]
    assert kinds == ["int", "float", "bool", "string", "unit"]


def test_loader_rejects_out_of_scope_index():
    certificate = certificate_of("let id x = x")
    lam = certificate["definitions"][-1]["value"]["expr"]["lam"]
    lam["body"]["local"]["index"] = 5
    with pytest.raises(CertificateError, match="out of scope"):
        load_definitions(certificate)


def test_loader_rejects_unbound_type_variable():
    certificate = certificate_of("let id x = x")
    certificate["definitions"][-1]["value"]["forall"] = []
    with pytest.raises(CertificateError, match="unbound type variable"):
        load_definitions(certificate)


def test_cli_emits_a_valid_certificate(tmp_path, registry, capsys):
    out = tmp_path / "cert.json"
    assert (
        main(["check", str(EXAMPLES / "basics" / "tour.hyp"), "--emit-certificate", str(out)]) == 0
    )
    assert registry.issues(CERTIFICATE_SCHEMA_ID, json.loads(out.read_text())) == []
    assert "definitions" in capsys.readouterr().err


# ------------------------------------------------- structure (JSON Schema)


def _break_missing_field(certificate: dict) -> None:
    del certificate["definitions"][-1]["value"]["forall"]


def _break_extra_field(certificate: dict) -> None:
    certificate["definitions"][-1]["value"]["bogus"] = 1


def _break_wrong_type(certificate: dict) -> None:
    body = certificate["definitions"][-1]["value"]["expr"]["lam"]["body"]
    body["local"]["index"] = "0"


def _break_two_keys(certificate: dict) -> None:
    certificate["definitions"][-1]["value"]["expr"]["global"] = {"name": "x", "type_args": []}


def _break_version(certificate: dict) -> None:
    certificate["certificate_version"] = "9.9.9"


INVALID_STRUCTURES = {
    "missing field": (_break_missing_field, "'forall' is a required property"),
    "extra field": (_break_extra_field, "Additional properties are not allowed"),
    "wrong type": (_break_wrong_type, "is not of type 'integer'"),
    "two keys": (_break_two_keys, "too many properties"),
    "unknown version": (_break_version, "'1.0.0' was expected"),
}
INVALID_PATHS = {
    "missing field": ".value",
    "extra field": ".value",
    "wrong type": ".value.expr.lam.body.local.index",
    "two keys": ".value.expr",
    "unknown version": "$.certificate_version",
}


@pytest.mark.parametrize("case", INVALID_STRUCTURES)
def test_loader_rejects_invalid_structure_with_its_json_path(case):
    certificate = certificate_of("let id x = x")
    last = len(certificate["definitions"]) - 1
    breaker, message = INVALID_STRUCTURES[case]
    breaker(certificate)
    with pytest.raises(CertificateError) as raised:
        load_definitions(certificate)
    text = str(raised.value)
    assert message in text
    path = INVALID_PATHS[case]
    expected = path if path.startswith("$") else f"$.definitions[{last}]{path}"
    assert expected in text
