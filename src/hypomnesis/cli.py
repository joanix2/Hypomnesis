"""Command-line interface (Typer): one function per ``hypomnesis`` subcommand."""

from __future__ import annotations

import json
import sys
from contextlib import nullcontext, redirect_stdout
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

import typer

from hypomnesis import __version__
from hypomnesis.engine.errors import LanguageError
from hypomnesis.language import ast as A
from hypomnesis.language.errors import HypomnesisError, diagnostics_document
from hypomnesis.language.parser import parse_program
from hypomnesis.session import Session


def _load_files(
    session: Session,
    paths: list[Path],
    *,
    execute: bool,
    as_json: bool = False,
    report_success: bool = True,
    strict: bool = False,
) -> tuple[int, Session]:
    """Load files in order and return the actual session, including language entries."""
    for path in paths:
        try:
            previous_warnings = len(session.warnings)
            source = path.read_text(encoding="utf-8")
            program = parse_program(source)
            if any(isinstance(item, A.LanguageItem) for item in program.items):
                from hypomnesis.engine.language import load_language

                language = load_language(path, execute=execute)
                language.session.warnings[:0] = session.warnings
                session = language.session
                if not as_json:
                    print(f"langage : {language.name}")
                result = None
            else:
                result = (
                    session.load_program(program, filename=str(path))
                    if execute
                    else session.check_program(program, filename=str(path))
                )
        except HypomnesisError as exc:
            if as_json:
                print(
                    json.dumps(
                        diagnostics_document(
                            [w.to_diagnostic() for w in session.warnings]
                            + [exc.to_diagnostic(str(path))]
                        )
                    )
                )
            else:
                print(exc.render(source, str(path)), file=sys.stderr)
            return 1, session
        except (LanguageError, OSError, UnicodeError) as exc:
            if as_json:
                print(
                    json.dumps(
                        diagnostics_document(
                            [w.to_diagnostic() for w in session.warnings]
                            + [HypomnesisError(str(exc)).to_diagnostic(str(path))]
                        )
                    )
                )
            else:
                print(f"refusé : {exc}", file=sys.stderr)
            return 1, session
        warnings = session.warnings[previous_warnings:]
        if not as_json:
            for warning in warnings:
                print(
                    warning.render(source if warning.filename == str(path) else None),
                    file=sys.stderr,
                )
            for binding in result.bindings if result is not None else ():
                print(binding.render() if execute else binding.render_signature())
        if strict and warnings:
            if as_json:
                print(
                    json.dumps(
                        diagnostics_document(
                            [{**w.to_diagnostic(), "severity": "error"} for w in session.warnings]
                        )
                    )
                )
            else:
                print("mode strict : avertissements de filtrage refusés", file=sys.stderr)
            return 1, session
    if as_json and report_success:
        print(json.dumps(diagnostics_document([w.to_diagnostic() for w in session.warnings])))
    return 0, session


