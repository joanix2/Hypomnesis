"""Banc LLM (HYP-139) : intervalles de Wilson, temps hors chargement, répétitions."""

import json
import shutil

import pytest

from hypomnesis_codegen.benchmark import REPEAT_TEMPERATURE, run_benchmark, summary, wilson
from hypomnesis_codegen.ollama import Reply
from hypomnesis_codegen.plots import cost_by_label, normalize
from test_llm import GOOD, MECANIQUE, FakeLLM

BAD = "let demande = { Plaque.nom = 1 }"
EXPECT = {"bindings": {"demande": {"largeur": 120.0}}}


class TimedLLM(FakeLLM):
    """Like FakeLLM, but each reply takes 2 s of which 0.5 s is model loading."""

    def chat(self, model, messages, *, num_ctx=16384, temperature=0.0):
        reply = super().chat(model, messages, num_ctx=num_ctx, temperature=temperature)
        return Reply(reply.text, 2.0, 10, 100.0, load_seconds=0.5)


@pytest.fixture
def language(tmp_path, monkeypatch):
    root = tmp_path / "mecanique"
    shutil.copytree(MECANIQUE, root)
    cases = [{"id": f"c{i}", "request": "plaque", "expect": EXPECT} for i in (1, 2)]
    (root / "benchmark.json").write_text(json.dumps({"examples": [], "cases": cases}))
    monkeypatch.chdir(tmp_path)
    return root


def test_wilson_known_values():
    low, high = wilson(5, 10)
    assert (low, high) == (pytest.approx(0.2366, abs=1e-3), pytest.approx(0.7634, abs=1e-3))
    low, high = wilson(0, 10)
    assert low == pytest.approx(0.0, abs=1e-12) and 0.25 < high < 0.35
    low, high = wilson(10, 10)
    assert high == pytest.approx(1.0, abs=1e-12) and 0.65 < low < 0.75
    assert wilson(0, 0) == (0.0, 0.0)


def test_summary_reports_intervals_repairs_and_time_without_loading(language):
    llm = TimedLLM(GOOD, BAD, GOOD)  # c1 right at once, c2 needs one repair
    results = run_benchmark(llm, ["faux"], [language], log=lambda _: None)
    assert [r.correct_first for r in results] == [True, False]
    assert all(r.correct for r in results)
    assert results[1].seconds == 4.0 and results[1].seconds_without_load == 3.0
    table = summary(results).splitlines()
    header, row = table[0], table[2]
    for column in ("Typé (1er essai)", "Correct (1er essai)", "Cas réparés", "hors chargement"):
        assert column in header
    low, high = wilson(1, 2)
    assert f"1/2 (50 %) [{100 * low:.0f}-{100 * high:.0f} %]" in row
    low, high = wilson(2, 2)
    assert f"2/2 (100 %) [{100 * low:.0f}-{100 * high:.0f} %]" in row
    assert "| 3.0 s | 2.2 s |" in row  # mean total 3.0 s, mean without loading 2.25 s
    assert "Cas stables" not in "\n".join(table)  # nothing repeated: no second table


def test_json_distinguishes_total_and_loading_time(language):
    [first, _] = run_benchmark(TimedLLM(GOOD, GOOD), ["faux"], [language], log=lambda _: None)
    row = first.to_json()
    assert (row["seconds"], row["load_seconds"], row["seconds_without_load"]) == (2.0, 0.5, 1.5)
    assert (row["repetition"], row["temperature"]) == (0, 0.0)


def test_repetitions_sample_above_zero_and_aggregate(language):
    llm = FakeLLM(GOOD, GOOD, BAD, GOOD, GOOD, GOOD, GOOD)
    results = run_benchmark(llm, ["faux"], [language], repetitions=3, log=lambda _: None)
    assert len(results) == 2 * 3
    assert [r.repetition for r in results] == [0, 1, 2, 0, 1, 2]
    assert {r.temperature for r in results} == {REPEAT_TEMPERATURE}
    assert set(llm.temperatures) == {REPEAT_TEMPERATURE}
    table = summary(results)
    low, high = wilson(5, 6)
    assert f"5/6 (83 %) [{100 * low:.0f}-{100 * high:.0f} %]" in table
    repeated = table.split("\n\n")[1]
    assert "| faux | 2 | 3 | 0.7 | 83 % | 1/2 |" in repeated  # c1 unstable, c2 stable


def test_single_run_stays_deterministic_and_temperature_is_overridable(language):
    llm = FakeLLM(GOOD, GOOD)
    run_benchmark(llm, ["faux"], [language], log=lambda _: None)
    assert llm.temperatures == [0.0, 0.0]
    llm = FakeLLM(GOOD, GOOD, GOOD, GOOD)
    run_benchmark(llm, ["faux"], [language], repetitions=2, temperature=0.3, log=lambda _: None)
    assert set(llm.temperatures) == {0.3}
    with pytest.raises(ValueError):
        run_benchmark(FakeLLM(), ["faux"], [language], repetitions=0)


def test_plots_read_the_loading_time_and_tolerate_older_results():
    new = normalize(
        {
            "model": "m",
            "correct": True,
            "seconds": 4.0,
            "load_seconds": 1.0,
            "seconds_without_load": 3.0,
        }
    )
    assert (new["load_seconds"], new["seconds_without_load"]) == (1.0, 3.0)
    old = normalize({"model": "m", "correct": True, "seconds": 4.0})
    assert (old["load_seconds"], old["seconds_without_load"]) == (0.0, 4.0)
    assert cost_by_label([new], "seconds_without_load")["m"][0] == 3.0
