"""Commentaires de documentation `(** … *)` et balises `@tag`."""

from hypomnesis.language.docs import declarations, parse_doc

SOURCE = """\
(** Le module des plaques. *)
module Plaque = struct
  (** Une demande.
      @unité mm *)
  type demande = {
    (** Largeur de la plaque.
        @unité mm
        @exemple « 12 cm » vaut 120.0 *)
    largeur : float;
    hauteur : float;
  }

  (* commentaire ordinaire : ne documente rien *)
  let cachee = 1

  (** Dimensionne une plaque.
      @quand « crée », « conçois »
      @quand « dimensionne » *)

  let concevoir (d : demande) = d

  type forme = Carre | Cercle of float
end
"""


def by_path():
    return {d.path: d for d in declarations(SOURCE)}


def test_parse_doc_splits_description_and_tags():
    doc = parse_doc("  Une phrase\n  sur deux lignes.\n  @quand un\n    et deux\n  @unité mm\n")
    assert doc.summary == "Une phrase sur deux lignes."
    assert doc.tags == (("quand", "un\n  et deux"), ("unité", "mm"))
    assert doc.tag("quand") == ["un\n  et deux"] and doc.tag("absent") == []


def test_docs_attach_to_modules_types_fields_and_values():
    found = by_path()
    assert found["Plaque"].doc.summary == "Le module des plaques."
    assert found["Plaque.demande"].doc.tag("unité") == ["mm"]
    assert found["Plaque.demande.largeur"].doc.tag("exemple") == ["« 12 cm » vaut 120.0"]
    assert found["Plaque.demande.largeur"].type_text == "float"
    assert found["Plaque.demande.hauteur"].doc is None


def test_blank_lines_are_allowed_but_ordinary_comments_detach():
    found = by_path()
    assert found["Plaque.concevoir"].doc.tag("quand") == [
        "« crée », « conçois »",
        "« dimensionne »",
    ]
    assert found["Plaque.cachee"].doc is None


def test_constructors_and_kinds_are_listed():
    found = by_path()
    assert found["Plaque.forme.Cercle"].kind == "constructor"
    assert found["Plaque.forme.Cercle"].type_text == "float"
    assert found["Plaque.forme.Carre"].type_text is None
    assert [d.kind for d in declarations(SOURCE)][:3] == ["module", "type", "field"]


def test_multiline_tags_keep_relative_indentation():
    doc = parse_doc("Résumé.\n @squelette\n   let a = 1\n     let b = 2\n @unité mm")
    assert doc.tag("squelette") == ["  let a = 1\n    let b = 2"]
    assert doc.tag("unité") == ["mm"]
