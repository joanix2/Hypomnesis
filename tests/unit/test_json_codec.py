"""Reversible typed contracts, including the actual JSON text boundary."""

import json
import math
import sys

import pytest
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from hypomnesis.contracts.codec import CodecError, TypeCodec, UnsupportedTypeError
from hypomnesis.engine.bridge import BridgeError, to_json
from hypomnesis.engine.procedure import json_to_python, python_to_json
from hypomnesis.language.errors import EvaluationError
from hypomnesis.language.typesystem.types import INT, TCon, TVar
from hypomnesis.runtime.json import data_to_json, json_to_data
from hypomnesis.runtime.natives import to_json_value
from hypomnesis.runtime.values import NIL, RecordValue, Variant, from_iterable
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def session():
    s = Session()
    s.load("""
module Model = struct
  type 'a box = { value : 'a; ok : bool }
  type 'a choice = Empty | Chosen of 'a
  type 'a tree = Leaf | Branch of 'a * 'a tree list
end
type integer_box = int Model.box
type 'a growing = Stop | Grow of ('a list) growing
""")
    return s


SCALAR_CASES = st.one_of(
    st.integers().map(lambda v: ("int", v)),
    st.floats(allow_nan=False, allow_infinity=False).map(lambda v: ("float", v)),
    st.text().map(lambda v: ("string", v)),
    st.booleans().map(lambda v: ("bool", v)),
    st.just(("unit", ())),
)


def compound(children):
    return st.one_of(
        children.map(lambda c: (f"({c[0]}) option", Variant("Some", c[1], 1))),
        children.map(lambda c: (f"({c[0]}) option", Variant("None"))),
        children.map(lambda c: (f"({c[0]}) list", from_iterable([c[1], c[1]]))),
        st.tuples(children, children).map(
            lambda cs: (f"({cs[0][0]}) * ({cs[1][0]})", (cs[0][1], cs[1][1]))
        ),
        children.map(
            lambda c: (
                f"({c[0]}) Model.box",
                RecordValue("Model.box", (("value", c[1]), ("ok", True))),
            )
        ),
        children.map(lambda c: (f"({c[0]}) Model.choice", Variant("Chosen", c[1], 1))),
    )


CASES = st.recursive(SCALAR_CASES, compound, max_leaves=12)


@given(CASES)
def test_typed_roundtrip_through_json_and_all_bridges(session, case):
    signature, value = case
    codec = TypeCodec(session.checker, signature)
    encoded = codec.encode(value)
    wire = json.loads(json.dumps(encoded, allow_nan=False))
    Draft202012Validator(codec.schema).validate(wire)
    assert codec.decode(wire) == value
    assert to_json(value) == encoded
    assert json_to_python(to_json_value(value)) == encoded
    assert json_to_python(python_to_json(wire)) == wire


TREE = st.recursive(
    st.just(Variant("Leaf")),
    lambda children: st.tuples(st.integers(), st.lists(children, max_size=3)).map(
        lambda pair: Variant("Branch", (pair[0], from_iterable(pair[1])), 1)
    ),
    max_leaves=10,
)


@given(TREE)
def test_regular_recursive_instantiation(session, tree):
    codec = TypeCodec(session.checker, "int Model.tree")
    wire = json.loads(json.dumps(codec.encode(tree)))
    assert codec.decode(wire) == tree
    assert len(codec.schema["$defs"]) == 1


@pytest.mark.parametrize(
    "signature, expression, expected",
    [
        ("unit option", "None", {"tag": "None"}),
        ("unit option", "Some ()", {"tag": "Some", "arg": None}),
        ("int option option", "Some None", {"tag": "Some", "arg": {"tag": "None"}}),
        ("int option option", "Some (Some 2)", {"tag": "Some", "arg": {"tag": "Some", "arg": 2}}),
        (
            "(int Model.box) Model.box",
            "{ Model.value = { Model.value = 2; ok = true }; ok = false }",
            {"value": {"value": 2, "ok": True}, "ok": False},
        ),
        ("integer_box", "{ Model.value = 2; ok = true }", {"value": 2, "ok": True}),
    ],
)
def test_options_nested_declarations_and_aliases(session, signature, expression, expected):
    value = session.eval(expression).value
    codec = TypeCodec(session.checker, signature)
    assert codec.encode(value) == expected
    assert codec.decode(expected) == value


@pytest.mark.parametrize("signature", ["'a", "int -> int", "missing", "int growing"])
def test_unsupported_types_are_explicit(session, signature):
    with pytest.raises(UnsupportedTypeError):
        TypeCodec(session.checker, signature)


