import pytest

from hypomnesis.language import ast as A
from hypomnesis.language.errors import ParseError
from hypomnesis.language.parser import parse_expression, parse_program


def test_operator_precedence():
    e = parse_expression("1 + 2 * 3 :: []")
    assert isinstance(e, A.Cons)
    assert e.head == A.BinOp(
        "+", A.Literal(1, "int"), A.BinOp("*", A.Literal(2, "int"), A.Literal(3, "int"))
    )


def test_application_binds_tighter_than_operators():
    e = parse_expression("f x + g y")
    assert e == A.BinOp("+", A.Apply(A.Var("f"), A.Var("x")), A.Apply(A.Var("g"), A.Var("y")))


def test_pipe_is_left_associative():
    e = parse_expression("x |> f |> g")
    assert e == A.BinOp("|>", A.BinOp("|>", A.Var("x"), A.Var("f")), A.Var("g"))


def test_qualified_names_and_field_access():
    e = parse_expression("Length.multiply p.width p.height")
    assert e == A.Apply(
        A.Apply(A.Var("Length.multiply"), A.Field(A.Var("p"), "width")),
        A.Field(A.Var("p"), "height"),
    )


def test_nested_match_absorbs_following_arms():
    e = parse_expression("match a with A -> match b with B -> 1 | C -> 2")
    assert isinstance(e, A.Match) and len(e.arms) == 1
    inner = e.arms[0].body
    assert isinstance(inner, A.Match) and len(inner.arms) == 2


def test_type_declarations():
    program = parse_program(
        "type ('a, 'b) pair = { left : 'a; right : 'b }\n"
        "type 'a tree = Leaf | Node of 'a tree * 'a * 'a tree\n"
        "type meters = float"
    )
    record, variant, alias = (item.defs[0] for item in program.items)
    assert record.params == ("'a", "'b") and isinstance(record.rhs, A.RecordRhs)
    assert [name for name, _ in variant.rhs.ctors] == ["Leaf", "Node"]
    assert alias.rhs == A.AliasRhs(A.TECon("float"))


def test_comments_and_numeric_literals():
    program = parse_program("(* a comment *) let x = 1_000 let y = 2.5e3")
    assert program.items[0].bindings[0].body == A.Literal(1000, "int")
    assert program.items[1].bindings[0].body == A.Literal(2500.0, "float")


def test_record_punning_in_patterns():
    e = parse_expression("fun { width; height = h } -> width")
    assert e.params[0] == A.PRecord((("width", A.PVar("width")), ("height", A.PVar("h"))))


def test_syntax_error_has_position():
    with pytest.raises(ParseError) as info:
        parse_program("let x = (1 + ")
    assert info.value.span is not None
    assert info.value.span.line == 1
