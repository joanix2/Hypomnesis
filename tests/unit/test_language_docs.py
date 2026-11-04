"""Descriptions obligatoires dans un langage M2 (HYP-137, ADR 0009)."""

import json
import shutil
from pathlib import Path

import pytest

from hypomnesis.certify import session_certificate
from hypomnesis.engine.language import MissingDescriptionError, load_language
from hypomnesis.language.docs import declarations, missing_descriptions
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.language.parser import lex
from hypomnesis.runtime.values import show
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = ROOT / "demo" / "languages"
LANGUAGE_SOURCES = [
    LANGUAGES / "mecanique" / "plaque.hyp",
    LANGUAGES / "ventilation" / "ventilation.hyp",
]
EXAMPLES = ROOT / "demo" / "examples"
# Sets of files loaded together (a file may use the previous one).
SOURCE_SETS = {
    "plaque": [LANGUAGE_SOURCES[0]],
    "ventilation": [LANGUAGE_SOURCES[1]],
    "tour": [EXAMPLES / "basics" / "tour.hyp"],
    "certifiable": [EXAMPLES / "basics" / "certifiable.hyp"],
    "units+plate": [EXAMPLES / "mechanics" / "units.hyp", EXAMPLES / "mechanics" / "plate.hyp"],
}


def is_doc(token) -> bool:
    text = str(token)
    return token.type == "COMMENT" and text.startswith("(**") and not text.startswith("(**)")


def strip_docs(source: str) -> str:
    """The source without its ``(** … *)`` comments (found by lexing, like the engine does)."""
    out, last = [], 0
    for token in lex(source):
        if is_doc(token):
            out.append(source[last : token.start_pos])
            last = token.end_pos
    return "".join(out) + source[last:]


def copy_language(tmp_path: Path, name: str) -> Path:
    shutil.copytree(LANGUAGES / name, tmp_path / name)
    return tmp_path / name


def edit_source(root: Path, old: str, new: str) -> None:
    source = next(path for path in root.glob("*.hyp") if path.name != "langage.hyp")
    text = source.read_text(encoding="utf-8")
    assert old in text
    source.write_text(text.replace(old, new, 1), encoding="utf-8")


# ----------------------------------------------------------------- the compile-time rule


def test_the_shipped_languages_are_fully_described():
    for path in LANGUAGE_SOURCES:
        assert missing_descriptions(path.read_text(encoding="utf-8")) == []
        load_language(path.parent)


def test_removing_a_field_description_names_the_field_at_its_position(tmp_path):
    root = copy_language(tmp_path, "mecanique")
    edit_source(root, "    (** Largeur de la plaque.", "    (* Largeur de la plaque.")
    source = (root / "plaque.hyp").read_text(encoding="utf-8")
    with pytest.raises(MissingDescriptionError) as raised:
        load_language(root)
    error = raised.value
    assert isinstance(error, HypomnesisError)
    assert error.declaration.path == "Plaque.demande.largeur"
    assert "field Plaque.demande.largeur" in error.message
    line = next(i for i, text in enumerate(source.splitlines(), 1) if "largeur : float;" in text)
    assert (error.span.line, error.span.column) == (line, 5)
    assert str(error).startswith(f"{root / 'plaque.hyp'}:{line}:5: ")
    assert "^^^^^^^" in error.render(source)  # the field name is underlined


def test_removing_a_value_description_names_the_value(tmp_path):
    root = copy_language(tmp_path, "ventilation")
    edit_source(root, "(** Régule la température", "(* Régule la température")
    with pytest.raises(MissingDescriptionError) as raised:
        load_language(root)
    assert raised.value.declaration.kind == "value"
    assert raised.value.declaration.path == "Ventilation.reguler"


def test_an_undescribed_language_loads_when_not_strict(tmp_path):
    root = copy_language(tmp_path, "ventilation")
    source = root / "ventilation.hyp"
    source.write_text(strip_docs(source.read_text(encoding="utf-8")), encoding="utf-8")
    with pytest.raises(MissingDescriptionError):
        load_language(root)
    assert load_language(root, strict=False).name == "ventilation"


