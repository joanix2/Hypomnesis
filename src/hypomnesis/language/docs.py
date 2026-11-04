"""Documentation comments ``(** … *)`` and their ``@tag`` annotations.

A language documents itself, in the spirit of GraphQL descriptions: the comment placed
right before a declaration (module, value, type, record field, constructor) describes it.
Its first paragraph is the description; every line starting with ``@name`` is a tag
(``@quand``, ``@unité``, ``@exemple``, …) whose meaning is left to the language author and
to the consumers of the documentation (prompt templates, ``describe`` exports).

Ordinary comments ``(* … *)`` stay invisible. Nothing here knows any domain.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

from hypomnesis.language import ast as A
from hypomnesis.language.errors import Span
from hypomnesis.language.parser import parse_program

_DOC = re.compile(r"\(\*\*(?!\))(.*?)\*\)", re.S)
_TAG = re.compile(r"^@(\w+)\s*(.*)$")


@dataclass(frozen=True)
class Doc:
    summary: str
    tags: tuple[tuple[str, str], ...] = ()

    def tag(self, name: str) -> list[str]:
        return [text for tag, text in self.tags if tag == name]


@dataclass(frozen=True)
class Declaration:
    kind: str  # "module" | "value" | "type" | "field" | "constructor"
    path: str  # qualified: Module.name, Module.type, Module.type.field
    doc: Doc | None
    type_text: str | None = None  # field / constructor type, as written in the source


def parse_doc(body: str) -> Doc:
    """Description, then ``@tags``. A tag continues on the following lines; their relative
    indentation is kept (``textwrap.dedent`` the text to show a block of code)."""
    summary: list[str] = []
    tags: list[list[str]] = []
    tag_indent = 0
    for raw in textwrap.dedent(body).strip().splitlines():
        line = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        match = _TAG.match(line)
        if match:
            tags.append([match.group(1), match.group(2)])
            tag_indent = indent
        elif tags and line:
            text = " " * max(0, indent - tag_indent) + line
            tags[-1][1] = f"{tags[-1][1]}\n{text}" if tags[-1][1] else text
        elif not tags and line:
            summary.append(line)
    return Doc(" ".join(summary), tuple((name, text) for name, text in tags))


def _doc_index(source: str) -> dict[int, Doc]:
    """Doc comments by the (1-based) line of the first code line that follows them."""
    lines = source.splitlines()
    index: dict[int, Doc] = {}
    for match in _DOC.finditer(source):
        following = source.count("\n", 0, match.end()) + 1  # 0-based index of the next line
        while following < len(lines) and not lines[following].strip():
            following += 1
        if following < len(lines):
            index[following + 1] = parse_doc(match.group(1))
    return index


def _slice(lines: list[str], span: Span | None) -> str | None:
    if span is None or span.line != span.end_line:
        return None
    return lines[span.line - 1][span.column - 1 : span.end_column - 1].strip()


def declarations(source: str, program: A.Program | None = None) -> list[Declaration]:
    """Every declaration of a source, in order, with its documentation if any."""
    program = program or parse_program(source)
    lines = source.splitlines()
    docs = _doc_index(source)
    found: list[Declaration] = []

    def doc_at(span: Span | None) -> Doc | None:
        return docs.get(span.line) if span else None

    def walk(items: tuple[A.Item, ...], prefix: str) -> None:
        for item in items:
            if isinstance(item, A.ModuleItem):
                path = prefix + item.name
                found.append(Declaration("module", path, doc_at(item.span)))
                walk(item.items, path + ".")
            elif isinstance(item, A.LetItem):
                for i, binding in enumerate(item.bindings):
                    if isinstance(binding, A.FunBinding):
                        doc = doc_at(binding.span) or (doc_at(item.span) if i == 0 else None)
                        found.append(Declaration("value", prefix + binding.name, doc))
            elif isinstance(item, A.TypeItem):
                for i, definition in enumerate(item.defs):
                    doc = doc_at(definition.span) or (doc_at(item.span) if i == 0 else None)
                    path = prefix + definition.name
                    found.append(Declaration("type", path, doc))
                    on_line = definition.span.line if definition.span else None
                    if isinstance(definition.rhs, A.RecordRhs):
                        for name, texpr in definition.rhs.fields:
                            line = texpr.span.line if texpr.span else None
                            doc = doc_at(texpr.span) if line != on_line else None
                            found.append(
                                Declaration(
                                    "field", f"{path}.{name}", doc, _slice(lines, texpr.span)
                                )
                            )
                    elif isinstance(definition.rhs, A.VariantRhs):
                        for name, texpr in definition.rhs.ctors:
                            text = _slice(lines, texpr.span) if texpr else None
                            found.append(Declaration("constructor", f"{path}.{name}", None, text))

    walk(program.items, "")
    return found