def _check(
    files: list[Path],
    output_format: CheckFormat,
    langage: Path | None,
    emit_certificate: Path | None,
    certify: bool = False,
    checker: Path | None = None,
    checker_timeout: float = 30.0,
    strict: bool = False,
) -> int:
    """Type-check files, alone or in the context of a M2 language."""
    session = Session()
    if langage is not None:
        from hypomnesis.engine.language import LanguageError, load_language

        try:
            session = load_language(langage, execute=False).session
        except (LanguageError, HypomnesisError) as exc:
            if output_format is CheckFormat.JSON:
                error = exc if isinstance(exc, HypomnesisError) else HypomnesisError(str(exc))
                print(json.dumps(diagnostics_document([error.to_diagnostic(str(langage))])))
            else:
                message = exc.render() if isinstance(exc, HypomnesisError) else str(exc)
                print(f"refusé : {message}", file=sys.stderr)
            return 1
    as_json = output_format is CheckFormat.JSON
    if not as_json:
        for warning in session.warnings:
            print(warning.render(), file=sys.stderr)
    if strict and session.warnings:
        if as_json:
            print(
                json.dumps(
                    diagnostics_document(
                        [{**w.to_diagnostic(), "severity": "error"} for w in session.warnings]
                    )
                )
            )
        else:
            print("mode strict : avertissements de filtrage refusés", file=sys.stderr)
        return 1
    status, session = _load_files(
        session, files, execute=False, as_json=as_json, report_success=False, strict=strict
    )
    if status:
        return status
    from hypomnesis.certify.checker import CertificationError, check_certificate

    try:
        if checker is not None and not certify:
            raise CertificationError("--checker exige --certify")
        if certify or emit_certificate is not None:
            with TemporaryDirectory(prefix="hyp-certify-") as directory:
                path = (
                    emit_certificate
                    if emit_certificate is not None
                    else (Path(directory) / "certificate.json")
                )
                _emit_certificate(session, path)
                if certify:
                    accepted = check_certificate(
                        path, checker=checker, timeout_seconds=checker_timeout
                    )
                    print(f"certification Lean : {accepted}", file=sys.stderr)
    except (CertificationError, OSError) as exc:
        if as_json:
            diagnostic = HypomnesisError(str(exc)).to_diagnostic(str(files[-1]))
            print(
                json.dumps(
                    diagnostics_document(
                        [w.to_diagnostic() for w in session.warnings] + [diagnostic]
                    )
                )
            )
        else:
            print(f"certification refusée : {exc}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(diagnostics_document([w.to_diagnostic() for w in session.warnings])))
    return 0


def _emit_certificate(session: Session, path: Path) -> None:
    """Write the session's certificate, validated against its JSON Schema."""
    from hypomnesis.certify import CERTIFICATE_SCHEMA_ID, CertificateError, session_certificate
    from hypomnesis.certify.checker import CertificationError
    from hypomnesis.contracts.registry import SchemaRegistry

    try:
        certificate = session_certificate(session)
    except CertificateError as exc:
        raise CertificationError(f"export du certificat : {exc}") from exc
    issues = SchemaRegistry.with_builtin_schemas().issues(CERTIFICATE_SCHEMA_ID, certificate)
    if issues:
        detail = "; ".join(map(str, issues[:10]))
        raise CertificationError(f"certificat invalide pour son schéma : {detail}")
    try:
        path.write_text(
            json.dumps(certificate, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise CertificationError(f"écriture du certificat : {exc}") from exc
    print(f"certificate: {len(session.definitions)} definitions -> {path}", file=sys.stderr)


def _pairs(items: list[str]) -> dict[str, str]:
    result = {}
    for item in items:
        key, separator, value = item.partition("=")
        if not separator or not key:
            raise ValueError(f"--env exige CLE=VALEUR : {item!r}")
        result[key] = value
    return result


def _plugins(
    manifests: list[Path],
    *,
    identifier: str | None = None,
    version: str | None = None,
    role: str | None = None,
) -> int:
    from hypomnesis.engine.registry import ExtensionRegistry, RegistryError

    try:
        registry = ExtensionRegistry()
        registry.load_paths(manifests)
        metadata = (
            registry.list(role=role) if identifier is None else registry.show(identifier, version)
        )
    except RegistryError as exc:
        print(f"refusé : {exc}", file=sys.stderr)
        return 1
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    return 0


class Mode(StrEnum):
    """Execution mode of a M1 program (forwarded to the procedure engine)."""

    SIMULATE = "simulate"
    DRY_RUN = "dry-run"
    PRODUCTION = "production"


class CheckFormat(StrEnum):
    """Output format of compiler diagnostics and procedure execution."""

    TEXT = "text"
    JSON = "json"


def _lancer(
    langage: Path,
    programme: Path | None,
    demande: str | None,
    mode: Mode,
    sortie: Path,
    env: list[str],
    sans_permission: bool,
    generated: bool = False,
    output_format: CheckFormat = CheckFormat.TEXT,
) -> int:
    from hypomnesis.engine.language import LanguageError, load_language
    from hypomnesis.engine.procedure import render, run_procedure

    as_json = output_format is CheckFormat.JSON
    try:
        missing_program = False
        report = None
        with redirect_stdout(sys.stderr) if as_json else nullcontext():
            language = load_language(langage)
            if programme is not None:
                program = programme.read_text(encoding="utf-8")
            elif demande is not None and language.adapters.identifiers("transcriber"):
                program = language.adapters.get("transcriber")(demande)
            else:
                missing_program = True
            if not missing_program:
                report = run_procedure(
                    language,
                    program,
                    mode=mode.value,
                    out_dir=sortie,
                    environment=_pairs(env),
                    permissions=frozenset() if sans_permission else None,
                    generated=generated or (programme is None and demande is not None),
                )
        if missing_program:
            message = "un programme M1 ou une --demande transcriptible est requis"
            if as_json:
                _print_execution(
                    _execution_document(
                        mode, "error", None, [HypomnesisError(message).to_diagnostic("<programme>")]
                    )
                )
            else:
                print(message, file=sys.stderr)
            return 64
        assert report is not None
        if as_json:
            diagnostics = [w.to_diagnostic() for w in language.session.warnings]
            if report.stopped:
                diagnostics.append(HypomnesisError(report.stopped).to_diagnostic(str(programme)))
            _print_execution(
                _execution_document(
                    mode,
                    "stopped" if report.stopped else "ok",
                    {**report.to_json(), "steps": report.steps},
                    diagnostics,
                )
            )
            return int(bool(report.stopped))
        print(render(report))
        return 0
    except (LanguageError, HypomnesisError, ValueError, OSError, UnicodeError) as exc:
        if as_json:
            error = exc if isinstance(exc, HypomnesisError) else HypomnesisError(str(exc))
            _print_execution(
                _execution_document(
                    mode, "error", None, [error.to_diagnostic(str(programme or "<programme>"))]
                )
            )
            return 1
        if isinstance(exc, HypomnesisError):
            message = exc.render(None, str(programme or "<programme>"))
        else:
            message = str(exc)
        print(f"refusé : {message}", file=sys.stderr)
        return 1


def _execution_document(
    mode: Mode, status: str, report: object, diagnostics: list[dict[str, object]]
) -> dict[str, object]:
    return {
        "version": "1.0.0",
        "mode": mode.value,
        "status": status,
        "report": report,
        "diagnostics": diagnostics,
    }


def _print_execution(document: dict[str, object]) -> None:
    from hypomnesis.contracts.registry import SchemaRegistry

    try:
        text = json.dumps(document, ensure_ascii=False, allow_nan=False)
    except TypeError as exc:
        raise ValueError(f"résultat d'exécution non JSON : {exc}") from exc
    SchemaRegistry.with_builtin_schemas().validate(
        "https://schemas.example.org/hypomnesis/cli-execution/1.0.0", json.loads(text)
    )
    print(text)


def _repl(session: Session) -> int:
    print(f"Hypomnesis {__version__} — enter items or expressions, end with ';;'. Ctrl-D to quit.")
    buffer: list[str] = []
    while True:
        try:
            line = input("# " if not buffer else "  ")
        except EOFError:
            print()
            return 0
        buffer.append(line)
        text = "\n".join(buffer).strip()
        if not text.endswith(";;"):
            continue
        buffer.clear()
        source = text[:-2].strip()
        if not source:
            continue
        try:
            previous_warnings = len(session.warnings)
            try:
                result = session.load(source)
                bindings = result.bindings
                for info in result.types:
                    print(f"type {info.qname.split('#', 1)[0]}")
            except HypomnesisError as first:
                if first.stage != "syntax error":
                    raise
                bindings = [session.eval(source)]
            for binding in bindings:
                print(binding.render())
            for warning in session.warnings[previous_warnings:]:
                print(warning.render(source, "<repl>"), file=sys.stderr)
        except HypomnesisError as exc:
            print(exc.render(source, "<repl>"), file=sys.stderr)


app = typer.Typer(
    name="hypomnesis",
    help="Hypomnesis — métalangage fonctionnel pour définir des langages métiers.",
    add_completion=False,
)

plugins_app = typer.Typer(help="Inspecter les manifestes statiques, sans charger les backends.")
app.add_typer(plugins_app, name="plugins")

ManifestPaths = Annotated[
    list[Path] | None,
    typer.Option(
        "--manifest",
        exists=True,
        readable=True,
        metavar="CHEMIN",
        help="manifeste JSON ou dossier (*.json immédiats) ; répétable, "
        "aucune découverte implicite",
    ),
]

SourceFiles = Annotated[
    list[Path],
    typer.Argument(
        exists=True,
        dir_okay=False,
        readable=True,
        help="fichiers .hyp, traités dans l'ordre",
    ),
]


def _show_version(value: bool) -> None:
    if value:
        print(f"hypomnesis {__version__}")
        raise typer.Exit()


def _exit_with(status: int) -> None:
    if status != 0:
        raise typer.Exit(status)


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="afficher la version et quitter",
        ),
    ] = False,
) -> None:
    """Hypomnesis — métalangage fonctionnel pour définir des langages métiers."""


