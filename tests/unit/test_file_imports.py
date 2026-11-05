"""Local Python-style imports share typed identities, not importer state."""

import json

import pytest

from hypomnesis.cli import main
from hypomnesis.engine.errors import SourceError
from hypomnesis.engine.language import load_language
from hypomnesis.language.errors import HypomnesisError, NameResolutionError, ParseError
from hypomnesis.language.parser import parse_program
from hypomnesis.lsp.analysis import analyze
from hypomnesis.runtime.natives import default_registry
from hypomnesis.session import Session


def counted_session():
    def emit(text):
        print(text)
        return ()

    natives = default_registry()
    natives.register("test.print", 1, emit)
    return Session(natives)


def load(session, path, source, *, execute=True):
    program = parse_program(source)
    if execute:
        return session.load_program(program, filename=str(path))
    return session.check_program(program, filename=str(path))


def test_python_import_ast_and_rejected_forms():
    program = parse_program(
        "import units\nimport physique.units as mesures\n"
        "from units import mm\nfrom units import mm as millimetres"
    )
    assert [(i.path, i.member, i.alias) for i in program.items] == [
        ("units", None, None),
        ("physique.units", None, "mesures"),
        ("units", "mm", None),
        ("units", "mm", "millimetres"),
    ]
    for source in ('import "units.hyp"', "from units import *", "import ../units"):
        with pytest.raises(ParseError):
            parse_program(source)


def test_relative_dotted_imports_and_aliases(tmp_path, monkeypatch):
    (tmp_path / "physique").mkdir()
    (tmp_path / "physique/units.hyp").write_text("let mm x = x + 1")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    session = Session()
    load(
        session,
        tmp_path / "main.hyp",
        "import physique.units\nimport physique.units as mesures\n"
        "from physique.units import mm as millimetres\n"
        "let answer = physique.units.mm 40 + mesures.mm 0 + millimetres 0",
    )
    assert session.value("answer") == 43
    assert session.type_of("mesures.mm") == "int -> int"
    assert session.type_of("physique.units.mm") == "int -> int"


def test_types_constructors_records_and_nested_modules_keep_identity(tmp_path):
    (tmp_path / "units.hyp").write_text(
        "type t = C of int\n"
        "type record = {value : int}\n"
        "let r = {value = 42}\n"
        "module Length = struct type t = float let mm x = x end"
    )
    session = Session()
    load(
        session,
        tmp_path / "main.hyp",
        "import units\nimport units as u\n"
        "from units import C as D\nfrom units import t\n"
        "from units import Length as L\n"
        "let c : t = u.C 42\n"
        "let answer = match c with units.C n -> n\n"
        "let other = match D 42 with u.C n -> n\n"
        "let r : u.record = {units.value = 42}\n"
        "let projected = units.r.value\n"
        "let length : units.Length.t = L.mm 1.0",
    )
    assert session.value("answer") == 42
    assert session.value("other") == 42
    assert session.value("projected") == 42
    assert session.value("length") == 1.0
    assert session.checker.lookup_type("u.t") is session.checker.lookup_type("units.t")


def test_open_only_opens_loaded_modules(tmp_path):
    (tmp_path / "units.hyp").write_text("module Length = struct let mm x = x end")
    session = Session()
    with pytest.raises(NameResolutionError, match="unbound module"):
        load(session, tmp_path / "main.hyp", "open units.Length")
    load(session, tmp_path / "main.hyp", "import units\nopen units.Length\nlet x = mm 42")
    assert session.value("x") == 42


def test_imports_are_isolated_from_importer_values(tmp_path):
    (tmp_path / "bad.hyp").write_text("let stolen = secret")
    with pytest.raises(SourceError, match="unbound value secret") as caught:
        load(Session(), tmp_path / "main.hyp", "let secret = 42\nimport bad")
    assert caught.value.path == tmp_path / "bad.hyp"
    assert caught.value.span.line == 1


def test_imported_file_still_sees_the_prelude(tmp_path):
    (tmp_path / "units.hyp").write_text("let total = List.fold_left ( + ) 0 [20; 22]")
    session = Session(execute_prelude=False)
    load(session, tmp_path / "main.hyp", "import units\nlet answer = units.total", execute=False)
    assert session.type_of("answer") == "int"


def test_cycles_report_the_chain(tmp_path):
    a = tmp_path / "a.hyp"
    b = tmp_path / "b.hyp"
    a.write_text("import b")
    b.write_text("import a")
    session = Session()
    with pytest.raises(SourceError, match="circular import") as caught:
        load(session, a, a.read_text())
    assert str(a) in caught.value.message and str(b) in caught.value.message
    assert session.imported_sources == {}


