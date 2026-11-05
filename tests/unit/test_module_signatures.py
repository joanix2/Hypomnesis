"""Module interfaces constrain the public type system, not the private representation."""

import pytest

from hypomnesis.certify import CERTIFICATE_SCHEMA_ID, load_definitions, session_certificate
from hypomnesis.cli import main
from hypomnesis.contracts.codec import TypeCodec, UnsupportedTypeError
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.language import LanguageError, load_language
from hypomnesis.language import ast as A
from hypomnesis.language.docs import declarations
from hypomnesis.language.errors import HypomnesisError, NameResolutionError, TypeCheckError
from hypomnesis.language.parser import parse_program
from hypomnesis.lsp.analysis import analyze
from hypomnesis.runtime.interpreter import Interpreter
from hypomnesis.session import Session

SIGNATURE = "module type S = sig val make : int -> t type t val read : t -> int end"
MODULE = " module M : S = struct type t = int let make x = x let read x = x let secret = true end "


def test_ast_preserves_signature_members_and_module_constraint():
    signature, module = parse_program(SIGNATURE + "\n" + MODULE).items
    assert isinstance(signature, A.ModuleTypeItem)
    assert [spec.name for spec in signature.specs] == ["make", "t", "read"]
    assert isinstance(signature.specs[1], A.TypeSpec)
    assert signature.specs[1].manifest is None
    assert module.signature == "S"
    assert parse_program("module M = struct end").items[0].signature is None


def test_opaque_module_has_only_its_public_interface():
    session = Session()
    result = session.load(SIGNATURE + "\n" + MODULE)
    assert {binding.name for binding in result.bindings} == {"make", "read"}
    assert len(result.types) == 1 and result.types[0].kind == "abstract"
    assert session.type_of("M.make") == "int -> M.t"
    assert session.type_of("M.read") == "M.t -> int"
    with pytest.raises(NameResolutionError, match="secret"):
        session.value("M.secret")
    session.load("let answer = M.read (M.make 42)")
    assert session.value("answer") == 42


@pytest.mark.parametrize(
    "body,message",
    [
        ("type t = int let make x = x", "missing value read"),
        ("let make x = x let read x = x", "must provide type t"),
        ("type 'a t = int let make x = x let read x = x", "arity 0"),
        ("type t = bool let make x = x + 1 let read x = 0", "Value make"),
    ],
)
def test_incompatible_structures_fail_at_the_module_header(body, message):
    session = Session()
    with pytest.raises(TypeCheckError, match=message) as caught:
        session.check(SIGNATURE + "\nmodule M : S = struct " + body + " end")
    assert caught.value.span.line == 2
    assert "M" not in session.checker.root.modules
    assert "S" not in session.checker.root.signatures


@pytest.mark.parametrize(
    "declaration,operation",
    [
        ("type t = C of int", "let broken = match M.make 42 with M.C x -> x"),
        ("type t = C of int", "let broken = match M.make 42 with C x -> x"),
        ("type t = {value : int}", "let broken = (M.make 42).value"),
        ("type t = {value : int}", "let broken = { M.value = 42 }"),
        ("type t = int", "let broken = M.make 42 + 1"),
        ("type t = int", "let broken : int = M.make 42"),
    ],
)
def test_abstract_representations_cannot_be_constructed_or_deconstructed(declaration, operation):
    make, read = {
        "type t = C of int": ("let make x = C x", "let read = function C x -> x"),
        "type t = {value : int}": ("let make x = {value = x}", "let read x = x.value"),
        "type t = int": ("let make x = x", "let read x = x"),
    }[declaration]
    session = Session()
    session.load(
        SIGNATURE + "\nmodule M : S = struct " + declaration + " " + make + " " + read + " end"
    )
    with pytest.raises(HypomnesisError):
        session.check(operation)
    session.load("let answer = M.read (M.make 42)")
    assert session.value("answer") == 42


def test_two_sealings_have_distinct_abstract_identities_even_with_the_same_representation():
    session = Session()
    session.load(SIGNATURE + MODULE + MODULE.replace("module M", "module N"))
    with pytest.raises(TypeCheckError):
        session.check("let broken = N.read (M.make 42)")
    session.load("open M\nlet answer = read (make 42)")
    assert session.value("answer") == 42


