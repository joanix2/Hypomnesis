"""Compiles a language's self-documentation into a prompt catalogue.

The catalogue is built from what the language says about itself: its documentation
comments and ``@tags`` (see ``hypomnesis.language.docs``) and the types the checker
infers. Only documented items are published, like the public schema of an API: an
undocumented helper stays out of the prompt. The wording lives in a template
(``templates/catalogue.md.j2``) so that it can be tuned without touching the code.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

from jinja2 import Environment, PackageLoader

from hypomnesis.engine.language import Language
from hypomnesis.language.docs import Declaration, Doc, declarations

# Display labels of the tag vocabulary; an unknown tag is shown under its own name.
TAG_LABELS = {
    "quand": "Utiliser quand",
    "pas_quand": "Ne pas utiliser quand",
    "unité": "Unité",
    "défaut": "Par défaut",
    "exemple": "Exemple",
    "note": "Note",
    "squelette": "Squelette de programme",
}


@dataclass(frozen=True)
class Described:
    path: str
    summary: str = ""
    tags: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class FieldDoc(Described):
    type: str = ""


@dataclass(frozen=True)
class TypeDoc(Described):
    fields: tuple[FieldDoc, ...] = ()
    constructors: tuple[FieldDoc, ...] = ()


@dataclass(frozen=True)
class ValueDoc(Described):
    signature: str = ""

    @property
    def is_procedure(self) -> bool:
        return self.signature.endswith("Effect.t")


@dataclass(frozen=True)
class ModuleDoc(Described):
    types: tuple[TypeDoc, ...] = ()
    values: tuple[ValueDoc, ...] = ()


@dataclass(frozen=True)
class Catalogue:
    language: str
    description: str
    entry: str
    modules: tuple[ModuleDoc, ...]

    def render(self) -> str:
        return _environment().get_template("catalogue.md.j2").render(c=self).strip() + "\n"


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("hypomnesis.llm", "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["label"] = lambda tag: TAG_LABELS.get(tag, tag)
    env.filters["inline"] = lambda text: " ".join(text.split())
    env.filters["block"] = lambda text: textwrap.dedent(text).strip("\n")
    return env


def _parts(doc: Doc | None) -> tuple[str, tuple[tuple[str, str], ...]]:
    return (doc.summary, doc.tags) if doc else ("", ())


def catalogue(language: Language) -> Catalogue:
    """The documented, public face of a language."""
    found: list[Declaration] = []
    for source in language.manifest["sources"]:
        found += declarations((language.root / source).read_text(encoding="utf-8"))

    modules: list[ModuleDoc] = []
    for module in (d for d in found if d.kind == "module" and d.doc):
        summary, tags = _parts(module.doc)
        prefix = module.path + "."

        def direct(d: Declaration, prefix: str = prefix) -> bool:
            return d.path.startswith(prefix) and "." not in d.path[len(prefix) :]

        types = []
        for t in (d for d in found if d.kind == "type" and d.doc and direct(d)):
            t_summary, t_tags = _parts(t.doc)
            members = [d for d in found if d.path.startswith(t.path + ".")]
            types.append(
                TypeDoc(
                    t.path,
                    t_summary,
                    t_tags,
                    tuple(
                        FieldDoc(d.path, *_parts(d.doc), d.type_text or "")
                        for d in members
                        if d.kind == "field"
                    ),
                    tuple(
                        FieldDoc(d.path, "", (), d.type_text or "")
                        for d in members
                        if d.kind == "constructor"
                    ),
                )
            )
        values = tuple(
            ValueDoc(d.path, *_parts(d.doc), language.session.type_of(d.path))
            for d in found
            if d.kind == "value" and d.doc and direct(d)
        )
        modules.append(ModuleDoc(module.path, summary, tags, tuple(types), values))
    return Catalogue(
        language.name,
        language.manifest.get("description", ""),
        language.procedure["entry"],
        tuple(modules),
    )
