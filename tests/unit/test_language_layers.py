"""Native package declarations, dependency isolation and static loading."""

import json
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.engine.errors import LanguageError, SourceError
from hypomnesis.engine.language import load_language
from hypomnesis.engine.layers import check_layers, resolve_layers
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.ir.core import DefValue
from hypomnesis.language import ast as A
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.language.parser import parse_program
from hypomnesis.lsp.analysis import analyze
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo" / "languages"


def layer(tmp_path, name, body="", imports=(), config="", entry="langage.hyp"):
    root = tmp_path / name
    root.mkdir(exist_ok=True)
    paths = "; ".join(json.dumps(path) for path in imports)
    (root / entry).write_text(
        f'language {name} = {{ version = "1"; imports = [{paths}]; {config} }}\n{body}'
    )
    return root if entry == "langage.hyp" else root / entry


def test_static_configuration_ast_and_positions():
    [item] = parse_program(
        '\nlanguage test = { version = "1"; adapters = []; extra = {"a-b" = true; n = 1_000} }'
    ).items
    assert isinstance(item, A.LanguageItem)
    assert item.configuration["extra"] == {"a-b": True, "n": 1000}
    assert item.span.line == 2
    with pytest.raises(HypomnesisError, match="package loader"):
        Session().check('language test = { version = "1" }')


@pytest.mark.parametrize(
    "source",
    [
        'language test = { version = "1"; version = "2" }',
        "language test = { version = compute () }",
        'language test = { version = "1"; imports = [read_file "evil"] }',
    ],
)
def test_configuration_is_not_an_evaluated_expression(source):
    with pytest.raises(HypomnesisError):
        parse_program(source)


@pytest.mark.parametrize(
    "source",
    [
        "language test = {}",
        'language test = { version = "1"; extra = true }',
        'let x = 1\nlanguage test = { version = "1" }',
        'language test = { version = "1" }\nlanguage again = { version = "1" }',
        'language test = { version = "1" }\nmodule M = struct language sub = {} end',
    ],
)
def test_invalid_declarations_are_refused(tmp_path, source):
    (tmp_path / "langage.hyp").write_text(source)
    with pytest.raises(LanguageError):
        resolve_layers(tmp_path)


def test_old_json_manifests_are_no_longer_loaded(tmp_path):
    (tmp_path / "langage.json").write_text('{"name": "legacy"}')
    with pytest.raises(LanguageError, match=r"langage\.hyp"):
        resolve_layers(tmp_path)


def test_shared_demo_layers_typecheck_and_execute_in_two_languages(tmp_path):
    a = load_language(DEMO / "composition_a")
    b = load_language(DEMO / "composition_b")
    assert a.session.type_of("Booleen.conjonction") == "bool -> bool -> bool"
    assert b.session.type_of("Arithmetique.addition") == "int -> int -> int"
    assert a.function("CompositionA.calculer")(20, 22).arg == 42
    assert b.function("CompositionB.invalide")(20, -1) is True
    for language in (a, b):
        program = ROOT / "demo" / "programs" / language.name / "exemple.hyp"
        report = run_procedure(language, program.read_text(), out_dir=tmp_path / language.name)
        assert not report.stopped
    with pytest.raises(HypomnesisError):
        load_language(DEMO / "composition_a").load_program("let x = Booleen.conjonction 1 true")


def test_diamond_and_path_aliases_load_shared_definitions_once():
    language = load_language(DEMO / "composition_a")
    names = [
        name
        for definition in language.session.definitions
        if isinstance(definition, DefValue)
        for _, name in definition.targets
    ]
    assert names.count("Arithmetique.addition") == 1
    graph = language.plan.to_json()
    assert graph["layers"] == [["arithmetique", "booleen"], ["contraintes"], ["composition_a"]]
    assert graph["orientation"] == "dependency-to-dependent"
    assert {"from": "arithmetique", "to": "composition_a"} in graph["edges"]


def test_cycle_reports_its_members(tmp_path):
    a = layer(tmp_path, "a", imports=["../b"])
    layer(tmp_path, "b", imports=["../a"])
    with pytest.raises(LanguageError, match=r"cycle d'imports.*a.*b"):
        resolve_layers(a)


def test_missing_dependency_is_not_an_empty_language(tmp_path):
    root = layer(tmp_path, "a", imports=["../missing"])
    with pytest.raises(LanguageError, match=r"missing/langage.hyp"):
        load_language(root)


def test_duplicate_identity_is_refused(tmp_path):
    a = layer(tmp_path, "a", imports=["../b", "../c"])
    layer(tmp_path, "b")
    c = layer(tmp_path, "c")
    (c / "langage.hyp").write_text('language b = { version = "1" }')
    with pytest.raises(LanguageError, match="identité de couche dupliquée"):
        resolve_layers(a)


@pytest.mark.parametrize(
    "body", ["module Shared = struct let x = 1 end", "let x = 1", "type t = A"]
)
def test_exports_from_distinct_layers_cannot_shadow_each_other(tmp_path, body):
    a = layer(tmp_path, "a", imports=["../b", "../c"])
    layer(tmp_path, "b", body)
    layer(tmp_path, "c", body)
    with pytest.raises(LanguageError, match="collision d'export"):
        load_language(a, strict=False)


