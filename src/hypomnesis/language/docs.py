"""Documentation comments ``(** … *)`` and their ``@tag`` annotations.

A language documents itself, in the spirit of GraphQL descriptions: the comment placed
right before a declaration (module, value, type, record field, constructor) describes it.
Its first paragraph is the description; every line starting with ``@name`` is a tag
(``@quand``, ``@unité``, ``@exemple``, …) whose meaning is left to the language author and
to the consumers of the documentation (prompt templates, ``describe`` exports).

Ordinary comments ``(* … *)`` stay invisible. Nothing here knows any domain.

Comments are found by lexing the source (a ``(**`` inside a string literal or inside an
ordinary comment is not a description) and attached by position: a description belongs to the
declaration whose first token follows it.

Every public declaration of a language must be described. *Public* means that neither the
name nor an ancestor's name starts with ``_``. The ``@interne`` tag marks a described
declaration that the prompt catalogue does not publish (its members are not published either,
and need no description); ``@discret`` keeps a field or a constructor in the catalogue, with
its name and type, without repeating its description.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from itertools import pairwise

from lark import Token

from hypomnesis.language import ast as A
from hypomnesis.language.errors import Span
from hypomnesis.language.parser import lex, parse_program

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
    span: Span | None = None  # where the declaration starts (its name, for a member)

    @property
    def internal(self) -> bool:
        return self.doc is not None and bool(self.doc.tag("interne"))


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


def _doc_index(tokens: list[Token]) -> dict[int, Doc]:
    """Doc comments by the (1-based) line of the first token that follows them."""
    index: dict[int, Doc] = {}
    for token, following in pairwise(tokens):
        text = str(token)
        is_doc = token.type == "COMMENT" and text.startswith("(**") and not text.startswith("(**)")
        if is_doc and following.line is not None:
            index[following.line] = parse_doc(text[3:-2])
    return index


def _token_span(token: Token) -> Span | None:
    if None in (token.line, token.column, token.end_line, token.end_column):
        return None
    return Span(
        int(token.line or 0),
        int(token.column or 0),
        int(token.end_line or 0),
        int(token.end_column or 0),
    )


def _members(code: list[Token], rhs: A.RecordRhs | A.VariantRhs) -> list[Token | None]:
    """The name token of each field / constructor of a type body, in order."""
    if rhs.span is None:
        return [None] * len(rhs.fields if isinstance(rhs, A.RecordRhs) else rhs.ctors)
    start, end = (rhs.span.line, rhs.span.column), (rhs.span.end_line, rhs.span.end_column)
    names: list[Token] = []
    for i, token in enumerate(code):
        if not start <= (token.line, token.column) < end:
            continue
        if isinstance(rhs, A.RecordRhs):
            if token.type == "LIDENT" and i + 1 < len(code) and code[i + 1].type == "COLON":
                names.append(token)
        elif token.type == "UPATH" and code[i - 1].type in ("EQ", "BAR"):
            names.append(token)
    wanted = [name for name, _ in (rhs.fields if isinstance(rhs, A.RecordRhs) else rhs.ctors)]
    return list(names) if [str(n) for n in names] == wanted else [None] * len(wanted)


def _slice(lines: list[str], span: Span | None) -> str | None:
    if span is None or span.line != span.end_line:
        return None
    return lines[span.line - 1][span.column - 1 : span.end_column - 1].strip()


def declarations(source: str, program: A.Program | None = None) -> list[Declaration]:
    """Every declaration of a source, in order, with its documentation if any."""
    program = program or parse_program(source)
    lines = source.splitlines()
    tokens = [t for t in lex(source) if t.type != "WS"]
    code = [t for t in tokens if t.type != "COMMENT"]
    docs = _doc_index(tokens)
    found: list[Declaration] = []

    def doc_at(span: Span | None) -> Doc | None:
        return docs.get(span.line) if span else None

    def member(kind: str, path: str, name: Token | None, on_line: int | None, text: str | None):
        # a member written on the line of its type cannot own the description before it
        doc = docs.get(name.line) if name and name.line not in (None, on_line) else None
        found.append(Declaration(kind, path, doc, text, _token_span(name) if name else None))

    def walk(items: tuple[A.Item, ...], prefix: str) -> None:
        for item in items:
            if isinstance(item, A.ModuleItem):
                path = prefix + item.name
                found.append(Declaration("module", path, doc_at(item.span), None, item.span))
                walk(item.items, path + ".")
            elif isinstance(item, A.LetItem):
                for i, binding in enumerate(item.bindings):
                    if isinstance(binding, A.FunBinding):
                        doc = doc_at(binding.span) or (doc_at(item.span) if i == 0 else None)
                        span = item.span if i == 0 and item.span else binding.span
                        found.append(Declaration("value", prefix + binding.name, doc, None, span))
            elif isinstance(item, A.TypeItem):
                for i, definition in enumerate(item.defs):
                    doc = doc_at(definition.span) or (doc_at(item.span) if i == 0 else None)
                    path = prefix + definition.name
                    span = item.span if i == 0 and item.span else definition.span
                    found.append(Declaration("type", path, doc, None, span))
                    on_line = definition.span.line if definition.span else None
                    rhs = definition.rhs
                    if isinstance(rhs, A.RecordRhs):
                        names = _members(code, rhs)
                        for (name, texpr), token in zip(rhs.fields, names, strict=True):
                            text = _slice(lines, texpr.span)
                            member("field", f"{path}.{name}", token, on_line, text)
                    elif isinstance(rhs, A.VariantRhs):
                        names = _members(code, rhs)
                        for (name, texpr), token in zip(rhs.ctors, names, strict=True):
                            text = _slice(lines, texpr.span) if texpr else None
                            member("constructor", f"{path}.{name}", token, on_line, text)

    walk(program.items, "")
    return found


def is_public(declaration: Declaration) -> bool:
    """No component of the qualified name starts with ``_``."""
    return not any(part.startswith("_") for part in declaration.path.split("."))


def published(found: list[Declaration]) -> list[Declaration]:
    """The declarations the prompt catalogue may show: public, described, and neither
    ``@interne`` nor nested in an ``@interne`` declaration."""
    hidden = [d.path + "." for d in found if d.internal]
    return [
        d
        for d in found
        if d.doc and is_public(d) and not d.internal and not d.path.startswith(tuple(hidden))
    ]


def missing_descriptions(source: str, program: A.Program | None = None) -> list[Declaration]:
    """Public declarations without a description, in source order. An ``@interne``
    declaration must be described too; its members are exempt."""
    found = declarations(source, program)
    hidden = [d.path + "." for d in found if d.internal]
    return [d for d in found if not d.doc and is_public(d) and not d.path.startswith(tuple(hidden))]
