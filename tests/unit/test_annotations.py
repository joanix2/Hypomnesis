"""Annotations de types de la Core IR élaborée (HYP-024)."""

from pathlib import Path

import pytest

from hypomnesis.ir import core as ir
from hypomnesis.language.parser import parse_program
from hypomnesis.language.typesystem.annotations import annotation_problems, free_variables
from hypomnesis.language.typesystem.infer import Checker
from hypomnesis.language.typesystem.types import TypePrinter
from hypomnesis.runtime.natives import default_registry
from hypomnesis.session import prelude_source

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
# Ordre de chargement : plate.hyp utilise les modules de units.hyp.
EXAMPLE_FILES = [
    EXAMPLES / "basics" / "tour.hyp",
    EXAMPLES / "mechanics" / "units.hyp",
    EXAMPLES / "mechanics" / "plate.hyp",
]


@pytest.fixture(scope="module")
def checker() -> Checker:
    c = Checker(default_registry().arities())
    c.check_program(parse_program(prelude_source()))
    return c


def elaborate(checker: Checker, source: str) -> list[ir.Definition]:
    return checker.check_program(parse_program(source)).definitions


def show(t) -> str:
    return TypePrinter().show(t)


def nodes(e: object, kind: type) -> list:
    """Tous les nœuds de type ``kind`` sous ``e`` (parcours générique des dataclasses)."""
    found = []

    def go(x: object) -> None:
        if isinstance(x, kind):
            found.append(x)
        if isinstance(x, tuple):
            for item in x:
                go(item)
        elif hasattr(x, "__dataclass_fields__"):
            for name in x.__dataclass_fields__:
                go(getattr(x, name))

    go(e)
    return found


def test_prelude_and_examples_are_fully_annotated():
    c = Checker(default_registry().arities())
    sources = [prelude_source()] + [p.read_text() for p in EXAMPLE_FILES]
    for source in sources:
        assert annotation_problems(c.check_program(parse_program(source)).definitions) == []


def test_lambda_parameters_carry_their_types(checker):
    (d,) = elaborate(checker, "let add (x : int) y = x + y")
    assert isinstance(d, ir.DefValue) and isinstance(d.expr, ir.Lambda)
    assert [show(t) for t in d.expr.param_types] == ["int", "int"]


def test_polymorphic_definition_is_quantified(checker):
    (d,) = elaborate(checker, "let id x = x")
    assert isinstance(d, ir.DefValue) and isinstance(d.expr, ir.Lambda)
    (param,) = d.expr.param_types
    assert [v.id for v in free_variables(param)] == [v.id for v in d.forall_vars]


def test_global_instantiation_is_explicit(checker):
    (d,) = elaborate(checker, "let n = List.length [1; 2]")
    assert isinstance(d, ir.DefValue)
    length = next(g for g in nodes(d.expr, ir.Global) if g.qname == "List.length")
    assert [show(t) for t in length.type_args] == ["int"]
    nil = next(c for c in nodes(d.expr, ir.Construct) if c.tag == "[]")
    assert [show(t) for t in nil.type_args] == ["int"]


def test_local_let_polymorphism(checker):
    (d,) = elaborate(checker, "let p = let f x = x in (f 1, f true)")
    assert isinstance(d, ir.DefValue)
    (let,) = nodes(d.expr, ir.Let)
    assert len(let.forall_vars) == 1
    uses = [
        show(t) for local in nodes(d.expr, ir.Local) if local.name == "f" for t in local.type_args
    ]
    assert sorted(uses) == ["bool", "int"]
    assert annotation_problems([d]) == []


def test_let_rec_records_types_and_quantifiers(checker):
    (d,) = elaborate(checker, "let rec len l = match l with [] -> 0 | _ :: t -> 1 + len t")
    assert isinstance(d, ir.DefRec)
    assert [show(t) for t in d.types] == ["'a list -> int"]
    assert [len(vs) for vs in d.foralls] == [1]


def test_and_bindings_through_temporaries_stay_closed(checker):
    (d,) = elaborate(checker, "let r = let f x = x and g = 1 in (f g, f true)")
    assert annotation_problems([d]) == []


def test_unconstrained_variables_default_to_unit(checker):
    (d,) = elaborate(checker, "let x = (fun _ -> 1) []")
    assert isinstance(d, ir.DefValue)
    nil = next(c for c in nodes(d.expr, ir.Construct) if c.tag == "[]")
    assert [show(t) for t in nil.type_args] == ["unit"]
    assert d.forall_vars == ()


def test_record_and_constructor_type_arguments(checker):
    (d,) = elaborate(checker, "type 'a box = { content : 'a }\nlet b = { content = Some 1 }")
    assert isinstance(d, ir.DefValue)
    (record,) = nodes(d.expr, ir.Record)
    assert [show(t) for t in record.type_args] == ["int option"]


def test_annotations_do_not_affect_equality():
    with_types = ir.Lambda(("x",), ir.Local("x"), param_types=())
    assert with_types == ir.Lambda(("x",), ir.Local("x"))