@app.command("run")
def run_command(files: SourceFiles) -> None:
    """Typer et évaluer des fichiers, dans l'ordre."""
    status, _ = _load_files(Session(), files, execute=True)
    _exit_with(status)


@app.command("check")
def check_command(
    files: SourceFiles,
    emit_certificate: Annotated[
        Path | None,
        typer.Option(
            "--emit-certificate",
            metavar="FILE",
            help="écrire le Core IR élaboré et annoté (prélude inclus) en certificat JSON",
        ),
    ] = None,
    output_format: Annotated[
        CheckFormat,
        typer.Option(
            "--format",
            help="text : signatures et erreurs lisibles ; json : diagnostics structurés "
            "(schéma diagnostics-1.0.0) sur la sortie standard",
        ),
    ] = CheckFormat.TEXT,
    langage: Annotated[
        Path | None,
        typer.Option(
            "--langage",
            metavar="DOSSIER",
            help="dossier d'un langage M2 : vérifier les fichiers M1 dans son contexte",
        ),
    ] = None,
    certify: Annotated[
        bool,
        typer.Option("--certify", help="exiger l'acceptation du certificat par Lean"),
    ] = False,
    checker: Annotated[
        Path | None,
        typer.Option("--checker", help="exécutable Lean à utiliser avec --certify"),
    ] = None,
    checker_timeout: Annotated[
        float,
        typer.Option("--checker-timeout", help="délai maximal du vérificateur en secondes"),
    ] = 30.0,
    strict: Annotated[
        bool, typer.Option("--strict", help="refuser les avertissements de filtrage")
    ] = False,
) -> None:
    """Typer des fichiers et afficher leurs signatures."""
    _exit_with(
        _check(
            files,
            output_format,
            langage,
            emit_certificate,
            certify,
            checker,
            checker_timeout,
            strict,
        )
    )


