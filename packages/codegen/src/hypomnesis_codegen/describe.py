"""Compiles a language's self-documentation into a prompt catalogue.

The catalogue is built from what the language says about itself: its documentation
comments and ``@tags`` (see ``hypomnesis.language.docs``) and the types the checker
infers. Only documented public items are published, like the public schema of an API: an
undocumented or ``_``-prefixed helper, and anything tagged ``@interne``, stays out of the
prompt. The wording lives in a template
(``templates/catalogue.md.j2``) so that it can be tuned without touching the code.
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict, dataclass, replace
from typing import Any

from jinja2 import Environment, PackageLoader

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.language import Language
from hypomnesis.engine.registry import ExtensionRegistry
from hypomnesis.language.docs import (
    Declaration,
    Doc,
    declarations_with_imports,
    is_public,
    published,
)

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
class PluginDoc:
    id: str
    version: str
    role: str
    signature: str
    input_schema: str
    output_schema: str
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class Catalogue:
    language: str
    description: str
    entry: str | None
    modules: tuple[ModuleDoc, ...]
    contracts: tuple[str, ...] = ()
    adapters: tuple[str, ...] = ()
    plugins: tuple[PluginDoc, ...] = ()

    def render(self) -> str:
        return _environment().get_template("catalogue.md.j2").render(c=self).strip() + "\n"

    def to_json(self) -> dict[str, Any]:
        document = json.loads(json.dumps({"version": "1.0.0", **asdict(self)}, allow_nan=False))
        SchemaRegistry.with_builtin_schemas().validate(
            "https://schemas.example.org/hypomnesis/language-catalogue/1.0.0", document
        )
        return document


def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("hypomnesis_codegen", "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["label"] = lambda tag: TAG_LABELS.get(tag, tag)
    env.filters["inline"] = lambda text: " ".join(text.split())
    env.filters["block"] = lambda text: textwrap.dedent(text).strip("\n")
    return env


def _parts(doc: Doc | None, member: bool = False) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Summary and tags to print. A ``@discret`` member is listed without its description."""
    if doc is None or (member and doc.tag("discret")):
        return "", ()
    return doc.summary, doc.tags


def catalogue(language: Language, *, plugins: ExtensionRegistry | None = None) -> Catalogue:
    """The documented, public face of a language."""
    found: list[Declaration] = []
    imports = dict(language.session.imported_sources)
    for source in language.plan.source_files():
        if source.path in imports:
            imports[source.path] = replace(imports[source.path], text=source.text)
    for source in language.plan.source_files():
        found += declarations_with_imports(
            source.text, source.path, imports, namespace=language.session.checker.root
        )

    modules: list[ModuleDoc] = []
    shown = published(found)
    shown_modules = [d for d in shown if d.kind == "module"]
    if any(d.kind in ("value", "type") and "." not in d.path for d in shown):
        shown_modules.append(Declaration("module", "", Doc("Déclarations à la racine.")))
    for module in shown_modules:
        summary, tags = _parts(module.doc)
        prefix = module.path + "." if module.path else ""

        def direct(d: Declaration, prefix: str = prefix) -> bool:
            return d.path.startswith(prefix) and "." not in d.path[len(prefix) :]

        types = []
        for t in (d for d in shown if d.kind == "type" and direct(d)):
            t_summary, t_tags = _parts(t.doc)
            members = [
                d
                for d in found
                if d.path.startswith(t.path + ".") and is_public(d) and not d.internal
            ]
            types.append(
                TypeDoc(
                    t.path,
                    t_summary,
                    t_tags,
                    tuple(
                        FieldDoc(d.path, *_parts(d.doc, member=True), d.type_text or "")
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
            for d in shown
            if d.kind == "value" and direct(d)
        )
        modules.append(ModuleDoc(module.path, summary, tags, tuple(types), values))
    return Catalogue(
        language.name,
        language.manifest.get("description", ""),
        language.manifest.get("procedure", {}).get("entry"),
        tuple(modules),
        tuple(language.manifest.get("contracts", [])),
        tuple(language.manifest.get("adapters", [])),
        tuple(
            PluginDoc(
                item["id"],
                item["version"],
                item["role"],
                f"{item['signature']['input']} -> {item['signature']['output']}",
                item["input_schema"],
                item["output_schema"],
                tuple(item["permissions"]),
            )
            for item in (plugins.list() if plugins is not None else [])
        ),
    )
