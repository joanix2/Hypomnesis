"""Compare completed outcomes, never Python work with Lean fuel counts."""

import json
import os
import subprocess
from pathlib import Path

import pytest
from hypothesis import HealthCheck, example, given, settings

from hypomnesis.certify import session_certificate
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.interpreter import Interpreter
from hypomnesis.runtime.values import RecordValue, Variant
from hypomnesis.session import Session, run_deep
from tests.differential.terms import TYPES, Term, terms

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "formal/.lake/build/bin/hypomnesis-check"
FUEL = 100_000
DECLARATIONS = "type cell = { count : int; flag : bool }\n"


def require_checker():
    if not EXE.is_file():
        if os.environ.get("HYPOMNESIS_REQUIRE_LEAN") == "1":
            pytest.fail("hypomnesis-check missing; build it before running differential tests")
        pytest.skip("hypomnesis-check not built; mandatory in proofs CI and validate.sh")
    return EXE


@pytest.fixture(scope="module")
def checker():
    path = require_checker()
    # Establish the runtime's stack policy before Hypothesis snapshots it.
    run_deep(lambda: None)
    return path


def test_missing_required_checker_is_not_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr("tests.differential.test_semantics.EXE", tmp_path / "missing-checker")
    monkeypatch.setenv("HYPOMNESIS_REQUIRE_LEAN", "1")
    with pytest.raises(pytest.fail.Exception, match="hypomnesis-check missing"):
        require_checker()


def show_lean(value):
    """Data representation of Certificate.showVal (functions are not observable)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, RecordValue):
        payload = "()"
        for _, item in reversed(value.fields):
            payload = f"({show_lean(item)}, {payload})"
        return f"#0 {payload}"
    if isinstance(value, Variant):
        return f"#{value.index} {show_lean(value.arg) if value.arg is not None else '()'}"
    if isinstance(value, tuple):
        if not value:
            return "()"
        if len(value) == 1:
            return show_lean(value[0])
        return f"({show_lean(value[0])}, {show_lean(value[1:])})"
    raise AssertionError(f"unhandled observable Python value: {value!r}")


def prepare(source):
    session = Session()
    session.check(DECLARATIONS + source)
    cert = session_certificate(session)
    # All dependencies remain present and are checked. Only the final,
    # monomorphic answer is an observable root, not unrelated prelude functions.
    cert["program_start"] = len(session.definitions) - 1
    assert not session.definitions[-1].forall_vars
    return session, cert


def lean_eval(checker, cert, path, fuel=FUEL):
    path.write_text(json.dumps(cert), encoding="utf-8")
    result = subprocess.run(
        [str(checker), "eval", str(path), str(fuel)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def compare(checker, source, path, *, fuel=FUEL):
    session, cert = prepare(source)
    actual = lean_eval(checker, cert, path, fuel)
    assert actual not in ("budget épuisé", "BLOQUÉ"), f"non-comparable Lean outcome: {actual}"
    try:
        run_deep(
            lambda: session.interpreter.execute(session.definitions[session.prelude_definitions :])
        )
        expected = show_lean(session.value("answer"))
    except EvaluationError as error:
        expected = error.message
    assert actual == expected, (
        f"Python/Lean divergence\n{source}\nPython: {expected}\nLean: {actual}"
    )


@settings(
    max_examples=500,
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@example(Term("int", "(let x = 7 in (fun (y : int) -> x + y) 4)"))
@example(Term("int", "((fun (x : int) -> fun (y : int) -> x - y) 8) 3"))
@example(Term("int", "((fun (x : int) -> x + 1) 3)"))
@example(Term("int", "(match [1; 2] with x :: _ -> x | [] -> 0)"))
@example(Term("int", "(match (1, 2) with (x, _) | (_, x) when x = 2 -> 0 | _ -> 17)"))
@given(terms())
def test_generated_terms(checker, tmp_path, term):
    compare(checker, f"let answer : {TYPES[term.kind]} = {term.source}", tmp_path / "term.json")


@pytest.mark.parametrize(
    "source",
    [
        "let answer = match 1 with 2 -> 3",
        "let answer = match Some 7 with None -> 0",
        "let answer = match false with true -> 0 | _ when false -> 1",
        "let answer = 17 / 0",
        "let answer = 17 mod 0",
        'let answer : int = failwith "explicit failure"',
        "let answer = match 2 with 1 | 2 -> 7 | _ -> 0",
        "let answer = (let r = { count = 7; flag = true } in "
        "let s = { r with count = r.count + 3 } in (r, s))",
        "let rec sum xs = match xs with [] -> 0 | x :: rest -> x + sum rest\n"
        "let answer = sum [1; 2; 3; 4]",
        "let answer = (fun x y -> x * y) 6 7",
        "let answer = let rec even n = if n = 0 then true else even (n - 2) in even 8",
        "let answer = (1.0 /. (-.0.0) < 0.0, 0.0 /. 0.0 <= 0.0)",
    ],
)
def test_completed_outcomes(checker, tmp_path, source):
    compare(checker, source, tmp_path / "case.json")


def test_budget_exhaustion_is_not_a_value_agreement(checker, tmp_path):
    source = "let rec count n = if n = 0 then 42 else count (n - 1)\nlet answer = count 12"
    _, cert = prepare(source)
    assert lean_eval(checker, cert, tmp_path / "budget.json", fuel=1) == "budget épuisé"
    with pytest.raises(AssertionError, match="non-comparable Lean outcome"):
        compare(checker, source, tmp_path / "budget.json", fuel=1)
    compare(checker, source, tmp_path / "budget.json")


def test_interpreter_mutation_is_detected(checker, tmp_path, monkeypatch):
    original = Interpreter._c_Literal

    def mutated(self, node, tail):
        if type(node.value) is int and node.value == 999983:
            return lambda env: node.value + 1
        return original(self, node, tail)

    monkeypatch.setattr(Interpreter, "_c_Literal", mutated)
    with pytest.raises(AssertionError, match="Python/Lean divergence"):
        compare(checker, "let answer = 999983", tmp_path / "mutation.json")