@pytest.mark.parametrize(
    "source,message",
    [
        ("import missing", "cannot read imported file"),
        ("from units import missing", "no exported member missing"),
        ("import units as A\nmodule A = struct end\nimport units as A", "collision"),
        ("let mm = 0\nfrom units import mm", "collision"),
        ("let units = 0\nimport units", "collision"),
        ("import units as mm\nfrom units import mm", "collision"),
        ("from units import mm as Upper", "capitalization"),
    ],
)
def test_import_failures_are_explicit_and_transactional(tmp_path, source, message):
    (tmp_path / "units.hyp").write_text("let mm = 42")
    session = Session()
    before = len(session.definitions)
    with pytest.raises(HypomnesisError, match=message):
        load(session, tmp_path / "main.hyp", source)
    assert len(session.definitions) == before
    assert not session.imported_sources
    load(session, tmp_path / "main.hyp", "import units\nlet answer = units.mm")
    assert session.value("answer") == 42


def test_static_import_does_not_evaluate_and_failed_file_can_be_corrected(tmp_path):
    target = tmp_path / "units.hyp"
    target.write_text("let x = unknown")
    session = Session()
    with pytest.raises(SourceError):
        load(session, tmp_path / "main.hyp", "import units", execute=False)
    target.write_text("let x = 1 / 0")
    load(session, tmp_path / "main.hyp", "import units\nlet x = units.x", execute=False)
    assert session.type_of("x") == "int"
    assert session.value("id")  # Only the prelude was evaluated.
    assert not any(name.endswith(".x") for name in session.interpreter.globals)


def test_canonical_paths_diamonds_aliases_and_multiple_roots_execute_once(tmp_path, capsys):
    (tmp_path / "base.hyp").write_text(
        'external emit : string -> unit = "test.print"\n'
        'let observed = emit "once"\ntype t = C\nlet x = 42'
    )
    (tmp_path / "a.hyp").write_text("import base\nlet x = base.x")
    (tmp_path / "b.hyp").write_text("import base\nlet x = base.x")
    (tmp_path / "alias.hyp").symlink_to(tmp_path / "base.hyp")
    session = counted_session()
    load(session, tmp_path / "main.hyp", "import a\nimport b\nimport alias\nimport base")
    load(session, tmp_path / "next.hyp", "import base as second\nlet x = second.x")
    assert capsys.readouterr().out == "once\n"
    assert session.value("x") == 42
    assert session.checker.lookup_type("base.t") is session.checker.lookup_type("alias.t")
    assert session.checker.lookup_type("second.t") is session.checker.lookup_type("base.t")


def test_check_then_execute_import_reuses_types_but_runs_pending_definitions(tmp_path, capsys):
    (tmp_path / "units.hyp").write_text(
        'external emit : string -> unit = "test.print"\nlet printed = emit "once"\nlet mm = 42'
    )
    session = counted_session()
    load(session, tmp_path / "static.hyp", "import units", execute=False)
    assert capsys.readouterr().out == ""
    load(session, tmp_path / "run.hyp", "import units\nlet answer = units.mm")
    load(session, tmp_path / "next.hyp", "from units import mm\nlet second = mm")
    assert capsys.readouterr().out == "once\n"
    assert session.value("answer") == session.value("second") == 42


def test_explicit_multifile_loading_then_import_reuses_definitions(tmp_path):
    units = tmp_path / "units.hyp"
    units.write_text("module Length = struct let mm x = x end")
    session = Session()
    load(session, units, units.read_text())
    load(
        session,
        tmp_path / "main.hyp",
        "from units import Length\nlet answer = Length.mm 42",
    )
    assert session.value("answer") == 42
    assert [b for b in session.interpreter.globals if b.startswith("Length.mm")] == ["Length.mm"]


def test_cli_dependency_error_identifies_original_file(tmp_path, capsys):
    (tmp_path / "units.hyp").write_text("let x = true + 1")
    entry = tmp_path / "main.hyp"
    entry.write_text("import units")
    assert main(["check", str(entry), "--format", "json"]) == 1
    [issue] = json.loads(capsys.readouterr().out)["diagnostics"]
    assert issue["file"] == str(tmp_path / "units.hyp")
    assert issue["stage"] == "type"


