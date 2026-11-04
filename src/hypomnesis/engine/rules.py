"""Bounded positive forward chaining with explicit provenance and revocable defaults."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import reduce
from operator import add
from typing import Any, Literal

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Source
from hypomnesis.epistemics.provenance import Obs, obs
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.json import data_to_json, json_to_data
from hypomnesis.runtime.values import Variant, from_iterable
from hypomnesis.session import Session


@dataclass(frozen=True)
class Conclusion:
    value: Any


@dataclass(frozen=True)
class Rule:
    name: str
    target: str
    premises: tuple[str, ...]
    evaluate: Callable[[tuple[Any, ...]], Conclusion | None]
    default: bool = False

    def __post_init__(self) -> None:
        if any(not isinstance(s, str) or not s.strip() for s in (self.name, self.target)):
            raise ValueError("a rule requires a name and a target")
        if type(self.premises) is not tuple or any(
            not isinstance(s, str) or not s.strip() for s in self.premises
        ):
            raise ValueError("rule premises must be an immutable tuple of identifiers")
        if not callable(self.evaluate) or type(self.default) is not bool:
            raise ValueError("a rule requires a pure evaluator and a boolean default flag")


class RuleConflict(ValueError):
    def __init__(self, target: str, facts: tuple[Fact, ...]) -> None:
        self.target = target
        self.facts = facts
        super().__init__(f"incompatible rule conclusions for {target}: {[f.value for f in facts]}")


@dataclass(frozen=True)
class RuleReport:
    status: Literal["fixed_point", "budget_exhausted"]
    evaluations: int
    published: int


class RuleEngine:
    def __init__(self, base: KnowledgeBase, rules: tuple[Rule, ...]) -> None:
        if type(rules) is not tuple or any(not isinstance(rule, Rule) for rule in rules):
            raise ValueError("rules must be an immutable tuple")
        if len({r.name for r in rules}) != len(rules):
            raise ValueError("rule names must be distinct")
        self.base = base
        self.rules = rules
        self._published: dict[str, Fact] = {}
        self._defaults: dict[str, Source] = {}
        self._contributions: dict[str, Fact] = {}
        self._inputs: dict[str, tuple[Fact, ...]] = {}

    def _refresh(self) -> None:
        for key, old in list(self._published.items()):
            current = self.base.facts.get(key)
            if current == old:
                continue
            if (
                current is not None
                and isinstance(current.provenance, Obs)
                and self.base.sources[current.provenance.id].kind == "observation"
            ):
                identifiers = set(old.provenance.observations())
                for rule in self.rules:
                    source = self._defaults.get(rule.name)
                    if (
                        rule.target == key
                        and source is not None
                        and source.id in identifiers
                        and source.id not in self.base.retracted
                    ):
                        self.base.retract_source(
                            source.id, f"observation remplaçant le défaut {key}"
                        )
            self._published.pop(key, None)

    def run(self, *, budget: int = 1000) -> RuleReport:
        if type(budget) is not int or budget < 0:
            raise ValueError("rule evaluation budget must be a nonnegative integer")
        self._refresh()
        contributions = self._contributions
        for rule in self.rules:
            inputs = tuple(self.base.facts.get(key) for key in rule.premises)
            current = self.base.facts.get(rule.target)
            if (
                inputs != self._inputs.get(rule.name)
                or current is None
                or current != self._published.get(rule.target)
            ):
                contributions.pop(rule.name, None)
        evaluations = published = 0
        while True:
            changed = False
            for rule in self.rules:
                if evaluations == budget:
                    return RuleReport("budget_exhausted", evaluations, published)
                evaluations += 1
                if any(key not in self.base.facts for key in rule.premises):
                    continue
                current = self.base.facts.get(rule.target)
                owned = current is not None and current == self._published.get(rule.target)
                if rule.default and current is not None and not owned:
                    continue
                inputs = tuple(self.base.facts[key] for key in rule.premises)
                result = rule.evaluate(tuple(fact.value for fact in inputs))
                if result is None:
                    continue
                if not isinstance(result, Conclusion):
                    raise ValueError(f"rule {rule.name} must return Conclusion or None")
                proof = self.base.provenance_of(rule.premises)
                source = None
                if rule.default:
                    source = self._defaults.get(rule.name)
                    if source is None or source.id in self.base.retracted:
                        source = self.base._source("default", f"règle {rule.name}", 1.0)
                    proof = proof * obs(source.id)
                candidate = Fact(
                    rule.target, result.value, proof, f"rule:{rule.name}", rule.premises
                )
                if source is not None:
                    self._defaults[rule.name] = source
                contributions[rule.name] = candidate
                self._inputs[rule.name] = inputs
                alternatives = [
                    (name, fact)
                    for name, fact in sorted(contributions.items())
                    if fact.key == rule.target
                ]
                if any(not f.same_value(candidate) for _, f in alternatives):
                    raise RuleConflict(rule.target, tuple(f for _, f in alternatives))
                if current is not None and not current.same_value(candidate):
                    raise RuleConflict(rule.target, (current, candidate))
                if current is not None and not owned:
                    continue
                combined = Fact(
                    rule.target,
                    alternatives[0][1].value,
                    reduce(add, (f.provenance for _, f in alternatives)),
                    "rules:" + ",".join(name for name, _ in alternatives),
                    tuple(p for _, f in alternatives for p in f.premises),
                )
                if combined == current:
                    continue
                identifiers = set(combined.provenance.observations())
                sources = tuple(s for s in self._defaults.values() if s.id in identifiers)
                self.base.publish_fact(combined, sources=sources)
                self._published[rule.target] = combined
                changed = True
                published += 1
            if not changed:
                return RuleReport("fixed_point", evaluations, published)


def language_rule(
    session: Session,
    name: str,
    target: str,
    premises: tuple[str, ...],
    function: str,
    *,
    default: bool = False,
) -> Rule:
    if session.type_of(function) != "Json.t list -> Json.t option":
        raise ValueError(f"rule {function} must have type Json.t list -> Json.t option")
    callback = session.value(function)

    def evaluate(values: tuple[Any, ...]) -> Conclusion | None:
        result = session.interpreter.apply(
            callback, [from_iterable(data_to_json(v) for v in values)]
        )
        if isinstance(result, Variant) and result.tag == "None" and result.arg is None:
            return None
        if isinstance(result, Variant) and result.tag == "Some":
            return Conclusion(json_to_data(result.arg))
        raise EvaluationError(f"rule {function} did not return an option")

    return Rule(name, target, premises, evaluate, default)