@pytest.mark.parametrize(
    "type_body,make,read,operation",
    [
        (
            "C of int",
            "fun x -> Base.C x",
            "function Base.C x -> x",
            "let broken = match M.make 42 with Base.C x -> x",
        ),
        (
            "{value : int}",
            "fun x -> {Base.value = x}",
            "fun x -> x.Base.value",
            "let broken = (M.make 42).Base.value",
        ),
    ],
)
def test_known_representation_members_do_not_bypass_the_abstract_identity(
    type_body, make, read, operation
):
    session = Session()
    session.load(
        "module Base = struct type t = "
        + type_body
        + " end "
        + SIGNATURE
        + " module M : S = struct type t = Base.t let make = "
        + make
        + " let read = "
        + read
        + " end"
    )
    with pytest.raises(TypeCheckError):
        session.check(operation)


def test_manifest_aliases_and_forward_references_preserve_public_equalities():
    session = Session()
    session.load(
        "module type S = sig val x : t type t = u type u = float end "
        "module M : S = struct type u = float type t = float let x = 2.5 end "
        "let answer : M.t = M.x +. 0.5"
    )
    assert session.value("answer") == 3.0
    assert session.type_of("M.x") == "float"
    assert TypeCodec(session.checker, "M.t").encode(3.0) == 3.0


def test_manifest_alias_constraints_cannot_be_ignored():
    with pytest.raises(TypeCheckError, match="Type t"):
        Session().check(
            "module type S = sig type t = float end module M : S = struct type t = int end"
        )


def test_manifest_alias_may_name_another_abstract_member():
    session = Session()
    session.load(
        "module type S = sig type u = t list val x : u type t end "
        "module M : S = struct type t = int type u = int list let x = [42] end"
    )
    assert session.type_of("M.x") == "M.t list"
    with pytest.raises(TypeCheckError):
        session.check("let broken : int list = M.x")


def test_parameterized_abstract_types_and_polymorphic_exports():
    session = Session()
    session.load(
        "module type Box = sig val make : 'a -> 'a t type 'a t "
        "val read : 'a t -> 'a end "
        "module B : Box = struct type 'a t = Box of 'a "
        "let make x = Box x let read = function Box x -> x end "
        "let answer = B.read (B.make 42) let truth = B.read (B.make true)"
    )
    assert session.value("answer") == 42 and session.value("truth") is True
    assert session.type_of("B.make") == "'a -> 'a B.t"


def test_polymorphic_implementation_can_be_specialized_and_certified():
    session = Session()
    session.load(
        "module type S = sig val id : int -> int end "
        "module M : S = struct let id x = x end let answer = M.id 42"
    )
    certificate = session_certificate(session)
    interpreter = Interpreter(session.natives)
    interpreter.execute(load_definitions(certificate))
    assert interpreter.globals["answer"] == 42
    with pytest.raises(TypeCheckError):
        session.check("let broken = M.id true")


def test_monomorphic_implementation_does_not_satisfy_a_polymorphic_contract():
    with pytest.raises(TypeCheckError, match="Value id"):
        Session().check(
            "module type S = sig val id : 'a -> 'a end module M : S = struct let id x = x + 1 end"
        )


def test_signatures_capture_lexical_types_instead_of_implementation_shadows():
    session = Session()
    session.check(
        "type t = int module type S = sig val x : t end "
        "module M : S = struct type t = bool let x = 42 end"
    )
    assert session.type_of("M.x") == "int"
    with pytest.raises(TypeCheckError):
        Session().check(
            "type t = int module type S = sig val x : t end "
            "module M : S = struct type t = bool let x = true end"
        )


@pytest.mark.parametrize(
    "specs,message",
    [
        ("type t type t", "duplicate type"),
        ("type ('a, 'a) t", "duplicate type"),
        ("val x : int val x : int", "duplicate value"),
        ("type t = u type u = t", "recursive signature alias"),
        ("type 'a t = 'b", "unbound type parameter"),
    ],
)
def test_invalid_signatures_are_explicit_errors(specs, message):
    with pytest.raises(TypeCheckError, match=message):
        Session().check("module type S = sig " + specs + " end")