@app.command("repl")
def repl_command() -> None:
    """Boucle interactive (toplevel)."""
    _exit_with(_repl(Session()))


@plugins_app.command("list")
def plugins_list_command(
    manifest: ManifestPaths = None,
    role: Annotated[
        str | None, typer.Option("--role", help="filtrer par rôle (ex. Solver, Observer)")
    ] = None,
) -> None:
    """Lister toutes les versions des extensions en JSON, sans résoudre leurs dépendances."""
    _exit_with(_plugins(manifest or [], role=role))


@plugins_app.command("show")
def plugins_show_command(
    identifier: Annotated[str, typer.Argument(help="identifiant de l'extension")],
    manifest: ManifestPaths = None,
    version: Annotated[
        str | None, typer.Option("--version", help="version exacte ; défaut : la plus récente")
    ] = None,
) -> None:
    """Afficher un manifeste complet en JSON, sans charger ni exécuter son backend."""
    _exit_with(_plugins(manifest or [], identifier=identifier, version=version))


@app.command("lancer")
def lancer_command(
    langage: Annotated[Path, typer.Argument(help="dossier du langage M2")],
    programme: Annotated[
        Path | None,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="programme M1 (.hyp)"),
    ] = None,
    demande: Annotated[
        str | None,
        typer.Option("--demande", help="demande en langage naturel, transcrite en programme M1"),
    ] = None,
    mode: Annotated[
        Mode, typer.Option("--mode", help="mode d'exécution des effets")
    ] = Mode.DRY_RUN,
    sortie: Annotated[Path, typer.Option("--sortie", help="résultats M0")] = Path("demo/sortie"),
    env: Annotated[
        list[str] | None,
        typer.Option(
            "--env",
            metavar="CLE=VALEUR",
            help="option de l'environnement (adaptateurs) ; répétable",
        ),
    ] = None,
    sans_permission: Annotated[
        bool, typer.Option("--sans-permission", help="n'accorder aucune permission")
    ] = False,
    generated: Annotated[
        bool, typer.Option("--generated", help="fichier généré : Record reste Hypothesis")
    ] = False,
    output_format: Annotated[
        CheckFormat,
        typer.Option("--format", help="text : rapport lisible ; json : résultat versionné"),
    ] = CheckFormat.TEXT,
) -> None:
    """Exécuter un programme M1 écrit dans un langage M2 (entrée langage.hyp)."""
    _exit_with(
        _lancer(
            langage,
            programme,
            demande,
            mode,
            sortie,
            env or [],
            sans_permission,
            generated,
            output_format,
        )
    )


@app.command("layers")
def layers_command(
    langage: Annotated[Path, typer.Argument(help="dossier ou fichier d'entrée du langage")],
) -> None:
    """Exporter le DAG des couches, de la dépendance vers son utilisateur, en JSON."""
    from hypomnesis.engine.layers import resolve_layers

    try:
        print(json.dumps(resolve_layers(langage).to_json(), indent=2, ensure_ascii=False))
    except (LanguageError, HypomnesisError) as exc:
        message = exc.render() if isinstance(exc, HypomnesisError) else str(exc)
        print(f"refusé : {message}", file=sys.stderr)
        raise typer.Exit(1) from exc


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return its exit status (never raises ``SystemExit``).

    Typer runs in standalone mode, so usage errors get their rich rendering and exit with
    Click's status (2); that exit is converted into the returned integer.
    """
    try:
        app(args=argv, prog_name="hypomnesis")
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else int(stop.code is not None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