def test_lsp_unsaved_transitive_dependency_and_error_recovery(tmp_path):
    base = tmp_path / "base.hyp"
    middle = tmp_path / "middle.hyp"
    base.write_text("let x = 1")
    middle.write_text("import base\nlet x = base.x")
    path = tmp_path / "main.hyp"
    source = "import middle\nlet answer = middle.x + 1"
    assert analyze(path, source, tmp_path, None, {}) == []
    [issue] = analyze(path, source, tmp_path, None, {str(base): "let x = true"})
    assert issue.code == "type"
    assert analyze(path, source, tmp_path, None, {str(base): "let x = 42"}) == []


def test_source_less_import_is_refused_not_resolved_from_cwd():
    with pytest.raises(NameResolutionError, match="source filename"):
        Session().check("import units")


def test_failed_evaluation_never_replays_import_side_effects(tmp_path, capsys):
    (tmp_path / "units.hyp").write_text(
        'external emit : string -> unit = "test.print"\n'
        'let observed = emit "once"\nlet broken = 1 / 0'
    )
    session = counted_session()
    with pytest.raises(HypomnesisError, match="Division_by_zero"):
        load(session, tmp_path / "main.hyp", "import units")
    assert capsys.readouterr().out == "once\n"
    with pytest.raises(NameResolutionError, match="new session"):
        load(session, tmp_path / "retry.hyp", "import units")
    assert capsys.readouterr().out == ""


def test_imported_warnings_retain_their_source_file(tmp_path):
    dependency = tmp_path / "units.hyp"
    dependency.write_text("let f = function Some x -> x")
    result = load(Session(), tmp_path / "main.hyp", "import units", execute=False)
    [warning] = result.warnings
    assert warning.filename == str(dependency)


def test_language_file_imports_remain_confined_even_through_symlinks(tmp_path):
    root = tmp_path / "language"
    root.mkdir()
    (root / "langage.hyp").write_text('language example = struct let version = "1" end')
    (tmp_path / "outside.hyp").write_text("let x = 42")
    (root / "units.hyp").symlink_to(tmp_path / "outside.hyp")
    entry = root / "langage.hyp"
    entry.write_text(entry.read_text() + "\nimport units")
    with pytest.raises(SourceError, match="outside language package"):
        load_language(root, strict=False)


def test_language_imports_are_static_and_require_documentation(tmp_path):
    entry = tmp_path / "langage.hyp"
    entry.write_text('language example = struct let version = "1" end\nimport units')
    dependency = tmp_path / "units.hyp"
    dependency.write_text("let mm = 1 / 0")
    with pytest.raises(HypomnesisError, match="has no description"):
        load_language(tmp_path, execute=False)
    dependency.write_text("(** Millimetres. *)\nlet mm = 1 / 0")
    assert load_language(tmp_path, execute=False).session.type_of("units.mm") == "int"


def test_different_directories_can_have_distinct_units_files(tmp_path):
    for folder, number in (("a", 20), ("b", 22)):
        directory = tmp_path / folder
        directory.mkdir()
        (directory / "units.hyp").write_text(f"type t = C\nlet value = {number}")
        (directory / "main.hyp").write_text("import units\nlet value = units.value")
    session = Session()
    load(
        session,
        tmp_path / "main.hyp",
        "import a.main as a\nimport b.main as b\nlet answer = a.value + b.value",
    )
    assert session.value("answer") == 42
    assert session.checker.lookup_type("a.units.t") is not session.checker.lookup_type("b.units.t")


def test_explicit_file_reexports_an_import_already_visible_in_the_session(tmp_path):
    base = tmp_path / "base.hyp"
    base.write_text("let x = 42")
    middle = tmp_path / "middle.hyp"
    middle.write_text("import base")
    session = Session()
    session.load("import base", filename=str(tmp_path / "first.hyp"))
    session.load(middle.read_text(), filename=str(middle))
    session.load("import middle\nlet answer = middle.base.x", filename=str(tmp_path / "last.hyp"))
    assert session.value("answer") == 42


def test_cli_m1_program_resolves_imports_beside_its_file(tmp_path, monkeypatch, capsys):
    root = tmp_path / "language"
    root.mkdir()
    (root / "langage.hyp").write_text(
        'language example = struct let version = "1" '
        'let procedure = {kind = "program"; entry = "main"} end'
    )
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "parameters.hyp").write_text("let answer = 42")
    program = programs / "main.hyp"
    program.write_text("import parameters\nlet main = Effect.return parameters.answer")
    monkeypatch.chdir(root)
    assert (
        main(
            [
                "lancer",
                str(root),
                str(program),
                "--sortie",
                str(tmp_path / "output"),
                "--format",
                "json",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "ok"
    assert result["report"]["result"] == 42
