"""Z3 backend for the Problem IR (cahier des charges §15.1).

Z3 is not trusted: its model is converted to exact rationals and re-checked by
:func:`hypomnesis.ir.problem.check_assignment` before being returned.
"""

from __future__ import annotations

from fractions import Fraction

import z3

from hypomnesis.ir.problem import Problem, Solution, check_assignment

NAME = "z3"


def solve(problem: Problem) -> Solution:
    opt = z3.Optimize()
    xs = {v.name: z3.Real(v.name) for v in problem.variables}
    for v in problem.variables:
        x = xs[v.name]
        if v.lower is not None:
            opt.add(x >= z3.RealVal(str(Fraction(v.lower))))
        if v.upper is not None:
            opt.add(x <= z3.RealVal(str(Fraction(v.upper))))
        if v.choices:
            opt.add(z3.Or([x == z3.RealVal(str(Fraction(c))) for c in v.choices]))
    for c in problem.constraints:
        lhs = z3.Sum([z3.RealVal(str(Fraction(k))) * xs[name] for name, k in c.terms])
        rhs = z3.RealVal(str(Fraction(c.rhs)))
        opt.add({"<=": lhs <= rhs, ">=": lhs >= rhs, "==": lhs == rhs}[c.op])
    if problem.target is not None:
        name, goal = problem.target
        gap = z3.Real(f"__gap_{name}")
        goal_v = z3.RealVal(str(Fraction(goal)))
        opt.add(gap >= xs[name] - goal_v, gap >= goal_v - xs[name])
        opt.minimize(gap)

    status = opt.check()
    if status != z3.sat:
        return Solution("unsat" if status == z3.unsat else "unknown", solver=NAME)
    model = opt.model()
    assignment: dict[str, Fraction | int | float] = {}
    for name, x in xs.items():
        value = model.eval(x, model_completion=True)
        assignment[name] = Fraction(value.as_fraction())  # type: ignore[attr-defined]
    violations = tuple(check_assignment(problem, assignment))
    return Solution("sat", assignment, NAME, violations)
