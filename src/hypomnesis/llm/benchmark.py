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

from scipy.stats import binomtest

from hypomnesis.engine.bridge import to_json
from hypomnesis.engine.language import Language, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.language import ast as A
from hypomnesis.language.errors import HypomnesisError, Span
from hypomnesis.language.parser import parse_program
from hypomnesis.llm.prompting import DEFAULT, Strategy
from hypomnesis.llm.translation import ChatClient, Translation, translate

ANY = "*"
REPEAT_TEMPERATURE = 0.7  # default sampling temperature once a case is repeated


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
    repetition: int = 0  # index of this trial among the repetitions of the same case
    temperature: float = 0.0  # sampling temperature (0: deterministic, repeating is useless)

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

    @property
    def load_seconds(self) -> float:
        return sum(a.reply.load_seconds for a in self.translation.attempts)

    @property
    def seconds_without_load(self) -> float:
        """Total time minus the model load time (the cost of the translation itself)."""
        return max(0.0, self.seconds - self.load_seconds)

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
            "repetition": self.repetition,
            "temperature": self.temperature,
            "seconds": round(self.seconds, 2),
            "load_seconds": round(self.load_seconds, 2),
            "seconds_without_load": round(self.seconds_without_load, 2),
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
    strategy: Strategy = DEFAULT,
    *,
    temperature: float = 0.0,
    repetition: int = 0,
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
        temperature=temperature,
    )
    result = CaseResult(
        language.name,
        case["id"],
        model,
        translation,
        strategy="" if strategy == DEFAULT else str(strategy),
        split=case.get("split", "dev"),
        repetition=repetition,
        temperature=temperature,
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
    strategy: Strategy = DEFAULT,
    splits: Sequence[str] | None = None,
    repetitions: int = 1,
    temperature: float | None = None,
    log=print,
) -> list[CaseResult]:
    """Run every selected case ``repetitions`` times per model.

    At temperature 0 trials of a case are identical, so ``repetitions > 1`` samples at
    ``temperature`` (default ``REPEAT_TEMPERATURE``); a single run defaults to 0."""
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if temperature is None:
        temperature = REPEAT_TEMPERATURE if repetitions > 1 else 0.0
    results = []
    for root in languages:
        spec = json.loads((root / "benchmark.json").read_text(encoding="utf-8"))
        for model in models:
            for case in spec["cases"]:
                if splits is not None and case.get("split", "dev") not in splits:
                    continue
                for repetition in range(repetitions):
                    r = run_case(
                        client,
                        model,
                        root,
                        spec,
                        case,
                        repairs,
                        strategy,
                        temperature=temperature,
                        repetition=repetition,
                    )
                    mark = "✓" if r.correct and r.executed else ("~" if r.typed else "✗")
                    again = f"#{repetition + 1} " if repetitions > 1 else ""
                    log(
                        f"  {mark} {model:<14} {r.language}/{r.case} {again}"
                        f"{r.seconds:5.1f} s ({r.seconds_without_load:.1f} s hors chargement)  "
                        f"{len(r.translation.attempts)} essai(s)  "
                        f"{'; '.join(r.semantic_errors)[:90]}"
                    )
                    results.append(r)
    return results


def wilson(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score interval of ``k`` successes out of ``n`` trials (``(0, 0)`` when ``n`` is 0)."""
    if n == 0:
        return (0.0, 0.0)
    interval = binomtest(k, n).proportion_ci(confidence_level=confidence, method="wilson")
    return (interval.low, interval.high)


def repetition_table(results: list[CaseResult]) -> str:
    """Per model, how repeated trials of the same case agree (empty when nothing is repeated)."""
    if not any(r.repetition for r in results):
        return ""
    lines = [
        "| Modèle | Cas distincts | Essais par cas | Température "
        "| Correct 1er essai moy. par cas | Cas stables (même issue à chaque essai) |",
        "|---|---|---|---|---|---|",
    ]
    for model in dict.fromkeys(r.label for r in results):
        by_case: dict[tuple[str, str], list[CaseResult]] = {}
        for r in results:
            if r.label == model:
                by_case.setdefault((r.language, r.case), []).append(r)
        rates = [sum(r.correct_first for r in rs) / len(rs) for rs in by_case.values()]
        stable = sum(1 for rate in rates if rate in (0.0, 1.0))
        trials = max(len(rs) for rs in by_case.values())
        temperatures = sorted({r.temperature for rs in by_case.values() for r in rs})
        lines.append(
            f"| {model} | {len(by_case)} | {trials} | {', '.join(f'{t:g}' for t in temperatures)} "
            f"| {100 * sum(rates) / len(rates):.0f} % | {stable}/{len(by_case)} |"
        )
    return "\n".join(lines)


def summary(results: list[CaseResult]) -> str:
    """Markdown table per model: parsed / typed / correct (first try and final, with 95 % Wilson
    intervals), repaired cases, mean time with and without model loading, then — when cases
    were repeated — a table of agreement between trials."""
    models = list(dict.fromkeys(r.label for r in results))
    lines = [
        "| Modèle | Cas | Parsé (1er essai) | Typé (1er essai) | **Correct (1er essai)** "
        "| Typé (après réparations) | **Correct** | Exécuté | Cas réparés | Essais moy. "
        "| Temps moy. | Temps moy. hors chargement | Jetons générés moy. | Jetons/s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model in models:
        rs = [r for r in results if r.label == model]
        n = len(rs)

        def pct(k: int, n: int = n) -> str:
            return f"{k}/{n} ({100 * k // n} %)"

        def pct_ci(k: int, n: int = n) -> str:
            low, high = wilson(k, n)
            return f"{pct(k)} [{100 * low:.0f}-{100 * high:.0f} %]"

        tps = [
            a.reply.tokens_per_second
            for r in rs
            for a in r.translation.attempts
            if a.reply.tokens_per_second
        ]
        lines.append(
            f"| {model} | {n} | {pct(sum(r.parsed_first for r in rs))} "
            f"| {pct(sum(r.typed_first for r in rs))} "
            f"| **{pct_ci(sum(r.correct_first for r in rs))}** | {pct(sum(r.typed for r in rs))} "
            f"| **{pct_ci(sum(r.correct for r in rs))}** | {pct(sum(r.executed for r in rs))} "
            f"| {sum(len(r.translation.attempts) > 1 for r in rs)} "
            f"| {sum(len(r.translation.attempts) for r in rs) / n:.2f} "
            f"| {sum(r.seconds for r in rs) / n:.1f} s "
            f"| {sum(r.seconds_without_load for r in rs) / n:.1f} s "
            f"| {sum(r.output_tokens for r in rs) // n} "
            f"| {sum(tps) / len(tps) if tps else 0:.0f} |"
        )
    repeated = repetition_table(results)
    return "\n".join(lines) + (f"\n\n{repeated}" if repeated else "")