def test_imported_signatures_and_aliases_share_sealed_type_identities(tmp_path):
    (tmp_path / "interfaces.hyp").write_text(SIGNATURE)
    (tmp_path / "units.hyp").write_text(
        "from interfaces import S as Contract\n" + MODULE.replace(": S", ": Contract")
    )
    session = Session()
    session.load(
        "import units as a\nimport units as b\nlet answer = b.M.read (a.M.make 42)",
        filename=str(tmp_path / "main.hyp"),
    )
    assert session.value("answer") == 42
    assert session.type_of("a.M.make") == "int -> a.M.t"
    assert session.checker.lookup_type("a.M.t") is session.checker.lookup_type("b.M.t")


def test_namespaced_signatures_and_open_are_supported():
    session = Session()
    session.load(
        "module Interfaces = struct "
        + SIGNATURE
        + " end "
        + MODULE.replace(": S", ": Interfaces.S")
        + " open Interfaces "
        + MODULE.replace("module M", "module N")
        + " let answer = N.read (N.make 42)"
    )
    assert session.value("answer") == 42


def test_failed_seal_rolls_back_without_corrupting_an_existing_opaque_module():
    session = Session()
    session.load(SIGNATURE + MODULE)
    original = session.checker.lookup_type("M.t")
    count = len(session.definitions)
    with pytest.raises(TypeCheckError):
        session.check("module M : S = struct type t = bool end")
    assert session.checker.lookup_type("M.t") is original
    assert len(session.definitions) == count
    session.load("let answer = M.read (M.make 42)")
    assert session.value("answer") == 42


def test_opaque_json_contracts_are_explicitly_refused():
    session = Session()
    session.check(SIGNATURE + MODULE)
    with pytest.raises(UnsupportedTypeError, match="no data representation"):
        TypeCodec(session.checker, "M.t")
    session.check("type box = {value : M.t}")
    with pytest.raises(UnsupportedTypeError, match="no data representation"):
        TypeCodec(session.checker, "box")


def test_lsp_checks_unsaved_imported_signature_without_evaluation(tmp_path):
    interface = tmp_path / "interfaces.hyp"
    interface.write_text(SIGNATURE)
    path = tmp_path / "main.hyp"
    source = "from interfaces import S\n" + MODULE.replace("let secret = true", "let z = 1 / 0")
    assert analyze(path, source, tmp_path, None, {}) == []
    errors = analyze(
        path, source, tmp_path, None, {str(interface): SIGNATURE.replace("int -> t", "bool -> t")}
    )
    assert len(errors) == 1 and "Value make" in errors[0].message
    assert errors[0].range.start.line == 1


def test_cli_static_check_does_not_publish_hidden_bindings(tmp_path, capsys):
    path = tmp_path / "main.hyp"
    path.write_text(SIGNATURE + MODULE)
    assert main(["check", str(path)]) == 0
    output = capsys.readouterr().out
    assert "secret" not in output
    assert "M.t" in output


def test_public_documentation_does_not_expose_a_hidden_representation(tmp_path):
    path = tmp_path / "langage.hyp"
    source = (
        'language example = struct let version = "1" end\n'
        "(** Interface. *)\n" + SIGNATURE + "\n(** Module. *)\nmodule M : S = struct\n"
        "(** Valeur abstraite. *)\ntype t = Secret of int\n"
        "(** Construction. *)\nlet make x = Secret x\n"
        "(** Lecture. *)\nlet read = function Secret x -> x\n"
        "let secret = false\nend"
    )
    path.write_text(source)
    language = load_language(tmp_path, execute=False)
    found = declarations(source, namespace=language.session.checker.root)
    assert {d.path for d in found} == {"S", "M", "M.t", "M.make", "M.read"}
    assert all("secret" not in d.path.lower() for d in found)
    certificate = session_certificate(language.session)
    assert all(t["kind"] != "abstract" for t in certificate["types"])
    SchemaRegistry.with_builtin_schemas().validate(CERTIFICATE_SCHEMA_ID, certificate)


def test_language_layers_reject_conflicting_signature_exports(tmp_path):
    for name in ("a", "b"):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "langage.hyp").write_text(
            f'language {name} = struct let version = "1" end\nmodule type S = sig end'
        )
    root = tmp_path / "root"
    root.mkdir()
    (root / "langage.hyp").write_text(
        'language root = struct let version = "1" let imports = ["../a"; "../b"] end'
    )
    with pytest.raises(LanguageError, match=r"collision.*S.*signatures"):
        load_language(root, strict=False, execute=False)
