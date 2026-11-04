"""Closed, type-directed source terms; no rejection by the type checker."""

from dataclasses import dataclass

from hypothesis import strategies as st

TYPES = {
    "int": "int",
    "bool": "bool",
    "string": "string",
    "pair": "int * bool",
    "list": "int list",
    "option": "int option",
    "record": "cell",
}


def float_literal(value):
    return f"(-.{abs(value)!r})" if value < 0 else repr(value)


@dataclass(frozen=True)
class Term:
    kind: str
    source: str


@st.composite
def terms(draw, kind=None, depth=3, context=()):
    kind = kind or draw(st.sampled_from(tuple(TYPES)))
    name = f"v{depth}"

    def child(target=kind, *, scope=context):
        return draw(terms(target, max(0, depth - 1), scope)).source

    choices = ["base"]
    if any(t == kind for t, _ in context):
        choices.append("variable")
    if depth:
        choices += ["if", "let", "apply", "match", "rec"]
        if kind == "int":
            choices += ["arithmetic", "field", "guard", "alternatives"]
        elif kind == "bool":
            choices += ["compare", "float"]
        elif kind == "string":
            choices += ["concat"]
        elif kind == "record":
            choices += ["update"]
    form = draw(st.sampled_from(choices))
    if form == "variable":
        source = draw(st.sampled_from([n for t, n in context if t == kind]))
    elif form == "if":
        source = f"(if {child('bool')} then {child()} else {child()})"
    elif form in ("let", "apply"):
        argument = draw(st.sampled_from(tuple(TYPES)))
        value = child(argument)
        body = child(scope=(*context, (argument, name)))
        if form == "let":
            source = f"(let {name} : {TYPES[argument]} = {value} in {body})"
        else:
            source = f"((fun ({name} : {TYPES[argument]}) -> {body}) {value})"
    elif form == "match":
        option = child("option")
        yes = child(scope=(*context, ("int", name)))
        source = f"(match {option} with None -> {child()} | Some {name} -> {yes})"
    elif form == "rec":
        steps = draw(st.integers(0, 6))
        source = (
            f"(let rec go{depth} (n : int) : {TYPES[kind]} = if n <= 0 then {child()} "
            f"else go{depth} (n - 1) in go{depth} {steps})"
        )
    elif form == "arithmetic":
        op = draw(st.sampled_from(["+", "-", "*", "/", "mod"]))
        source = f"({child()} {op} {child()})"
    elif form == "field":
        source = f"({child('record')}).count"
    elif form == "guard":
        source = f"(match {child('int')} with {name} when false -> 999983 | _ -> {child()})"
    elif form == "alternatives":
        source = (
            f"(match ({child('int')}, {child('int')}) with "
            f"| ({name}, _) | (_, {name}) when {name} < 0 -> {name} | _ -> {child()})"
        )
    elif form == "compare":
        target = draw(st.sampled_from(["int", "string"]))
        op = draw(st.sampled_from(["=", "<>", "<", "<=", ">", ">="]))
        source = f"({child(target)} {op} {child(target)})"
    elif form == "float":
        left, right = draw(st.tuples(st.integers(-32, 32), st.integers(-32, 32)))
        op = draw(st.sampled_from(["=", "<>", "<", "<=", ">", ">="]))
        # Binary fractions include signed zero, NaN and infinity through division.
        other = draw(st.integers(-32, 32)) / 2
        source = (
            f"(({float_literal(left / 2)} /. {float_literal(right / 2)}) "
            f"{op} {float_literal(other)})"
        )
    elif form == "concat":
        source = f"({child()} ^ {child()})"
    elif form == "update":
        source = f"{{ {child('record')} with count = {child('int')} }}"
    elif kind == "int":
        source = f"({draw(st.integers(-(2**80), 2**80))})"
    elif kind == "bool":
        source = "true" if draw(st.booleans()) else "false"
    elif kind == "string":
        text = draw(st.text(alphabet="abc XYZéλ☀", max_size=12))
        source = f'"{text}"'
    elif kind == "pair":
        source = f"({child('int')}, {child('bool')})"
    elif kind == "list":
        source = "[" + "; ".join(child("int") for _ in range(draw(st.integers(0, 3)))) + "]"
    elif kind == "option":
        source = f"(Some {child('int')})" if draw(st.booleans()) else "(None : int option)"
    else:
        assert kind == "record"
        source = f"{{ count = {child('int')}; flag = {child('bool')} }}"
    return Term(kind, source)
