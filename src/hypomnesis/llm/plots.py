"""Charts for the LLM benchmark, drawn from its ``resultats-*.json`` files.

Three layers, so each can be tested alone:

1. :func:`load_results` reads a results file and fills the fields that older runs lack;
2. pure series functions (``accuracy_*``, ``cost_by_label``) compute the plotted numbers —
   no matplotlib, no I/O;
3. one function per figure draws a :class:`~matplotlib.figure.Figure`; :func:`render_all`
   writes them as PNG and SVG.

Figures are built on the object-oriented API with an explicit ``Agg`` canvas: nothing is
displayed, no GUI backend is imported, and the pyplot global state is never touched.
"""

from __future__ import annotations

import json
import math
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

matplotlib.use("Agg")

Result = dict[str, Any]

SPLIT_ORDER = ("dev", "test", "hard")
Z_95 = 1.959963984540054


class ResultsError(ValueError):
    """A results file is unreadable or does not have the expected shape."""


# ---------------------------------------------------------------- loading


def normalize(raw: Mapping[str, Any]) -> Result:
    """One result row with every field the charts read, tolerating older result files.

    Runs predating prompting strategies have no ``strategy``/``split``/``correct_first``:
    they are the default strategy on the ``dev`` split, and a case counts as right on its
    first try when it is right and needed no repair (``attempts <= 1``).
    """
    if "model" not in raw or "correct" not in raw:
        raise ResultsError("a result needs at least the keys 'model' and 'correct'")
    row: Result = dict(raw)
    row["model"] = str(row["model"])
    row["correct"] = bool(row["correct"])
    row["strategy"] = str(row.get("strategy") or "")
    row["split"] = str(row.get("split") or "dev")
    row.setdefault("language", "")
    row.setdefault("case", "")
    row.setdefault("executed", False)
    if "correct_first" not in row:
        row["correct_first"] = row["correct"] and row.get("attempts", 1) <= 1
    row["correct_first"] = bool(row["correct_first"])
    row["seconds"] = float(row.get("seconds") or 0.0)
    row["output_tokens"] = int(row.get("output_tokens") or 0)
    row["tokens_per_second"] = float(row.get("tokens_per_second") or 0.0)
    row["label"] = f"{row['model']} · {row['strategy']}" if row["strategy"] else row["model"]
    return row


