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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hypomnesis.engine.bridge import to_json
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
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

    @property
    def parsed_first(self) -> bool:
        return self.translation.attempts[0].stage != "syntax error"

    @property
    def typed_first(self) -> bool:
        return not self.translation.attempts[0].error

    @property
    def typed(self) -> bool:
        return self.translation.accepted

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


def semantic_errors(language_root: Path, program: str, expect: dict[str, Any]) -> list[str]:
    language = load_language(language_root)
    language.load_program(program)
    errors = []
    for binding, fields in expect.get("bindings", {}).items():
        actual = to_json(language.session.value(binding))
        for name, expected in fields.items():
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


def run_case(
    client: ChatClient, model: str, root: Path, spec: dict, case: dict, repairs: int
) -> CaseResult:
    language = load_language(root)
    examples = [(root / e).read_text(encoding="utf-8") for e in spec.get("examples", [])]
    translation = translate(
        client, model, language, case["request"], examples=examples, max_repairs=repairs
    )
    result = CaseResult(language.name, case["id"], model, translation)
    if not translation.accepted:
        return result
    result.semantic_errors = semantic_errors(root, translation.program, case.get("expect", {}))
    try:
        run_procedure(
            load_language(root),
            translation.program,
            mode="dry-run",
            out_dir=Path("sortie") / "benchmark-llm" / "runs",
            environment=case.get("environment", {}),
            max_steps=200,
        )
        result.executed = True
    except Exception as exc:  # l'échec d'exécution est une mesure, pas une erreur du banc
        result.execution_error = f"{type(exc).__name__}: {exc}"
    return result


def run_benchmark(
    client: ChatClient, models: list[str], languages: list[Path], *, repairs: int = 2, log=print
) -> list[CaseResult]:
    results = []
    for root in languages:
        spec = json.loads((root / "benchmark.json").read_text(encoding="utf-8"))
        for model in models:
            for case in spec["cases"]:
                r = run_case(client, model, root, spec, case, repairs)
                mark = "✓" if r.correct and r.executed else ("~" if r.typed else "✗")
                log(
                    f"  {mark} {model:<14} {r.language}/{r.case}  {r.seconds:5.1f} s  "
                    f"{len(r.translation.attempts)} essai(s)  {'; '.join(r.semantic_errors)[:90]}"
                )
                results.append(r)
    return results


def summary(results: list[CaseResult]) -> str:
    models = list(dict.fromkeys(r.model for r in results))
    lines = [
        "| Modèle | Cas | Parsé (1er essai) | Typé (1er essai) | Typé (après réparations) "
        "| **Correct** | Exécuté | Essais moy. | Temps moy. | Jetons générés moy. | Jetons/s |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model in models:
        rs = [r for r in results if r.model == model]
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
            f"| {pct(sum(r.typed_first for r in rs))} | {pct(sum(r.typed for r in rs))} "
            f"| **{pct(sum(r.correct for r in rs))}** | {pct(sum(r.executed for r in rs))} "
            f"| {sum(len(r.translation.attempts) for r in rs) / n:.2f} "
            f"| {sum(r.seconds for r in rs) / n:.1f} s | {sum(r.output_tokens for r in rs) // n} "
            f"| {sum(tps) / len(tps) if tps else 0:.0f} |"
        )
    return "\n".join(lines)
