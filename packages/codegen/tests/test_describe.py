"""Catalogue de prompt compilé depuis l'auto-documentation d'un langage."""

import json
import shutil
from pathlib import Path

import pytest

from hypomnesis.engine.language import load_language
from hypomnesis.language.docs import declarations, published
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


def test_imported_sealed_module_only_publishes_its_opaque_interface(tmp_path):
    (tmp_path / "langage.hyp").write_text(
        'language example = struct let version = "1" end\nimport units as mesures'
    )
    (tmp_path / "units.hyp").write_text(
        "(** Interface. *)\nmodule type S = sig type t val make : int -> t "
        "val read : t -> int end\n"
        "(** Mesures abstraites. *)\nmodule M : S = struct\n"
        "(** Mesure. *)\ntype t = Secret of int\n"
        "(** Construction. *)\nlet make x = Secret x\n"
        "(** Lecture. *)\nlet read = function Secret x -> x\n"
        "(** Ne doit pas être publié. *)\nlet private_value = 1 / 0\nend"
    )
    result = catalogue(load_language(tmp_path, execute=False))
    text = result.render()
    assert "private_value" not in text and "Secret" not in text
    module = next(m for m in result.modules if m.path == "mesures.M")
    assert {v.path: v.signature for v in module.values} == {
        "mesures.M.make": "int -> mesures.M.t",
        "mesures.M.read": "mesures.M.t -> int",
    }
    assert len(module.types) == 1
    assert module.types[0].fields == () and module.types[0].constructors == ()


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


def test_mechanics_has_every_public_value_typed_within_a_measured_prompt_budget():
    language = load_language(LANGUAGES / "mecanique", execute=False)
    result = catalogue(language)
    expected = {
        d.path
        for source in language.plan.source_files()
        for d in published(declarations(source.text))
        if d.kind == "value"
    }
    values = {v.path: v.signature for module in result.modules for v in module.values}
    assert values == {path: language.session.type_of(path) for path in expected}
    assert expected
    assert len(result.render().encode("utf-8")) <= 16_384
    assert "Ventilation" not in result.render()


def test_static_plugin_contracts_permissions_and_adapters_are_exported(tmp_path, capsys):
    from hypomnesis_codegen.cli import main

    root = tmp_path / "mecanique"
    shutil.copytree(LANGUAGES / "mecanique", root)
    for path in (root / "adaptateurs").glob("*.py"):
        path.write_text('raise AssertionError("adapter imported during description")')
    manifest = {
        "id": "geometry.export",
        "version": "1.0.0",
        "role": "Actuator",
        "signature": {"input": "Json.t", "output": "Json.t"},
        "input_schema": "https://example.test/input",
        "output_schema": "https://example.test/output",
        "permissions": ["geometry.write"],
        "backend": {"kind": "python", "entry_point": "not_installed.factory"},
        "error_policy": {"idempotent": True, "timeout_seconds": 1, "max_attempts": 1},
    }
    path = tmp_path / "plugin.json"
    path.write_text(json.dumps(manifest))
    args = ["decrire", str(root), "--plugin", str(path)]
    assert main([*args, "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["plugins"][0]["permissions"] == ["geometry.write"]
    assert result["plugins"][0]["signature"] == "Json.t -> Json.t"
    assert result["contracts"] and result["adapters"]
    assert main(args) == 0
    text = capsys.readouterr().out
    assert "geometry.export@1.0.0" in text
    assert "Permissions requises, non accordées : geometry.write" in text
    assert main(["decrire", str(root), "--plugin", str(tmp_path / "absent")]) == 1
    assert "refusé" in capsys.readouterr().err


def test_library_and_top_level_values_are_publishable(tmp_path):
    (tmp_path / "langage.hyp").write_text(
        'language racine = struct let version = "1.0.0" end\n'
        "(** Fonction identité. *)\nlet identite x = x\n"
    )
    result = catalogue(load_language(tmp_path, execute=False))
    assert result.entry is None
    assert "Bibliothèque sans procédure" in result.render()
    assert result.modules[0].values[0].path == "identite"
    assert result.modules[0].values[0].signature == "'a -> 'a"


def test_imported_file_catalogue_uses_public_aliases_and_transitive_docs(tmp_path):
    (tmp_path / "langage.hyp").write_text(
        'language racine = struct let version = "1" end\n'
        "import units as mesures\nfrom units import mm as millimetres"
    )
    (tmp_path / "base.hyp").write_text("(** Valeur de référence. *)\nlet valeur = 42")
    (tmp_path / "units.hyp").write_text(
        "import base\n(** Conversion en millimètres. *)\nlet mm x = x\n"
        "(** Unité nominale. *)\ntype t =\n  (** Unité. *)\n  | U\n"
        "(** Valeur nominale. *)\nlet valeur = U\n"
        "(** Longueurs. *)\nmodule Length = struct\n"
        "  (** Identité. *)\n  let identite x = x\nend"
    )
    language = load_language(tmp_path, execute=False)
    result = catalogue(language)
    values = {v.path: v for module in result.modules for v in module.values}
    assert values["mesures.mm"].signature == "'a -> 'a"
    assert values["millimetres"].signature == "'a -> 'a"
    assert values["mesures.Length.identite"].signature == "'a -> 'a"
    assert values["mesures.valeur"].signature == "mesures.t"
    assert values["mesures.base.valeur"].signature == "int"
    assert "référence" in values["mesures.base.valeur"].summary
    result.to_json()
