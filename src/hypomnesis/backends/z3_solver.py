"""Z3 backend for the Problem IR (cahier des charges §15.1).

Z3 is not trusted: its model is converted to exact rationals and re-checked by
:func:`hypomnesis.ir.problem.check_assignment` before being returned.
"""

from __future__ import annotations

from fractions import Fraction
from time import perf_counter

import z3

from hypomnesis.ir.problem import Problem, Solution, check_assignment

NAME = "z3"


def solve(problem: Problem, *, timeout_ms: int = 1000) -> Solution:
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("solver timeout must be a positive number of milliseconds")
    started = perf_counter()
    opt = z3.Optimize()
    opt.set(timeout=timeout_ms)
    xs = {
        v.name: {"real": z3.Real, "int": z3.Int, "bool": z3.Bool}[v.kind](v.name)
        for v in problem.variables
    }
    numeric = {
        v.name: z3.If(xs[v.name], z3.RealVal(1), z3.RealVal(0)) if v.kind == "bool" else xs[v.name]
        for v in problem.variables
    }
    for v in problem.variables:
        x = xs[v.name]
        if v.lower is not None:
            opt.add(x >= z3.RealVal(str(Fraction(v.lower))))
        if v.upper is not None:
            opt.add(x <= z3.RealVal(str(Fraction(v.upper))))
        if v.choices:
            opt.add(
                z3.Or(
                    [
                        x == (z3.BoolVal(c) if v.kind == "bool" else z3.RealVal(str(Fraction(c))))
                        for c in v.choices
                    ]
                )
            )
    for c in problem.constraints:
        lhs = z3.Sum([z3.RealVal(str(Fraction(k))) * numeric[name] for name, k in c.terms])
        rhs = z3.RealVal(str(Fraction(c.rhs)))
        opt.add({"<=": lhs <= rhs, ">=": lhs >= rhs, "==": lhs == rhs}[c.op])
    if problem.target is not None:
        name, goal = problem.target
        gap = z3.FreshReal("objective_gap")
        goal_v = z3.RealVal(str(Fraction(goal)))
        opt.add(gap >= xs[name] - goal_v, gap >= goal_v - xs[name])
        opt.minimize(gap)

    status = opt.check()
    duration_ms = (perf_counter() - started) * 1000
    if status != z3.sat:
        return Solution(
            "unsat" if status == z3.unsat else "unknown",
            solver=NAME,
            duration_ms=duration_ms,
            reason=opt.reason_unknown() if status == z3.unknown else "",
        )
    model = opt.model()
    assignment: dict[str, Fraction | int | float] = {}
    for variable in problem.variables:
        name, x = variable.name, xs[variable.name]
        value = model.eval(x, model_completion=True)
        if variable.kind == "bool" and (z3.is_true(value) or z3.is_false(value)):
            assignment[name] = z3.is_true(value)
        elif isinstance(value, z3.IntNumRef):
            assignment[name] = value.as_long()
        elif isinstance(value, z3.RatNumRef):
            assignment[name] = value.as_fraction()
        else:
            return Solution(
                "unknown",
                solver=NAME,
                duration_ms=duration_ms,
                reason=f"unsupported model value for {name}: {value}",
            )
    violations = tuple(check_assignment(problem, assignment))
    return Solution("sat", assignment, NAME, violations, (perf_counter() - started) * 1000)