def load_results(path: Path) -> list[Result]:
    """Read a ``resultats-*.json`` file (a list of ``CaseResult.to_json()``)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResultsError(f"{path}: {exc}") from exc
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ResultsError(f"{path}: expected a JSON list of result objects")
    return [normalize(row) for row in data]


# ---------------------------------------------------------------- series


@dataclass(frozen=True)
class Rate:
    """A proportion ``successes / total`` with its 95 % Wilson interval."""

    successes: int
    total: int
    low: float
    high: float

    @property
    def value(self) -> float:
        return self.successes / self.total if self.total else 0.0


def wilson_interval(successes: int, total: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval of a binomial proportion (``(0, 0)`` when ``total`` is 0)."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    low = 0.0 if successes == 0 else min(p, max(0.0, centre - half))
    high = 1.0 if successes == total else max(p, min(1.0, centre + half))
    return (low, high)


def rate(successes: int, total: int) -> Rate:
    low, high = wilson_interval(successes, total)
    return Rate(successes, total, low, high)


def ordered_labels(results: Sequence[Result]) -> list[str]:
    """Model/strategy labels in order of first appearance."""
    return list(dict.fromkeys(r["label"] for r in results))


def ordered_splits(results: Sequence[Result]) -> list[str]:
    """Splits present, ``dev``, ``test``, ``hard`` first, others alphabetically after."""
    present = {r["split"] for r in results}
    known = [s for s in SPLIT_ORDER if s in present]
    return known + sorted(present - set(SPLIT_ORDER))


def accuracy_by_label(results: Sequence[Result], key: str) -> dict[str, Rate]:
    """Share of cases whose boolean field ``key`` holds, per model/strategy label."""
    out: dict[str, Rate] = {}
    for label in ordered_labels(results):
        rows = [r for r in results if r["label"] == label]
        out[label] = rate(sum(1 for r in rows if r[key]), len(rows))
    return out


def accuracy_by_split(results: Sequence[Result], key: str) -> dict[str, dict[str, Rate]]:
    """Like :func:`accuracy_by_label`, for each split: ``{split: {label: Rate}}``."""
    return {
        split: accuracy_by_label([r for r in results if r["split"] == split], key)
        for split in ordered_splits(results)
    }


def cost_by_label(results: Sequence[Result], key: str) -> dict[str, tuple[float, float]]:
    """Mean and standard error of a numeric per-case field (``seconds``, ``output_tokens``)."""
    out: dict[str, tuple[float, float]] = {}
    for label in ordered_labels(results):
        values = [float(r[key]) for r in results if r["label"] == label]
        error = statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
        out[label] = (statistics.fmean(values), error)
    return out


# ---------------------------------------------------------------- figures

FIRST_COLOR = "#4c78a8"
REPAIRED_COLOR = "#f58518"


def _new_figure(width: float, height: float, ncols: int = 1) -> tuple[Figure, list[Any]]:
    figure = Figure(figsize=(width, height))
    FigureCanvasAgg(figure)
    return figure, list(figure.subplots(1, ncols, squeeze=False)[0])


def _tilt(axes: Any) -> None:
    for tick in axes.get_xticklabels():
        tick.set_rotation(20)
        tick.set_horizontalalignment("right")


def _rate_bars(
    axes: Any, rates: Mapping[str, Rate], offset: float, width: float, color: str, name: str
) -> None:
    labels = list(rates)
    values = [rates[label].value for label in labels]
    below = [v - rates[label].low for v, label in zip(values, labels, strict=True)]
    above = [rates[label].high - v for v, label in zip(values, labels, strict=True)]
    axes.bar(
        [i + offset for i in range(len(labels))],
        values,
        width,
        yerr=[below, above],
        capsize=3,
        color=color,
        label=name,
    )


def accuracy_figure(results: Sequence[Result]) -> Figure:
    """Right on the first try vs after repairs, per model/strategy, with Wilson intervals."""
    first = accuracy_by_label(results, "correct_first")
    repaired = accuracy_by_label(results, "correct")
    figure, [axes] = _new_figure(max(6.0, 1.6 * len(first) + 2), 4.5)
    _rate_bars(axes, first, -0.2, 0.4, FIRST_COLOR, "premier essai")
    _rate_bars(axes, repaired, 0.2, 0.4, REPAIRED_COLOR, "après réparations")
    axes.set_xticks(range(len(first)), list(first))
    _tilt(axes)
    axes.set_ylim(0, 1.05)
    axes.set_ylabel("cas justes (IC de Wilson à 95 %)")
    axes.set_title(f"Justesse par modèle ({len(results)} résultats)")
    axes.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    figure.tight_layout()
    return figure


def accuracy_by_split_figure(results: Sequence[Result]) -> Figure:
    """One panel per measure (first try, after repairs); bars grouped by split."""
    labels = ordered_labels(results)
    splits = ordered_splits(results)
    figure, panels = _new_figure(max(7.0, 1.4 * len(splits) * len(labels) + 2), 4.5, 2)
    width = 0.8 / max(len(labels), 1)
    for axes, key, title in zip(
        panels, ("correct_first", "correct"), ("premier essai", "après réparations"), strict=True
    ):
        by_split = accuracy_by_split(results, key)
        for i, label in enumerate(labels):
            rates = {s: by_split[s][label] for s in splits if label in by_split[s]}
            offset = (i - (len(labels) - 1) / 2) * width
            positions = [splits.index(s) + offset for s in rates]
            axes.bar(
                positions,
                [r.value for r in rates.values()],
                width,
                yerr=[
                    [r.value - r.low for r in rates.values()],
                    [r.high - r.value for r in rates.values()],
                ],
                capsize=2,
                label=label,
            )
        axes.set_xticks(range(len(splits)), splits)
        axes.set_ylim(0, 1.05)
        axes.set_title(title)
    panels[0].set_ylabel("cas justes (IC de Wilson à 95 %)")
    panels[1].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize="small")
    figure.suptitle("Justesse par jeu de cas")
    figure.tight_layout()
    return figure


def cost_figure(results: Sequence[Result]) -> Figure:
    """Mean seconds and mean generated tokens per case, per model/strategy (± std. error)."""
    figure, panels = _new_figure(max(8.0, 3.0 * len(ordered_labels(results)) + 2), 4.5, 2)
    for axes, key, title, color in (
        (panels[0], "seconds", "temps par cas (s)", FIRST_COLOR),
        (panels[1], "output_tokens", "jetons générés par cas", REPAIRED_COLOR),
    ):
        costs = cost_by_label(results, key)
        axes.bar(
            range(len(costs)),
            [mean for mean, _ in costs.values()],
            yerr=[error for _, error in costs.values()],
            capsize=3,
            color=color,
        )
        axes.set_xticks(range(len(costs)), list(costs))
        _tilt(axes)
        axes.set_title(title)
    figure.tight_layout()
    return figure


FIGURES: dict[str, Callable[[Sequence[Result]], Figure]] = {
    "justesse": accuracy_figure,
    "justesse-par-jeu": accuracy_by_split_figure,
    "cout": cost_figure,
}


def render_all(results: Sequence[Result], directory: Path, stem: str = "graphiques") -> list[Path]:
    """Write every figure as ``<stem>-<figure>.png`` and ``.svg`` in ``directory``.

    Returns the written paths (empty when there are no results). SVG text is kept as text
    rather than outlines, so labels stay searchable and editable.
    """
    if not results:
        return []
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with matplotlib.rc_context({"svg.fonttype": "none"}):
        for name, draw in FIGURES.items():
            figure = draw(results)
            for extension in ("png", "svg"):
                path = directory / f"{stem}-{name}.{extension}"
                figure.savefig(path, dpi=150)
                written.append(path)
    return written