def test_m1_programs_need_no_description():
    session = load_language(LANGUAGES / "ventilation").session
    result = session.check(
        'let installation = { Ventilation.capteur = "t"; ventilateur = "f"; budget = 1 }'
    )
    assert [b.name for b in result.bindings] == ["installation"]


TOY = """\
(** Toy module. *)
module M = struct
  (** A shape. *)
  type shape =
    (** A point. *)
    | Point
    | Disc of float

  (** A record. *)
  type r = {
    (** Described. *)
    a : int;
    b : int;
    _c : int;
  }

  let _helper = 1
  let public_value = 2
end
"""


def test_every_kind_of_public_declaration_is_checked():
    missing = [(d.kind, d.path) for d in missing_descriptions(TOY)]
    assert missing == [
        ("constructor", "M.shape.Disc"),
        ("field", "M.r.b"),
        ("value", "M.public_value"),
    ]


def test_underscore_names_and_their_members_need_no_description():
    source = "(** M. *)\nmodule M = struct\n  type _t = { x : int }\n  let _y = 1\nend\n"
    assert missing_descriptions(source) == []


def test_interne_declarations_are_described_but_their_members_are_exempt():
    source = (
        "(** M. *)\nmodule M = struct\n"
        "  (** Helper type.\n      @interne *)\n  type t = { x : int; y : int }\n"
        "  (** Helper.\n      @interne *)\n  let v = 1\n"
        "  type u = { z : int }\nend\n"
    )
    assert [d.path for d in missing_descriptions(source)] == ["M.u", "M.u.z"]


def test_declarations_carry_their_position():
    found = {d.path: d for d in declarations(TOY)}
    assert (found["M"].span.line, found["M"].span.column) == (2, 1)
    assert (found["M.shape"].span.line, found["M.shape"].span.column) == (4, 3)
    assert (found["M.shape.Disc"].span.line, found["M.shape.Disc"].span.column) == (7, 7)
    assert found["M.shape.Point"].doc.summary == "A point."
    assert (found["M.r.b"].span.line, found["M.r.b"].span.column) == (13, 5)


# -------------------------------------------------- comments are found by lexing, not by regex

TRICKY = """\
(** Documented. *)
let documented = "(** not a description *)"
(* an ordinary comment mentioning (** a description *)
let plain = 1
"""


def test_a_doc_marker_inside_a_string_or_a_comment_is_not_a_description():
    found = {d.path: d for d in declarations(TRICKY)}
    assert found["documented"].doc.summary == "Documented."
    assert found["plain"].doc is None


def test_a_doc_comment_followed_by_an_ordinary_comment_is_detached():
    found = {d.path: d for d in declarations("(** Lost. *)\n(* ordinary *)\nlet a = 1\n")}
    assert found["a"].doc is None


# --------------------------------------------------------------- descriptions have no effect


@pytest.mark.parametrize("name", SOURCE_SETS)
def test_descriptions_change_neither_the_core_ir_nor_the_certificate(name):
    with_docs, without = Session(), Session()
    for path in SOURCE_SETS[name]:
        source = path.read_text(encoding="utf-8")
        with_docs.check(source)
        without.check(strip_docs(source))
    assert with_docs.definitions == without.definitions
    assert json.dumps(session_certificate(with_docs), sort_keys=True) == json.dumps(
        session_certificate(without), sort_keys=True
    )


def test_the_languages_really_carry_descriptions():
    for path in LANGUAGE_SOURCES:
        source = path.read_text(encoding="utf-8")
        assert len(strip_docs(source)) < len(source) * 0.8


def test_descriptions_do_not_change_the_runtime_behaviour():
    source = LANGUAGE_SOURCES[1].read_text(encoding="utf-8")
    with_docs, without = Session(), Session()
    with_docs.load(source)
    without.load(strip_docs(source))
    assert with_docs.type_of("Ventilation.reguler") == without.type_of("Ventilation.reguler")
    assert show(with_docs.value("Ventilation.seuil")) == show(without.value("Ventilation.seuil"))
