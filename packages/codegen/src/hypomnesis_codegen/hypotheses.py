"""Host-side ingestion of generated, closed data; no claim is trusted as evidence."""

from __future__ import annotations

from dataclasses import dataclass

from hypomnesis.contracts.codec import TypeCodec, closed_type
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.metavariables import MetaVar
from hypomnesis.language.typesystem.infer import Checker
from hypomnesis.language.typesystem.types import TCon, Type, TypePrinter, substitute
from hypomnesis.runtime.values import RecordValue, Value, Variant, iter_list


@dataclass(frozen=True)
class GeneratedInput:
    facts: tuple[Fact, ...]
    missing: tuple[MetaVar, ...]

    def report(self) -> dict[str, object]:
        return {
            "support": "Hypothesis",
            "facts": [fact.key for fact in self.facts],
            "missing": [
                {"key": meta.id, "type": TypePrinter().show(meta.type), "state": meta.state}
                for meta in self.missing
            ],
        }


def capture_input(
    checker: Checker,
    type_: Type | str,
    value: Value,
    kb: KnowledgeBase,
    *,
    key: str = "input",
) -> GeneratedInput:
    """Capture validated data; every absent option is an unresolved typed hole."""
    if not isinstance(key, str) or not key.strip():
        raise ValueError("input requires a nonempty key")
    codec = TypeCodec(checker, type_)
    codec.encode(value)
    facts: list[Fact] = []
    missing: list[MetaVar] = []

    def remember(path: str, payload: object) -> None:
        facts.append(
            kb.hypothesis(path, payload, "generated input, not independently sourced", 0.0)
        )

    def visit(type_: TCon, item: Value, path: str) -> None:
        info = checker.types_by_qname.get(type_.name)
        if info is not None and info.kind == "alias" and info.alias is not None:
            visit(closed_type(substitute(info.alias, type_.args)), item, path)
        elif type_.name == "option" and len(type_.args) == 1 and isinstance(item, Variant):
            child = TypeCodec(checker, type_.args[0])
            if item.tag == "None":
                missing.append(MetaVar(path, child))
            else:
                visit(child.type, item.arg, path)
        elif info is not None and info.kind == "record" and isinstance(item, RecordValue):
            fields = dict(item.fields)
            for field in info.fields:
                visit(
                    closed_type(substitute(field.type, type_.args)),
                    fields[field.name],
                    f"{path}.{field.name}",
                )
        elif type_.name == "list":
            for index, child in enumerate(iter_list(item)):
                visit(closed_type(type_.args[0]), child, f"{path}[{index}]")
        elif type_.name == "*" and isinstance(item, tuple):
            for index, (child_type, child) in enumerate(zip(type_.args, item, strict=True)):
                visit(closed_type(child_type), child, f"{path}[{index}]")
        elif info is not None and info.kind == "variant" and isinstance(item, Variant):
            remember(f"{path}.tag", item.tag)
            constructor = next(c for c in info.ctors if c.name == item.tag)
            if constructor.arg is not None:
                visit(closed_type(substitute(constructor.arg, type_.args)), item.arg, f"{path}.arg")
        else:
            payload = TypeCodec(checker, type_).encode(item)
            remember(path, payload)

    visit(codec.type, value, key)
    return GeneratedInput(tuple(facts), tuple(missing))
