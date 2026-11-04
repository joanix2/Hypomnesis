"""Traduction langage naturel → programme M1 et banc d'essai, avec un faux LLM."""

import re
import shutil
from pathlib import Path

import pytest

from hypomnesis.engine.language import MissingDescriptionError, load_language
from hypomnesis_codegen.benchmark import run_benchmark, semantic_errors, summary
from hypomnesis_codegen.ollama import Reply
from hypomnesis_codegen.prompting import BASE
from hypomnesis_codegen.translation import extract_code, system_prompt, translate

ROOT = Path(__file__).resolve().parents[3]
MECANIQUE = ROOT / "demo" / "languages" / "mecanique"
VENTILATION = ROOT / "demo" / "languages" / "ventilation"
GOOD = (
    'let demande = { Plaque.nom = "p"; largeur = 120.0; hauteur = 80.0; '
    "epaisseur = Some 4.0; masse_max = 0.5 }\n"
    "let procedure = Plaque.concevoir demande Plaque.estimateur_regle\n"
)


class FakeLLM:
    """Rend les réponses prévues, dans l'ordre, et garde les messages reçus."""

    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.calls: list[list[dict[str, str]]] = []
        self.temperatures: list[float] = []

    def chat(self, model, messages, *, num_ctx=16384, temperature=0.0):
        self.calls.append(messages)
        self.temperatures.append(temperature)
        return Reply(self.answers.pop(0), 0.1, 10, 100.0)


def test_extract_code_drops_markdown_and_reasoning():
    assert extract_code("```ocaml\nlet x = 1\n```\nVoilà.") == "let x = 1\n"
    assert extract_code("Okay, let's think…\n</think>\n\nlet x = 1") == "let x = 1\n"


def test_default_prompt_is_the_generated_catalogue_with_similar_examples():
    llm = FakeLLM(GOOD)
    translate(
        llm, "m", load_language(MECANIQUE), "plaque 120 x 80 mm, 0,5 kg", examples=["(* exemple *)"]
    )
    system = llm.calls[0][0]["content"]
    assert "=== Catalogue du langage « mecanique »" in system and "let procedure" in system
    assert "module Plaque" not in system and "(* exemple *)" not in system
    assert len(llm.calls[0]) == 2 + 5 * 2  # system, five worked examples, the request


def test_historical_prompt_is_the_raw_source_and_example_programs():
    llm = FakeLLM(GOOD)
    translate(
        llm, "m", load_language(MECANIQUE), "plaque", examples=["(* exemple *)"], strategy=BASE
    )
    system = llm.calls[0][0]["content"]
    assert "module Plaque" in system and "(* exemple *)" in system and "let procedure" in system


def test_an_undocumented_language_falls_back_on_its_source(tmp_path):
    shutil.copytree(VENTILATION, tmp_path / "ventilation")
    source = tmp_path / "ventilation" / "ventilation.hyp"
    source.write_text(re.sub(r"\(\*\*.*?\*\)", "", source.read_text(encoding="utf-8"), flags=re.S))
    language = load_language(tmp_path / "ventilation", strict=False)
    assert "module Ventilation" in system_prompt(language, [])
    with pytest.raises(MissingDescriptionError):
        load_language(tmp_path / "ventilation")


def test_compiler_diagnostics_drive_the_repair():
    llm = FakeLLM("let demande = { Plaque.nom = 1 }", GOOD)
    result = translate(llm, "m", load_language(MECANIQUE), "plaque", examples=[])
    assert result.accepted and len(result.attempts) == 2
    assert "type error" in result.attempts[0].stage
    assert "Le compilateur refuse" in llm.calls[1][-1]["content"]


def test_repairs_are_bounded():
    llm = FakeLLM("n'importe quoi", "toujours pas", "encore")
    result = translate(llm, "m", load_language(MECANIQUE), "plaque", examples=[], max_repairs=2)
    assert not result.accepted and len(result.attempts) == 3


def test_semantic_check_catches_invented_values():
    errors = semantic_errors(
        MECANIQUE, GOOD, {"bindings": {"demande": {"epaisseur": {"tag": "None"}}}}
    )
    assert errors == ["demande.epaisseur = {'tag': 'Some', 'arg': 4.0}, attendu {'tag': 'None'}"]


def test_benchmark_end_to_end_with_a_fake_model(tmp_path, monkeypatch):
    spec = (
        '{"examples": [], "cases": [{"id": "c1", "request": "plaque", '
        '"expect": {"bindings": {"demande": {"largeur": 120.0, '
        '"epaisseur": {"tag": "Some", "arg": 4.0}}}}}]}'
    )
    language = tmp_path / "mecanique"
    shutil.copytree(MECANIQUE, language)  # copie réelle : les adaptateurs restent dans le paquet
    (language / "benchmark.json").write_text(spec)
    monkeypatch.chdir(tmp_path)
    results = run_benchmark(FakeLLM(GOOD), ["faux"], [language], log=lambda _: None)
    assert results[0].correct and results[0].executed
    assert "| faux | 1 |" in summary(results)