def test_a_layer_does_not_accidentally_see_a_siblings_imports(tmp_path):
    root = layer(tmp_path, "root", imports=["../a", "../b"])
    layer(tmp_path, "a", "module A = struct let x = 1 end")
    b = layer(tmp_path, "b", "module B = struct let x = A.x end")
    with pytest.raises(SourceError) as caught:
        load_language(root, strict=False)
    assert caught.value.path == b / "langage.hyp"
    assert caught.value.stage_id == "name"
    assert str(b / "langage.hyp") in str(caught.value)


def test_explicit_file_imports_and_aliases_share_the_same_layer(tmp_path):
    b = layer(tmp_path, "b", "let x = 1", entry="base.hyp")
    a = layer(tmp_path, "a", imports=["../b/base.hyp", "../b/../b/base.hyp"])
    plan = resolve_layers(a)
    assert plan.order() == [b, a / "langage.hyp"]
    assert check_layers(plan, strict=False).type_of("x") == "int"


@pytest.mark.parametrize(
    "config",
    [
        'sources = ["../outside.hyp"]',
        'sources = ["langage.hyp"]',
        'sources = ["same.hyp"; "same.hyp"]',
        'adapters = ["../outside.py"]',
        'contracts = ["../outside.json"]',
        'examples = "../outside.json"',
    ],
)
def test_package_owned_paths_cannot_escape_or_repeat(tmp_path, config):
    root = layer(tmp_path, "a", config=config)
    with pytest.raises(LanguageError):
        resolve_layers(root)


def test_symlinks_to_external_sources_are_refused(tmp_path):
    outside = tmp_path / "outside.hyp"
    outside.write_text("let x = 1")
    root = layer(tmp_path, "a", config='sources = ["alias.hyp"]')
    (root / "alias.hyp").symlink_to(outside)
    with pytest.raises(LanguageError, match="hors du paquet"):
        resolve_layers(root)


def test_library_has_no_implicit_procedure(tmp_path):
    language = load_language(DEMO / "booleen")
    with pytest.raises(LanguageError, match="bibliothèque sans procédure"):
        run_procedure(language, "let procedure = Effect.return ()", out_dir=tmp_path)


def test_static_paths_never_evaluate_definitions_or_import_python(tmp_path):
    root = layer(
        tmp_path,
        "a",
        "(** A value. *)\nlet x = 1 / 0",
        config='adapters = ["external.py"]',
    )
    (root / "external.py").write_text('raise RuntimeError("Python must not run")')
    assert load_language(root, execute=False).session.type_of("x") == "int"
    assert main(["check", str(root / "langage.hyp")]) == 0
    target = tmp_path / "program.hyp"
    assert analyze(target, "let y = x + 1", tmp_path, str(root), {}) == []


def test_static_package_certificates_keep_the_prelude_boundary(tmp_path):
    root = layer(tmp_path, "a", "(** Value. *)\nlet x = 1")
    static = load_language(root, execute=False).session
    evaluated = load_language(root).session
    assert static.prelude_definitions == evaluated.prelude_definitions > 0
    assert static.definitions == evaluated.definitions


def test_dependency_error_keeps_its_file_and_span_in_cli_json(tmp_path, capsys):
    a = layer(tmp_path, "a", imports=["../b"])
    b = layer(tmp_path, "b", "(** Broken. *)\nlet x = true + 1")
    program = tmp_path / "p.hyp"
    program.write_text("let x = 1")
    assert main(["check", str(program), "--langage", str(a), "--format", "json"]) == 1
    [issue] = json.loads(capsys.readouterr().out)["diagnostics"]
    assert issue["file"] == str(b / "langage.hyp")
    assert issue["line"] == 3
    assert issue["stage"] == "type"


def test_cli_checks_language_then_program_and_exports_graph(tmp_path, capsys):
    path = DEMO / "composition_a"
    program = ROOT / "demo" / "programs" / "composition_a" / "exemple.hyp"
    assert main(["check", str(path / "langage.hyp"), str(program), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["diagnostics"] == []
    assert main(["layers", str(path)]) == 0
    assert json.loads(capsys.readouterr().out) == resolve_layers(path).to_json()
    assert main(["layers", str(tmp_path / "missing")]) == 1


def test_lsp_follows_transitive_unsaved_sources_and_declarations(tmp_path):
    a = layer(tmp_path, "a", imports=["../b"])
    b = layer(tmp_path, "b", "let x = 1")
    target = tmp_path / "program.hyp"
    assert analyze(target, "let y = x + 1", tmp_path, str(a), {}) == []
    [issue] = analyze(
        target,
        "let y = x + 1",
        tmp_path,
        str(a),
        {str(b / "langage.hyp"): 'language b = { version = "1" }\nlet x = true'},
    )
    assert issue.code == "type"
    [issue] = analyze(
        target,
        "let y = x + 1",
        tmp_path,
        str(a),
        {str(a / "langage.hyp"): 'language a = { version = "1" }'},
    )
    assert issue.code == "name"


def test_lsp_reports_dependency_errors_at_the_program_start(tmp_path):
    a = layer(tmp_path, "a", imports=["../b"])
    b = layer(tmp_path, "b", "let x = 1 + true")
    [issue] = analyze(tmp_path / "p.hyp", "let y = 1", tmp_path, str(a), {})
    assert issue.code == "type"
    assert str(b / "langage.hyp") in issue.message
    assert issue.range.start.line == 0


def test_lsp_checks_a_new_unsaved_entry_and_uses_its_configuration(tmp_path):
    entry = tmp_path / "langage.hyp"
    source = 'language test = { version = "1" }\nlet x = 1 + true'
    [issue] = analyze(entry, source, tmp_path, None, {})
    assert issue.code == "type"
    assert issue.range.start.line == 1