def test_bound_type_variables_do_not_compress_or_mutate(session):
    first, second = TVar(3), TVar(4)
    first.ref, second.ref = second, INT
    codec = TypeCodec(session.checker, first)
    assert codec.encode(2) == 2
    assert first.ref is second
    schema = codec.schema
    schema["type"] = "string"
    assert codec.schema["type"] == "integer"


@pytest.mark.parametrize(
    "signature, value",
    [
        ("int", True),
        ("float", True),
        ("float", 1),
        ("unit", None),
        ("int * bool", (1,)),
        ("int list", Variant("::", (1, Variant("bad")))),
        ("int list", Variant("[]", 1)),
        ("int Model.choice", Variant("Unknown")),
        ("int Model.choice", Variant("Empty", 2)),
        ("int Model.box", RecordValue("other", (("value", 1), ("ok", True)))),
        ("int Model.box", RecordValue("Model.box", (("value", 1),))),
    ],
)
def test_bad_runtime_values_refused(session, signature, value):
    with pytest.raises(CodecError):
        TypeCodec(session.checker, signature).encode(value)


@pytest.mark.parametrize(
    "signature, value",
    [
        ("int", True),
        ("int", 1.5),
        ("bool", 1),
        ("int * bool", [1]),
        ("int list", (1,)),
        ("int Model.choice", {"tag": "Unknown"}),
        ("int Model.choice", {"tag": "Empty", "arg": None}),
        ("int Model.choice", {"tag": "Chosen"}),
        ("int Model.box", {"value": 1}),
        ("int Model.box", {"value": 1, "ok": True, "extra": 0}),
        ("unit option", None),
        ("float", 10**400),
    ],
)
def test_bad_json_values_refused(session, signature, value):
    with pytest.raises(CodecError):
        TypeCodec(session.checker, signature).decode(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_numbers_rejected_by_all_boundaries(session, value):
    codec = TypeCodec(session.checker, "float")
    for action in (codec.encode, codec.decode):
        with pytest.raises(CodecError):
            action(value)
    for action in (to_json_value, python_to_json):
        with pytest.raises(EvaluationError):
            action(value)
    with pytest.raises(BridgeError):
        to_json(value)


@pytest.mark.parametrize("integer", [2**53 + 1, -(2**100 + 1), 10**300])
def test_exact_integers_in_prelude_and_wire(session, integer):
    result = session.eval(f"to_json ({integer})").value
    assert result == Variant("Int", integer, 6)
    assert json_to_python(result) == integer
    assert session.eval(f"Json.int (to_json ({integer}))").value == Variant("Some", integer, 1)
    assert (
        TypeCodec(session.checker, "int").decode(json.loads(json.dumps(json_to_python(result))))
        == integer
    )


def test_float_type_and_negative_zero_preserved(session):
    for value in (1.0, -0.0, sys.float_info.max):
        codec = TypeCodec(session.checker, "float")
        restored = codec.decode(json.loads(json.dumps(codec.encode(value))))
        assert type(restored) is float
        assert math.copysign(1, restored) == math.copysign(1, value)
        assert type(json_to_python(python_to_json(value))) is float


def test_malformed_raw_json_and_lists_are_not_coerced():
    for value in ({1: "not a string key"}, (), object()):
        with pytest.raises(EvaluationError):
            data_to_json(value)
    for value in (Variant("Num", 1), Variant("Int", 1.0), Variant("Arr", Variant("bad"))):
        with pytest.raises(EvaluationError):
            json_to_data(value)
    with pytest.raises(EvaluationError, match="duplicate"):
        json_to_data(
            Variant(
                "Obj",
                from_iterable(
                    [
                        ("x", Variant("Int", 1)),
                        ("x", Variant("Int", 2)),
                    ]
                ),
            )
        )
    assert json_to_data(Variant("Arr", NIL)) == []


def test_type_arity_is_checked_even_for_direct_type_objects(session):
    with pytest.raises(UnsupportedTypeError):
        TypeCodec(session.checker, TCon("int", (INT,)))


def test_json_schema_integer_includes_integral_number_tokens(session):
    codec = TypeCodec(session.checker, "int")
    assert type(codec.decode(1.0)) is int
    assert codec.decode(-0.0) == 0


@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.text(),
            st.floats(allow_nan=False, allow_infinity=False),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=3), st.dictionaries(st.text(), children, max_size=3)
        ),
        max_leaves=8,
    )
)
def test_json_algebra_type_is_itself_reversible(session, data):
    codec = TypeCodec(session.checker, "Json.t")
    value = data_to_json(data)
    encoded = codec.encode(value)
    assert codec.decode(json.loads(json.dumps(encoded, allow_nan=False))) == value
    assert json_to_data(value) == data
