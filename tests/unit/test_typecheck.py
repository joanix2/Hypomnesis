import pytest

from hypomnesis.language.errors import NameResolutionError, TypeCheckError
from hypomnesis.session import Session


def sig(source: str, name: str) -> str:
    session = Session()
    session.check(source)
    return session.type_of(name)


@pytest.mark.parametrize(
    ("source", "name", "expected"),
    [
        ("let id x = x", "id", "'a -> 'a"),
        ("let k x y = x", "k", "'a -> 'b -> 'a"),
        ("let compose f g x = f (g x)", "compose", "('a -> 'b) -> ('c -> 'a) -> 'c -> 'b"),
        ("let rec len l = match l with [] -> 0 | _ :: t -> 1 + len t", "len", "'a list -> int"),
        ('let pair = (1, "a", true)', "pair", "int * string * bool"),
        ("let f o = match o with Some x -> x | None -> 0", "f", "int option -> int"),
        ("let apply f = f 1 +. 2.0", "apply", "(int -> float) -> float"),
        ("type 'a box = { content : 'a }\nlet open_box b = b.content", "open_box", "'a box -> 'a"),
        ("let swap (a, b) = (b, a)", "swap", "'a * 'b -> 'b * 'a"),
        ("let m = List.map", "m", "('a -> 'b) -> 'a list -> 'b list"),
        ("let f = function [] -> None | x :: _ -> Some x", "f", "'a list -> 'a option"),
    ],
)
def test_inferred_signatures(source, name, expected):
    assert sig(source, name) == expected


def test_let_polymorphism():
    source = 'let pair = let id x = x in (id 1, id "s")'
    assert sig(source, "pair") == "int * string"


def test_lambda_bound_variables_are_monomorphic():
    with pytest.raises(TypeCheckError):
        Session().check('let f = fun id -> (id 1, id "s")')


def test_mutual_recursion():
    source = (
        "let rec even n = if n = 0 then true else odd (n - 1)\n"
        "and odd n = if n = 0 then false else even (n - 1)"
    )
    assert sig(source, "odd") == "int -> bool"


def test_occurs_check():
    with pytest.raises(TypeCheckError, match="infinite"):
        Session().check("let f x = x x")


@pytest.mark.parametrize(
    "source",
    [
        "let x = 1 + 1.0",
        "let x = if 1 then 2 else 3",
        'let x = if true then 1 else "a"',
        'let x = [1; "a"]',
        "let f x = x.width",
        "type r = { a : int }\nlet x = { a = 1; b = 2 }",
        "type r = { a : int; b : int }\nlet x = { a = 1 }",
        "let x = None 1",
        "let x = 1 2",
        "let f (x, x) = x",
        "let rec x = 1",
    ],
)
def test_ill_typed_programs_are_rejected(source):
    with pytest.raises((TypeCheckError, NameResolutionError)):
        Session().check(source)


def test_constructor_used_as_function():
    assert sig("let f = Some", "f") == "'a -> 'a option"


def test_unbound_names():
    with pytest.raises(NameResolutionError, match="unbound value nope"):
        Session().check("let x = nope")
    with pytest.raises(NameResolutionError, match="unbound module Nope"):
        Session().check("let x = Nope.f")


def test_type_annotations_constrain():
    assert sig("let f (x : int) = x", "f") == "int -> int"
    assert sig("let f x : float = x", "f") == "float -> float"
    with pytest.raises(TypeCheckError):
        Session().check("let f (x : int) : string = x")


def test_modules_and_open():
    session = Session()
    session.check(
        "module Geometry = struct\n"
        "  type point = { x : float; y : float }\n"
        "  let origin = { x = 0.0; y = 0.0 }\n"
        "  module Inner = struct let norm p = p.x *. p.x +. p.y *. p.y end\n"
        "end\n"
        "open Geometry\n"
        "let d = Inner.norm origin\n"
        "let e = Geometry.Inner.norm { x = 1.0; y = 2.0 }"
    )
    assert session.type_of("d") == "float"
    assert session.type_of("Geometry.Inner.norm") == "Geometry.point -> float"


def test_field_resolution_uses_known_type():
    source = (
        "type a = { name : string; size : int }\n"
        "type b = { name : string; weight : float }\n"
        "let size_of (x : a) = x.name"
    )
    assert sig(source, "size_of") == "a -> string"


def test_failed_phrase_leaves_environment_unchanged():
    session = Session()
    session.load("let x = 1")
    with pytest.raises(TypeCheckError):
        session.load('let y = 2\nlet x = x + "bad"')
    with pytest.raises(NameResolutionError):
        session.check("let z = y")
    assert session.type_of("x") == "int"


def test_unknown_native_symbol_is_rejected():
    with pytest.raises(NameResolutionError, match="unknown native symbol"):
        Session().check('external evil : string -> unit = "os.system"')


def test_native_arity_must_match_declared_type():
    with pytest.raises(TypeCheckError, match="takes 2 argument"):
        Session().check('external add : int -> int = "int.add"')
