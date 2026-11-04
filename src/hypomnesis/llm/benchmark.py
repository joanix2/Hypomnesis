"""Benchmark: natural language → M1 program, per model (hypothesis H2).

For each case of a language's ``benchmark.json`` and each model, the LLM
translates the request; the program is then checked at four levels:

1. **syntax** — it parses;
2. **typing** — it type-checks in the language (first try, then after repairs);
3. **semantics** — the values it binds are the expected ones (units converted,
   unknowns left unknown, the right procedure called);
4. **execution** — its procedure runs (dry-run) without error.

Expectations are data of the language package; this runner is generic.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

from hypomnesis.engine.bridge import to_json
from hypomnesis.engine.language import Language, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.language import ast as A
from hypomnesis.language.errors import HypomnesisError, Span
from hypomnesis.language.parser import parse_program
from hypomnesis.llm.prompting import BASE, Strategy
from hypomnesis.llm.translation import ChatClient, Translation, translate

ANY = "*"


@dataclass
class CaseResult:
    language: str
    case: str
    model: str
    translation: Translation
    semantic_errors: list[str] = field(default_factory=list)
    executed: bool = False
    execution_error: str = ""
    first_ok: bool = False  # the first attempt ran and is semantically right (no repair needed)
    strategy: str = ""  # prompting strategy, empty for the default one
    split: str = "dev"

    @property
    def label(self) -> str:
        return f"{self.model} · {self.strategy}" if self.strategy else self.model

    @property
    def parsed_first(self) -> bool:
        return self.translation.attempts[0].stage != "syntax error"

    @property
    def typed_first(self) -> bool:
        return self.translation.attempts[0].stage in ("", "runtime error")

    @property
    def typed(self) -> bool:
        return self.translation.compiled

    @property
    def correct_first(self) -> bool:
        return self.first_ok

    @property
    def correct(self) -> bool:
        return self.typed and not self.semantic_errors

    @property
    def output_tokens(self) -> int:
        return sum(a.reply.output_tokens for a in self.translation.attempts)

    @property
    def seconds(self) -> float:
        return sum(a.reply.seconds for a in self.translation.attempts)

    def to_json(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "case": self.case,
            "model": self.model,
            "typed_first": self.typed_first,
            "typed": self.typed,
            "correct": self.correct,
            "correct_first": self.correct_first,
            "strategy": self.strategy,
            "split": self.split,
            "executed": self.executed,
            "attempts": len(self.translation.attempts),
            "seconds": round(self.seconds, 2),
            "output_tokens": self.output_tokens,
            "tokens_per_second": round(
                sum(a.reply.tokens_per_second for a in self.translation.attempts)
                / len(self.translation.attempts),
                1,
            ),
            "semantic_errors": self.semantic_errors,
            "execution_error": self.execution_error,
            "program": self.translation.program,
            "diagnostics": [a.error for a in self.translation.attempts if a.error],
        }


def _same(expected: Any, actual: Any) -> bool:
    if expected == ANY:
        return True
    if isinstance(expected, int | float) and isinstance(actual, int | float):
        return math.isclose(expected, actual, rel_tol=1e-6, abs_tol=1e-9)
    return expected == actual


def _text(source: str, span: Span) -> str:
    lines = source.split("\n")
    if span.line == span.end_line:
        return lines[span.line - 1][span.column - 1 : span.end_column - 1]
    middle = lines[span.line : span.end_line - 1]
    first = lines[span.line - 1][span.column - 1 :]
    return "\n".join([first, *middle, lines[span.end_line - 1][: span.end_column - 1]])


def inline_records(program: str) -> list[str]:
    """Source text of every record literal written in a program, wherever it appears."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, A.Record) and node.span is not None:
            found.append(_text(program, node.span))
        if is_dataclass(node) and not isinstance(node, type):
            for f in fields(node):
                walk(getattr(node, f.name))
        elif isinstance(node, tuple | list):
            for item in node:
                walk(item)

    walk(parse_program(program))
    return found


def _bound_or_inline(language: Language, program: str, binding: str, names: list[str]) -> Any:
    """The value of ``binding``; if the program never names it, the inline record that carries
    the expected fields (a record written directly in the call is as good as a variable)."""
    try:
        return to_json(language.session.value(binding))
    except HypomnesisError:
        for text in inline_records(program):
            candidate = to_json(language.session.eval(text).value)
            if isinstance(candidate, dict) and all(n in candidate for n in names):
                return candidate
        raise


