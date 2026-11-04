"""Stratégies de prompt, exemples de travail et recherche d'exemples similaires (RAG)."""

import json
import shutil
from pathlib import Path

import pytest

from hypomnesis.engine.language import LanguageError, load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.llm.prompting import BASE, Strategy
from hypomnesis.llm.retrieval import Retriever, load_examples
from hypomnesis.llm.translation import shots, system_prompt

LANGUAGES = Path(__file__).resolve().parents[2] / "languages"
NAMES = ["mecanique", "ventilation"]


def test_strategy_spec_parsing_and_printing():
    assert Strategy.parse("base") == BASE and str(BASE) == "source+programmes"
    s = Strategy.parse("catalogue+rag3")
    assert (s.source, s.catalogue, s.programs, s.shots, s.retrieval) == (
        False,
        True,
        False,
        3,
        True,
    )
    assert str(s) == "catalogue+rag3"
    assert Strategy.parse("source+tirs2").retrieval is False
    with pytest.raises(ValueError, match="inconnu"):
        Strategy.parse("catalogue+magie")


def test_system_prompt_follows_the_strategy():
    language = load_language(LANGUAGES / "mecanique")
    only_catalogue = system_prompt(language, ["(* exemple *)"], Strategy.parse("catalogue"))
    assert "=== Catalogue du langage" in only_catalogue
    assert "module Plaque" not in only_catalogue and "(* exemple *)" not in only_catalogue
    base = system_prompt(language, ["(* exemple *)"], BASE)
    assert "module Plaque" in base and "(* exemple *)" in base and "Catalogue" not in base


def test_retrieval_puts_the_most_similar_example_last_and_ignores_numbers():
    language = load_language(LANGUAGES / "mecanique")
    request = (
        "Conçois une plaque de 11 × 22 mm, 3 kg max, puis contrôle l'épaisseur au pied à coulisse."
    )
    last = Retriever(load_examples(language)).top(request, 3)[-1]
    assert "concevoir_puis_mesurer" in last.program


def test_shots_are_alternating_chat_turns():
    language = load_language(LANGUAGES / "mecanique")
    turns = shots(language, "plaque 10x10 1kg", Strategy.parse("rag2"))
    assert [t["role"] for t in turns] == ["user", "assistant", "user", "assistant"]
    assert turns[1]["content"].startswith("let demande")
    assert shots(language, "plaque", BASE) == []


@pytest.mark.parametrize("name", NAMES)
def test_examples_file_is_validated_by_its_schema(name, tmp_path):
    shutil.copytree(LANGUAGES / name, tmp_path / name)
    (tmp_path / name / "exemples.json").write_text('[{"request": "x"}]', encoding="utf-8")
    with pytest.raises(LanguageError, match="exemples invalides"):
        load_examples(load_language(tmp_path / name))


@pytest.mark.parametrize("name", NAMES)
def test_every_shipped_example_compiles_and_runs(name, tmp_path):
    root = LANGUAGES / name
    for example in load_examples(load_language(root)):
        run_procedure(
            load_language(root),
            example.program,
            mode="dry-run",
            out_dir=tmp_path,
            environment=example.environment,
            max_steps=200,
        )


@pytest.mark.parametrize("name", NAMES)
def test_examples_never_repeat_a_benchmark_request(name):
    root = LANGUAGES / name
    benchmark = json.loads((root / "benchmark.json").read_text(encoding="utf-8"))
    asked = {case["request"].strip().lower() for case in benchmark["cases"]}
    shipped = {e.request.strip().lower() for e in load_examples(load_language(root))}
    assert not asked & shipped
