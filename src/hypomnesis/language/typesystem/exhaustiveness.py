"""Usefulness of typed pattern matrices (Maranget, JFP 2007).

Guards never contribute coverage. Open scalar domains require a default
pattern; finite signatures are specialized recursively, including products.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hypomnesis.ir import core as ir
from hypomnesis.language.errors import CompilerWarning, Span
from hypomnesis.language.typesystem.types import TUPLE, TCon, Type, prune, substitute

if TYPE_CHECKING:
    from hypomnesis.language.typesystem.infer import TypeInfo

Row = tuple[ir.Pattern, ...]
Matrix = list[Row]


@dataclass(frozen=True)
class PatternArm:
    pattern: ir.Pattern
    guarded: bool
    span: Span | None


@dataclass(frozen=True)
class MatchSite:
    type: Type
    arms: tuple[PatternArm, ...]
    span: Span | None


@dataclass(frozen=True)
class _Head:
    pattern: ir.Pattern
    types: tuple[Type, ...] = ()

    def build(self, args: Row) -> ir.Pattern:
        p = self.pattern
        if isinstance(p, ir.PCtor):
            return ir.PCtor(p.tag, args[0] if args else None, index=p.index)
        if isinstance(p, ir.PTuple):
            return ir.PTuple(args)
        if isinstance(p, ir.PRecord):
            return ir.PRecord(
                tuple((name, arg) for (name, _), arg in zip(p.fields, args, strict=True))
            )
        return p


def _unwrap(pattern: ir.Pattern) -> ir.Pattern:
    while isinstance(pattern, ir.PAlias):
        pattern = pattern.pattern
    return pattern


def _wild(pattern: ir.Pattern) -> bool:
    return isinstance(_unwrap(pattern), (ir.PWild, ir.PVar))


def _expand(matrix: Matrix) -> Matrix:
    rows = []
    for row in matrix:
        if row and isinstance(pattern := _unwrap(row[0]), ir.POr):
            rows.extend(_expand([(pattern.left, *row[1:]), (pattern.right, *row[1:])]))
        else:
            rows.append(row)
    return rows


class Coverage:
    def __init__(self, types: Mapping[str, TypeInfo]) -> None:
        self.types = types

    def _signature(self, t: Type) -> tuple[_Head, ...] | None:
        t = prune(t)
        if not isinstance(t, TCon):
            return None
        if t.name == "bool":
            return (_Head(ir.PLit(False)), _Head(ir.PLit(True)))
        if t.name == "unit":
            return (_Head(ir.PLit(())),)
        if t.name == TUPLE:
            return (_Head(ir.PTuple(tuple(ir.PWild() for _ in t.args)), t.args),)
        info = self.types.get(t.name)
        if info is not None and info.kind == "record":
            return (
                _Head(
                    ir.PRecord(tuple((field.name, ir.PWild()) for field in info.fields)),
                    tuple(substitute(field.type, t.args) for field in info.fields),
                ),
            )
        if info is not None and info.ctors:
            return tuple(
                _Head(
                    ir.PCtor(c.name, None, index=c.index),
                    () if c.arg is None else (substitute(c.arg, t.args),),
                )
                for c in info.ctors
            )
        return None

    def _head(self, pattern: ir.Pattern, t: Type) -> _Head:
        pattern = _unwrap(pattern)
        if isinstance(pattern, ir.PLit):
            return _Head(pattern)
        for head in self._signature(t) or ():
            if isinstance(pattern, ir.PCtor) and isinstance(head.pattern, ir.PCtor):
                if pattern.tag == head.pattern.tag:
                    return head
            elif isinstance(pattern, type(head.pattern)):
                return head
        raise ValueError(f"unresolved typed pattern: {pattern!r}")

    @staticmethod
    def _arguments(pattern: ir.Pattern, head: _Head) -> Row:
        pattern = _unwrap(pattern)
        if _wild(pattern):
            return tuple(ir.PWild() for _ in head.types)
        if isinstance(pattern, ir.PCtor):
            return () if pattern.arg is None else (pattern.arg,)
        if isinstance(pattern, ir.PTuple):
            return pattern.items
        if isinstance(pattern, ir.PRecord) and isinstance(head.pattern, ir.PRecord):
            fields = dict(pattern.fields)
            return tuple(fields.get(name, ir.PWild()) for name, _ in head.pattern.fields)
        return ()

    def _specialize(self, matrix: Matrix, head: _Head, t: Type) -> Matrix:
        return [
            (*self._arguments(row[0], head), *row[1:])
            for row in matrix
            if _wild(row[0]) or self._head(row[0], t).pattern == head.pattern
        ]

    @staticmethod
    def _fresh(t: Type, present: tuple[_Head, ...]) -> ir.Pattern:
        t = prune(t)
        if not isinstance(t, TCon) or t.name not in ("int", "float", "string"):
            return ir.PWild()
        index = 0
        while True:
            value = (
                "a" * index if t.name == "string" else float(index) if t.name == "float" else index
            )
            candidate = ir.PLit(value)
            if all(candidate != head.pattern for head in present):
                return candidate
            index += 1

    def useful(self, matrix: Matrix, vector: Row, types: tuple[Type, ...]) -> Row | None:
        matrix = _expand(matrix)
        if not vector:
            return () if not matrix else None
        pattern, rest = _unwrap(vector[0]), vector[1:]
        t, tail_types = types[0], types[1:]
        if isinstance(pattern, ir.POr):
            left = self.useful(matrix, (pattern.left, *rest), types)
            return left if left is not None else self.useful(matrix, (pattern.right, *rest), types)
        if not _wild(pattern):
            head = self._head(pattern, t)
            witness = self.useful(
                self._specialize(matrix, head, t),
                (*self._arguments(pattern, head), *rest),
                (*head.types, *tail_types),
            )
            if witness is None:
                return None
            count = len(head.types)
            return (head.build(witness[:count]), *witness[count:])
        present = tuple(self._head(row[0], t) for row in matrix if not _wild(row[0]))
        signature = self._signature(t)
        missing = (
            tuple(h for h in signature if all(h.pattern != p.pattern for p in present))
            if signature is not None
            else ()
        )
        if signature is not None and not missing:
            for head in signature:
                witness = self.useful(
                    self._specialize(matrix, head, t),
                    (*tuple(ir.PWild() for _ in head.types), *rest),
                    (*head.types, *tail_types),
                )
                if witness is not None:
                    count = len(head.types)
                    return (head.build(witness[:count]), *witness[count:])
            return None
        defaults = [row[1:] for row in matrix if _wild(row[0])]
        witness = self.useful(defaults, rest, tail_types)
        if witness is None:
            return None
        uncovered = (
            missing[0].build(tuple(ir.PWild() for _ in missing[0].types))
            if missing
            else self._fresh(t, present)
        )
        return (uncovered, *witness)

    def warnings(self, site: MatchSite) -> list[CompilerWarning]:
        matrix: Matrix = []
        warnings = []
        for index, arm in enumerate(site.arms, 1):
            if self.useful(matrix, (arm.pattern,), (site.type,)) is None:
                warnings.append(CompilerWarning(f"unreachable pattern (arm {index})", arm.span))
            if not arm.guarded:
                matrix.append((arm.pattern,))
        witness = self.useful(matrix, (ir.PWild(),), (site.type,))
        if witness is not None:
            warnings.append(
                CompilerWarning(
                    f"non-exhaustive pattern matching; example: {show_pattern(witness[0])}",
                    site.span,
                )
            )
        return warnings


def show_pattern(pattern: ir.Pattern) -> str:
    pattern = _unwrap(pattern)
    if isinstance(pattern, ir.PLit):
        value = pattern.value
        if value == ():
            return "()"
        if isinstance(value, bool):
            return str(value).lower()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(pattern, ir.PCtor):
        if pattern.tag == "::" and isinstance(pattern.arg, ir.PTuple):
            head, tail = pattern.arg.items
            return f"({show_pattern(head)} :: {show_pattern(tail)})"
        return pattern.tag + (f" ({show_pattern(pattern.arg)})" if pattern.arg is not None else "")
    if isinstance(pattern, ir.PTuple):
        return "(" + ", ".join(map(show_pattern, pattern.items)) + ")"
    if isinstance(pattern, ir.PRecord):
        return "{ " + "; ".join(f"{n} = {show_pattern(p)}" for n, p in pattern.fields) + " }"
    return "_"
