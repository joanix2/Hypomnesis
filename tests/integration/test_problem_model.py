"""Feasibility model correspondence; no solver result is itself trusted."""

import json
import math
import random
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from hypomnesis.backends import z3_solver
from hypomnesis.engine.bridge import BridgeError, solution_value
from hypomnesis.ir.problem import Constraint, Problem, Solution, Variable, check_assignment

FORMAL = Path(__file__).resolve().parents[2] / "formal"


def _rat(value):
    q = Fraction(str(value)) if isinstance(value, float) else Fraction(value)
    return f"(({q.numerator} : Rat) / {q.denominator})"


def _scalar(value):
    if type(value) is bool:
        return f"Scalar.boolean {str(value).lower()}"
    if not isinstance(value, (int, float, Fraction)) or (
        isinstance(value, float) and not math.isfinite(value)
    ):
        return "Scalar.invalid"
    return f"Scalar.number {_rat(value)}"


def _list(values):
    return "[" + ", ".join(values) + "]"


def _case(problem, assignment):
    def bound(value):
        return "none" if value is None else f"some {_rat(value)}"

    kinds = {"real": "real", "int": "integer", "bool": "boolean"}
    relations = {"<=": "le", ">=": "ge", "==": "eq"}
    variables = _list(
        f"⟨{json.dumps(v.name, ensure_ascii=False)}, .{kinds[v.kind]}, "
        f"{bound(v.lower)}, {bound(v.upper)}, {_list(_scalar(x) for x in v.choices)}⟩"
        for v in problem.variables
    )
    constraints = _list(
        "⟨"
        + _list(f"({json.dumps(n)}, {_rat(k)})" for n, k in c.terms)
        + f", .{relations[c.op]}, {_rat(c.rhs)}⟩"
        for c in problem.constraints
    )
    values = _list(f"({json.dumps(n)}, {_scalar(x)})" for n, x in assignment.items())
    return f"(⟨{variables}, {constraints}⟩, {values})"


@pytest.fixture(scope="module")
def lean_check(lean_lake, tmp_path_factory):
    built = subprocess.run(
        [lean_lake, "build", "Hypomnesis.Problem.Check"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    directory = tmp_path_factory.mktemp("lean-problem")

    def compare(cases):
        actual = []
        for start in range(0, len(cases), 40):
            batch = cases[start : start + 40]
            source = directory / "Samples.lean"
            source.write_text(
                "import Hypomnesis.Problem.Check\nimport Lean\n"
                "open Hypomnesis.Problem\n"
                "set_option maxRecDepth 4096\n"
                "set_option maxHeartbeats 4000000\n"
                "def cases : List (Problem × Assignment) := "
                + _list(_case(p, a) for p, a in batch)
                + "\n#eval IO.println (Lean.toJson "
                "(cases.map fun (p, a) => check p a)).compress\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [lean_lake, "env", "lean", f"--root={directory}", str(source)],
                cwd=FORMAL,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            actual.extend(json.loads(result.stdout))
        expected = [not check_assignment(p, a) for p, a in cases]
        assert actual == expected
        assert len(actual) == len(cases)
        return actual

    return compare


def _generated():
    rng = random.Random(53)
    for index in range(24):
        assignment = {
            "r": Fraction(rng.randint(-6, 6), 3),
            "i": rng.randint(-2, 2),
            "b": rng.choice([False, True]),
        }
        variables = (
            Variable("r", -3, 3, (assignment["r"],) if index % 2 else ()),
            Variable("i", -3, 3, (assignment["i"],) if index % 3 else (), "int"),
            Variable("b", choices=(assignment["b"],) if index % 2 else (), kind="bool"),
        )
        constraints = []
        for relation in ("<=", ">=", "=="):
            terms = tuple((name, Fraction(rng.randint(-4, 4), 3)) for name in assignment)
            lhs = sum(k * int(assignment[n]) if n == "b" else k * assignment[n] for n, k in terms)
            constraints.append(Constraint(relation, terms, relation, lhs))
        yield (
            Problem(variables, tuple(constraints), ("r", assignment["r"]) if index % 2 else None),
            assignment,
        )


def test_generated_domains_constraints_and_corrupt_assignments(lean_check):
    cases = []
    for problem, assignment in _generated():
        cases.append((problem, assignment))
        cases.extend(
            (problem, assignment | {"r": value})
            for value in (Fraction(1, 7), -4, 4, True, float("nan"), float("inf"), "bad", None)
        )
        cases.extend(
            [
                (problem, assignment | {"i": Fraction(3, 2)}),
                (problem, assignment | {"i": True}),
                (problem, assignment | {"b": 1}),
                (problem, assignment | {"unknown": 0}),
                (problem, {n: v for n, v in assignment.items() if n != "r"}),
            ]
        )
    verdicts = lean_check(cases)
    assert len(verdicts) == 24 * 14
    assert all(verdicts[index] for index in range(0, len(verdicts), 14))
    assert not all(verdicts)


def test_exact_boundaries_empty_sums_and_negative_coefficients(lean_check):
    cases = [(Problem((), ()), {}), (Problem((), ()), {"extra": 0})]
    for relation in ("<=", ">=", "=="):
        for rhs in (-1, 0, 1):
            cases.append((Problem((), (Constraint("empty", (), relation, rhs),)), {}))
    for goal in (Fraction(1, 3), Fraction(-2, 7), 2**100 + 1, -(2**100), 0.1):
        problem = Problem(
            (Variable("x", lower=goal, upper=goal, choices=(goal,)),),
            (Constraint("exact", (("x", Fraction(-3, 7)),), "==", Fraction(str(goal)) * -3 / 7),),
        )
        cases.append((problem, {"x": goal}))
        cases.append((problem, {"x": Fraction(str(goal)) + Fraction(1, 10**30)}))
    for allowed in (False, True):
        problem = Problem(
            (Variable("b", choices=(allowed,), kind="bool"),),
            (Constraint("as-number", (("b", -2),), "==", -2 * allowed),),
        )
        cases.extend((problem, {"b": value}) for value in (False, True, 0, 1))
    verdicts = lean_check(cases)
    assert verdicts[0] and not verdicts[1]
    assert sum(verdicts) > 5


def test_real_z3_models_and_falsified_provider_claims(lean_check):
    cases = []
    for problem, _ in _generated():
        result = z3_solver.solve(problem)
        assert result.status == "sat" and not result.violations
        assert solution_value(problem, result).type_name == "Problem.solution"
        cases.append((problem, result.assignment))
        false = dict(result.assignment) | {"b": 1}
        assert check_assignment(problem, false)
        with pytest.raises(BridgeError, match="invalid solver assignment"):
            solution_value(problem, Solution("sat", false))
        cases.append((problem, false))
    assert lean_check(cases) == [True, False] * 24