def semantic_errors(language_root: Path, program: str, expect: dict[str, Any]) -> list[str]:
    language = load_language(language_root)
    language.load_program(program)
    errors = []
    for binding, fields_ in expect.get("bindings", {}).items():
        try:
            actual = _bound_or_inline(language, program, binding, list(fields_))
        except HypomnesisError:
            errors.append(f"le programme ne définit pas `{binding}`")
            continue
        for name, expected in fields_.items():
            got = actual.get(name, "<absent>") if isinstance(actual, dict) else "<absent>"
            if not _same(expected, got):
                errors.append(f"{binding}.{name} = {got!r}, attendu {expected!r}")
    text = re.sub(r"\s+", " ", program)
    for call in expect.get("calls", []):
        if call not in text:
            errors.append(f"appel attendu : {call}")
    for call in expect.get("not_calls", []):
        if call in text:
            errors.append(f"appel inattendu : {call}")
    return errors


def _dry_run(root: Path, program: str, environment: dict) -> str:
    """ "" if the procedure runs in simulation, else the runtime diagnostic."""
    try:
        run_procedure(
            load_language(root),
            program,
            mode="dry-run",
            out_dir=Path("sortie") / "benchmark-llm" / "runs",
            environment=environment,
            max_steps=200,
        )
    except HypomnesisError as exc:
        return exc.render(program, "<programme>")
    except Exception as exc:  # l'échec d'exécution est une mesure, pas une erreur du banc
        return f"{type(exc).__name__}: {exc}"
    return ""


def run_case(
    client: ChatClient,
    model: str,
    root: Path,
    spec: dict,
    case: dict,
    repairs: int,
    strategy: Strategy = BASE,
) -> CaseResult:
    language = load_language(root)
    examples = [(root / e).read_text(encoding="utf-8") for e in spec.get("examples", [])]
    environment = case.get("environment", {})
    translation = translate(
        client,
        model,
        language,
        case["request"],
        examples=examples,
        max_repairs=repairs,
        simulate=lambda program: _dry_run(root, program, environment),
        strategy=strategy,
    )
    result = CaseResult(
        language.name,
        case["id"],
        model,
        translation,
        strategy="" if strategy == BASE else str(strategy),
        split=case.get("split", "dev"),
    )
    if not translation.compiled:
        return result
    expect = case.get("expect", {})

    def check(program: str) -> list[str]:
        try:
            return semantic_errors(root, program, expect)
        except Exception as exc:  # un programme inattendu est une mesure, pas une panne du banc
            return [f"contrôle impossible : {type(exc).__name__}: {exc}"]

    result.semantic_errors = check(translation.program)
    first = translation.attempts[0]
    result.first_ok = first.stage == "" and (
        not result.semantic_errors if len(translation.attempts) == 1 else not check(first.program)
    )
    result.execution_error = translation.attempts[-1].error if not translation.accepted else ""
    result.executed = translation.accepted
    return result


def run_benchmark(
    client: ChatClient,
    models: list[str],
    languages: list[Path],
    *,
    repairs: int = 2,
    strategy: Strategy = BASE,
    splits: Sequence[str] | None = None,
    log=print,
) -> list[CaseResult]:
    results = []
    for root in languages:
        spec = json.loads((root / "benchmark.json").read_text(encoding="utf-8"))
        for model in models:
            for case in spec["cases"]:
                if splits is not None and case.get("split", "dev") not in splits:
                    continue
                r = run_case(client, model, root, spec, case, repairs, strategy)
                mark = "✓" if r.correct and r.executed else ("~" if r.typed else "✗")
                log(
                    f"  {mark} {model:<14} {r.language}/{r.case}  {r.seconds:5.1f} s  "
                    f"{len(r.translation.attempts)} essai(s)  {'; '.join(r.semantic_errors)[:90]}"
                )
                results.append(r)
    return results


def summary(results: list[CaseResult]) -> str:
    models = list(dict.fromkeys(r.label for r in results))
    lines = [
        "| Modèle | Cas | Parsé (1er essai) | Typé (1er essai) | **Correct (1er essai)** "
        "| Typé (après réparations) | **Correct** | Exécuté | Essais moy. | Temps moy. "
        "| Jetons générés moy. | Jetons/s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model in models:
        rs = [r for r in results if r.label == model]
        n = len(rs)

        def pct(k: int, n: int = n) -> str:
            return f"{k}/{n} ({100 * k // n} %)"

        tps = [
            a.reply.tokens_per_second
            for r in rs
            for a in r.translation.attempts
            if a.reply.tokens_per_second
        ]
        lines.append(
            f"| {model} | {n} | {pct(sum(r.parsed_first for r in rs))} "
            f"| {pct(sum(r.typed_first for r in rs))} "
            f"| **{pct(sum(r.correct_first for r in rs))}** | {pct(sum(r.typed for r in rs))} "
            f"| **{pct(sum(r.correct for r in rs))}** | {pct(sum(r.executed for r in rs))} "
            f"| {sum(len(r.translation.attempts) for r in rs) / n:.2f} "
            f"| {sum(r.seconds for r in rs) / n:.1f} s | {sum(r.output_tokens for r in rs) // n} "
            f"| {sum(tps) / len(tps) if tps else 0:.0f} |"
        )
    return "\n".join(lines)
