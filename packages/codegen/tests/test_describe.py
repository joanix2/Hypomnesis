"""Catalogue de prompt compilé depuis l'auto-documentation d'un langage."""

from pathlib import Path

import pytest

from hypomnesis.engine.language import load_language
from hypomnesis.language.docs import declarations
from hypomnesis_codegen.describe import catalogue

LANGUAGES = Path(__file__).resolve().parents[3] / "demo" / "languages"
SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"


def render(name: str) -> str:
    return catalogue(load_language(LANGUAGES / name)).render()


def test_catalogue_lists_documented_types_fields_and_tags():
    text = render("mecanique")
    assert "### Type `Plaque.demande`" in text
    assert "- `masse_max : float` — Masse maximale admissible." in text
    assert "  - Unité : kg" in text
    assert "  - Exemple : " in text


def test_catalogue_gives_inferred_signatures_and_separates_procedures():
    text = render("mecanique")
    assert "`Plaque.concevoir` : Plaque.demande -> Plaque.estimateur -> string Effect.t" in text
    assert "### Procédures" in text and "### Valeurs" in text
    assert "- Utiliser quand : " in text and "- Ne pas utiliser quand : " in text


def test_undocumented_items_stay_out_of_the_catalogue():
    text = render("mecanique")
    assert "valider_et_exporter" not in text and "petit_cote" not in text


def test_interne_elements_are_documented_but_not_published():
    for name in ("mecanique", "ventilation"):
        text = render(name)
        for internal in ("petit_cote", "valider_et_exporter", "reviser_par_mesure", "boucle"):
            assert internal not in text
    source = (LANGUAGES / "mecanique" / "plaque.hyp").read_text(encoding="utf-8")
    interne = {d.path for d in declarations(source) if d.internal}
    assert {"Plaque.petit_cote", "Plaque.reviser_par_mesure", "Plaque.piece"} <= interne


def test_discret_members_are_listed_without_their_description():
    text = render("mecanique")
    assert "- `estimer : demande -> float`\n" in text
    assert "Fonction qui estime" not in text


def test_catalogue_is_generic_across_languages():
    text = render("ventilation")
    assert "`Ventilation.reguler`" in text and "`budget : int`" in text
    assert "Plaque" not in text


@pytest.mark.parametrize("name", ["mecanique", "ventilation"])
def test_rendered_catalogue_matches_the_measured_snapshot(name):
    """The prompt text was measured on the LLM bench: it must not drift, byte for byte."""
    expected = (SNAPSHOTS / f"catalogue_{name}.md").read_bytes()
    assert render(name).encode("utf-8") == expected


def test_catalogue_names_the_entry_point():
    assert "`let procedure = …`" in render("mecanique")


@pytest.mark.parametrize("name", ["mecanique", "ventilation"])
def test_catalogue_is_much_shorter_than_the_source(name):
    language = load_language(LANGUAGES / name)
    source = "".join(
        (language.root / s).read_text(encoding="utf-8") for s in language.manifest["sources"]
    )
    assert len(render(name)) < len(source)


def test_program_skeleton_is_rendered_as_a_code_block():
    text = render("mecanique")
    assert "- Squelette de programme :\n    ```\n    let demande = {" in text
    assert "let procedure = Plaque.concevoir demande Plaque.estimateur_regle\n    ```" in text


def test_decrire_command_prints_the_catalogue_and_its_size(capsys):
    from hypomnesis_codegen.cli import main

    assert main(["decrire", str(LANGUAGES / "ventilation")]) == 0
    captured = capsys.readouterr()
    assert "`Ventilation.reguler`" in captured.out
    assert "caractères" in captured.err
    assert main(["decrire", str(LANGUAGES / "ventilation"), "--format", "json"]) == 0
    assert '"entry": "procedure"' in capsys.readouterr().out
    assert main(["decrire", str(LANGUAGES / "absent")]) == 1


def test_catalogue_includes_transitive_imports_once():
    text = render("composition_a")
    for name in ("Booleen", "Arithmetique", "Contraintes", "CompositionA"):
        assert text.count(f"## Module {name}\n") == 1
