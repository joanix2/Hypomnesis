"""LLM benchmark charts: loader, series and figures, on synthetic results (no network, no GPU)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.llm.plots import (
    ResultsError,
    accuracy_by_label,
    accuracy_by_split,
    cost_by_label,
    load_results,
    normalize,
    render_all,
    wilson_interval,
)


def row(model: str, split: str, correct: bool, first: bool, **extra: object) -> dict[str, object]:
    return {
        "language": "ventilation",
        "case": "c",
        "model": model,
        "strategy": "catalogue+rag5",
        "split": split,
        "correct": correct,
        "correct_first": first,
        "executed": correct,
        "attempts": 1 if first else 2,
        "seconds": 2.0,
        "output_tokens": 100,
        "tokens_per_second": 50.0,
        **extra,
    }


def synthetic() -> list[dict[str, object]]:
    return [
        row("alpha:1b", "dev", True, True),
        row("alpha:1b", "dev", True, False, seconds=6.0, output_tokens=300),
        row("alpha:1b", "test", False, False),
        row("alpha:1b", "hard", False, False),
        row("beta:4b", "dev", True, True),
        row("beta:4b", "test", True, True),
        row("beta:4b", "hard", True, False),
        row("beta:4b", "hard", False, False),
    ]


@pytest.fixture
def results_file(tmp_path: Path) -> Path:
    path = tmp_path / "resultats-20260101-000000.json"
    path.write_text(json.dumps(synthetic()), encoding="utf-8")
    return path


def test_wilson_interval_known_values():
    low, high = wilson_interval(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-3)
    assert high == pytest.approx(0.7634, abs=1e-3)
    assert wilson_interval(0, 0) == (0.0, 0.0)
    low, high = wilson_interval(10, 10)
    assert high == 1.0
    assert 0.65 < low < 0.75


def test_wilson_interval_contains_the_proportion():
    for total in range(1, 30):
        for successes in range(total + 1):
            low, high = wilson_interval(successes, total)
            assert 0.0 <= low <= successes / total <= high <= 1.0 + 1e-12


def test_loader_reads_rows_and_labels(results_file: Path):
    rows = load_results(results_file)
    assert len(rows) == 8
    assert rows[0]["label"] == "alpha:1b · catalogue+rag5"


def test_loader_tolerates_old_results_without_new_fields():
    old = normalize({"model": "m", "correct": True, "attempts": 2, "seconds": 3.5})
    assert (old["strategy"], old["split"], old["label"]) == ("", "dev", "m")
    assert old["correct_first"] is False  # needed a repair
    assert normalize({"model": "m", "correct": True})["correct_first"] is True
    assert normalize({"model": "m", "correct": False})["correct_first"] is False
    assert old["output_tokens"] == 0 and old["executed"] is False


def test_loader_rejects_malformed_files(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"model": "x"}', encoding="utf-8")
    with pytest.raises(ResultsError):
        load_results(bad)
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(ResultsError):
        load_results(bad)
    bad.write_text('[{"model": "x"}]', encoding="utf-8")
    with pytest.raises(ResultsError, match="model"):
        load_results(bad)
    with pytest.raises(ResultsError):
        load_results(tmp_path / "missing.json")


def test_series_counts():
    rows = [normalize(r) for r in synthetic()]
    first = accuracy_by_label(rows, "correct_first")
    repaired = accuracy_by_label(rows, "correct")
    assert [(r.successes, r.total) for r in first.values()] == [(1, 4), (2, 4)]
    assert [(r.successes, r.total) for r in repaired.values()] == [(2, 4), (3, 4)]
    by_split = accuracy_by_split(rows, "correct")
    assert list(by_split) == ["dev", "test", "hard"]
    beta = "beta:4b · catalogue+rag5"
    assert (by_split["hard"][beta].successes, by_split["hard"][beta].total) == (1, 2)


def test_cost_series():
    rows = [normalize(r) for r in synthetic()]
    seconds = cost_by_label(rows, "seconds")
    mean, error = seconds["alpha:1b · catalogue+rag5"]
    assert mean == pytest.approx(3.0)
    assert error == pytest.approx(1.0)  # stdev([2, 6, 2, 2]) / sqrt(4)
    assert seconds["beta:4b · catalogue+rag5"] == (2.0, 0.0)
    assert cost_by_label(rows, "output_tokens")["alpha:1b · catalogue+rag5"][0] == 150.0


def test_render_all_writes_png_and_svg(results_file: Path, tmp_path: Path):
    out = tmp_path / "figures"
    written = render_all(load_results(results_file), out, "demo")
    assert {p.suffix for p in written} == {".png", ".svg"}
    assert len(written) == 6
    for path in written:
        assert path.parent == out and path.stat().st_size > 0
    assert written[0].read_bytes().startswith(b"\x89PNG")
    svg = (out / "demo-justesse.svg").read_text(encoding="utf-8")
    assert "alpha:1b" in svg and "beta:4b" in svg


def test_render_all_handles_old_results_and_empty_input(tmp_path: Path):
    old = [normalize({"model": "m", "correct": i % 2 == 0, "seconds": 1.0}) for i in range(4)]
    assert len(render_all(old, tmp_path / "old")) == 6
    assert render_all([], tmp_path / "none") == []
    assert not (tmp_path / "none").exists()


def test_matplotlib_backend_is_agg():
    import matplotlib

    assert matplotlib.get_backend().lower() == "agg"


def test_cli_graphiques_llm_command(results_file: Path, tmp_path: Path, capsys):
    out = tmp_path / "out"
    assert main(["graphiques-llm", str(results_file), "--sortie", str(out)]) == 0
    stem = results_file.stem
    assert (out / f"{stem}-justesse.png").stat().st_size > 0
    assert (out / f"{stem}-cout.svg").stat().st_size > 0
    assert "justesse.png" in capsys.readouterr().out


def test_cli_graphiques_llm_defaults_to_the_results_directory(results_file: Path):
    assert main(["graphiques-llm", str(results_file)]) == 0
    assert (results_file.parent / f"{results_file.stem}-justesse-par-jeu.png").exists()


def test_cli_graphiques_llm_refuses_bad_input(tmp_path: Path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("[1]", encoding="utf-8")
    assert main(["graphiques-llm", str(bad)]) == 1
    assert "graphiques-llm" in capsys.readouterr().err
    assert main(["graphiques-llm", str(tmp_path / "absent.json")]) == 2


class _Stub:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data

    def to_json(self) -> dict[str, object]:
        return self.data


@pytest.mark.parametrize("flag, expected", [("--graphiques", True), ("--sans-graphiques", False)])
def test_cli_benchmark_llm_figures_follow_the_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, flag: str, expected: bool
):
    import hypomnesis.llm.benchmark as benchmark

    rows = [_Stub(r) for r in synthetic()]
    monkeypatch.setattr(benchmark, "run_benchmark", lambda *args, **kwargs: rows)
    monkeypatch.setattr(benchmark, "summary", lambda results: "table")
    ventilation = Path(__file__).resolve().parents[2] / "languages" / "ventilation"
    argv = ["benchmark-llm", str(ventilation), "--modeles", "alpha:1b", "--sortie", str(tmp_path)]
    assert main([*argv, flag]) == 0
    assert bool(list(tmp_path.glob("*-justesse.png"))) is expected
    assert len(list(tmp_path.glob("resultats-*.json"))) == 1