def test_inline_record_counts_as_the_expected_binding():
    inline = (
        "let procedure = Plaque.concevoir\n"
        '  { Plaque.nom = "p"; largeur = 160.0; hauteur = 90.0; epaisseur = None;'
        " masse_max = 0.6 }\n"
        "  Plaque.estimateur_regle\n"
    )
    expect = {"bindings": {"demande": {"largeur": 160.0, "epaisseur": {"tag": "None"}}}}
    assert semantic_errors(MECANIQUE, inline, expect) == []
    wrong = {"bindings": {"demande": {"largeur": 999.0}}}
    assert semantic_errors(MECANIQUE, inline, wrong) == ["demande.largeur = 160.0, attendu 999.0"]


def test_missing_binding_is_a_semantic_error_not_a_crash():
    no_record = "let procedure = Effect.return 0\n"
    errors = semantic_errors(MECANIQUE, no_record, {"bindings": {"demande": {"largeur": 1.0}}})
    assert errors == ["le programme ne définit pas `demande`"]


def test_missing_entry_point_says_what_to_write():
    llm = FakeLLM(
        'let demande = { Plaque.nom = "p"; largeur = 1.0; hauteur = 1.0; '
        "epaisseur = None; masse_max = 1.0 }\n",
        GOOD,
    )
    result = translate(llm, "m", load_language(MECANIQUE), "plaque", examples=[])
    assert result.accepted
    assert "`procedure` n'est pas défini" in result.attempts[0].error
    assert "let procedure = " in llm.calls[1][-1]["content"]


def test_prose_answer_is_told_to_return_code_only_and_the_diagnostic_stays_short():
    prose = "Okay, let's tackle this problem. " + "blah " * 200
    llm = FakeLLM(prose, GOOD)
    result = translate(llm, "m", load_language(MECANIQUE), "plaque", examples=[])
    feedback = llm.calls[1][-1]["content"]
    assert "n'est pas un programme" in feedback
    assert len(feedback) < 600 and result.accepted


def test_simulation_failure_is_fed_back_to_the_model():
    runs = []

    def simulate(program: str) -> str:
        runs.append(program)
        return "boom : prémisses inconnues" if len(runs) == 1 else ""

    llm = FakeLLM(GOOD, GOOD)
    result = translate(llm, "m", load_language(MECANIQUE), "plaque", examples=[], simulate=simulate)
    assert result.accepted and len(result.attempts) == 2
    assert result.attempts[0].stage == "runtime error" and result.compiled
    assert "échoue à l'exécution" in llm.calls[1][-1]["content"]
    assert "boom" in llm.calls[1][-1]["content"]


def test_recorded_mvp_response_is_checked_without_running_it(monkeypatch):
    from hypomnesis.language.parser import parse_program
    from hypomnesis.session import Session, prelude_source

    program = (ROOT / "demo/programs/mecanique/plaque_120x80.hyp").read_text()
    language = load_language(MECANIQUE, execute=False)

    original = Session.load_program
    trusted_prelude = parse_program(prelude_source())

    def forbidden(self, candidate):
        assert candidate == trusted_prelude, "M2 or candidate evaluated during compilation"
        return original(self, candidate)

    monkeypatch.setattr(Session, "load_program", forbidden)
    result = translate(
        FakeLLM(program),
        "fixture",
        language,
        "Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité "
        "et exporte sa géométrie.",
        examples=[],
        max_repairs=0,
    )
    assert result.compiled and result.accepted
    assert "epaisseur = None" in result.program


def test_runtime_failure_is_not_executed_by_the_compiler():
    from hypomnesis_codegen.translation import check

    assert check(MECANIQUE, "let _ = 1 / 0\nlet procedure = Effect.return 0") == ("", "")


def test_python_is_not_an_accepted_program(tmp_path):
    target = tmp_path / "must_not_exist"
    code = f"import pathlib\npathlib.Path({str(target)!r}).touch()\n"
    result = translate(
        FakeLLM(code), "fixture", load_language(MECANIQUE), "plaque", examples=[], max_repairs=0
    )
    assert not result.accepted and result.attempts[0].stage == "syntax error"
    assert not target.exists()


@pytest.mark.parametrize("budget", [-1, True, 1.5, "2"])
def test_invalid_repair_budget_is_rejected_before_a_model_call(budget):
    client = FakeLLM(GOOD)
    with pytest.raises(ValueError, match="max_repairs"):
        translate(client, "m", load_language(MECANIQUE), "x", examples=[], max_repairs=budget)
    assert not client.calls
