"""Command-line interface (Typer): one function per ``hypomnesis`` subcommand."""

from __future__ import annotations

import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from hypomnesis import __version__
from hypomnesis.language.errors import HypomnesisError, diagnostics_document
from hypomnesis.session import Session


def _load_files(
    session: Session, paths: list[Path], *, execute: bool, as_json: bool = False
) -> int:
    """Load files in order; with ``as_json``, stdout carries only the diagnostics document."""
    for path in paths:
        source = path.read_text(encoding="utf-8")
        try:
            result = session.load(source) if execute else session.check(source)
        except HypomnesisError as exc:
            if as_json:
                print(json.dumps(diagnostics_document([exc.to_diagnostic(str(path))])))
            else:
                print(exc.render(source, str(path)), file=sys.stderr)
            return 1
        if not as_json:
            for binding in result.bindings:
                print(binding.render() if execute else binding.render_signature())
    if as_json:
        print(json.dumps(diagnostics_document([])))
    return 0


def _check(
    files: list[Path],
    output_format: CheckFormat,
    langage: Path | None,
    emit_certificate: Path | None,
) -> int:
    """Type-check files, alone or in the context of a M2 language."""
    session = Session()
    if langage is not None:
        from hypomnesis.engine.language import LanguageError, load_language

        try:
            session = load_language(langage).session
        except (LanguageError, HypomnesisError) as exc:
            message = exc.render() if isinstance(exc, HypomnesisError) else str(exc)
            print(f"refusé : {message}", file=sys.stderr)
            return 1
    status = _load_files(session, files, execute=False, as_json=output_format is CheckFormat.JSON)
    if status == 0 and emit_certificate is not None:
        status = _emit_certificate(session, emit_certificate)
    return status


def _emit_certificate(session: Session, path: Path) -> int:
    """Write the session's certificate, validated against its JSON Schema."""
    from hypomnesis.certify import CERTIFICATE_SCHEMA_ID, CertificateError, session_certificate
    from hypomnesis.contracts.registry import SchemaRegistry

    try:
        certificate = session_certificate(session)
    except CertificateError as exc:
        print(f"certificate: {exc}", file=sys.stderr)
        return 1
    issues = SchemaRegistry.with_builtin_schemas().issues(CERTIFICATE_SCHEMA_ID, certificate)
    if issues:
        print("certificate: invalid against its schema", file=sys.stderr)
        for issue in issues[:10]:
            print(f"  {issue}", file=sys.stderr)
        return 1
    path.write_text(json.dumps(certificate, ensure_ascii=False), encoding="utf-8")
    print(f"certificate: {len(session.definitions)} definitions -> {path}", file=sys.stderr)
    return 0


def _pairs(items: list[str]) -> dict[str, str]:
    return dict(item.split("=", 1) for item in items if "=" in item)


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
    """Output format of ``check``."""

    TEXT = "text"
    JSON = "json"


class Format(StrEnum):
    """Output format of ``decrire``."""

    MD = "md"
    JSON = "json"


def _lancer(
    langage: Path,
    programme: Path | None,
    demande: str | None,
    mode: Mode,
    sortie: Path,
    env: list[str],
    sans_permission: bool,
) -> int:
    from hypomnesis.engine.language import LanguageError, load_language
    from hypomnesis.engine.procedure import render, run_procedure

    try:
        language = load_language(langage)
        if programme is not None:
            program = programme.read_text(encoding="utf-8")
        elif demande is not None and "transcriber" in language.manifest:
            program = language.adapter(language.manifest["transcriber"])(demande)
        else:
            print("un programme M1 ou une --demande transcriptible est requis", file=sys.stderr)
            return 64
        report = run_procedure(
            language,
            program,
            mode=mode.value,
            out_dir=sortie,
            environment=_pairs(env),
            permissions=frozenset() if sans_permission else None,
        )
        print(render(report))
        return 0
    except (LanguageError, HypomnesisError, ValueError) as exc:
        if isinstance(exc, HypomnesisError):
            message = exc.render(None, str(programme or "<programme>"))
        else:
            message = str(exc)
        print(f"refusé : {message}", file=sys.stderr)
        return 1


def _decrire(langage: Path, output_format: Format) -> int:
    from dataclasses import asdict

    from hypomnesis.engine.language import LanguageError, load_language
    from hypomnesis.llm.describe import catalogue

    try:
        published = catalogue(load_language(langage))
    except LanguageError as exc:
        print(f"refusé : {exc}", file=sys.stderr)
        return 1
    text = (
        json.dumps(asdict(published), indent=2, ensure_ascii=False)
        if output_format is Format.JSON
        else published.render()
    )
    print(text)
    print(f"-- {len(text)} caractères (≈ {len(text) // 3} jetons)", file=sys.stderr)
    return 0


def _benchmark(
    langages: list[Path],
    modeles: str,
    reparations: int,
    strategie: str,
    jeux: str,
    sortie: Path,
    graphiques: bool = True,
) -> int:
    from datetime import datetime

    from hypomnesis.llm.benchmark import run_benchmark, summary
    from hypomnesis.llm.ollama import OllamaClient
    from hypomnesis.llm.prompting import Strategy

    models = [m.strip() for m in modeles.split(",") if m.strip()]
    results = run_benchmark(
        OllamaClient(),
        models,
        langages,
        repairs=reparations,
        strategy=Strategy.parse(strategie),
        splits=[j.strip() for j in jeux.split(",")] if jeux else None,
    )
    table = summary(results)
    sortie.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rows = [r.to_json() for r in results]
    (sortie / f"resultats-{stamp}.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (sortie / f"resume-{stamp}.md").write_text(table + "\n", encoding="utf-8")
    print("\n" + table)
    if graphiques:
        try:
            from hypomnesis.llm.plots import normalize, render_all
        except ImportError:
            print("graphiques ignorés : matplotlib absent (extra « llm »)", file=sys.stderr)
        else:
            for path in render_all([normalize(r) for r in rows], sortie, f"resultats-{stamp}"):
                print(f"graphique : {path}", file=sys.stderr)
    return 0


def _graphiques(fichier: Path, sortie: Path | None) -> int:
    from hypomnesis.llm.plots import ResultsError, load_results, render_all

    try:
        results = load_results(fichier)
    except ResultsError as exc:
        print(f"graphiques-llm : {exc}", file=sys.stderr)
        return 1
    written = render_all(results, sortie if sortie is not None else fichier.parent, fichier.stem)
    if not written:
        print(f"graphiques-llm : {fichier} ne contient aucun résultat", file=sys.stderr)
        return 1
    for path in written:
        print(path)
    return 0


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
    _exit_with(_load_files(Session(), files, execute=True))


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
) -> None:
    """Typer des fichiers et afficher leurs signatures."""
    _exit_with(_check(files, output_format, langage, emit_certificate))


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
    sortie: Annotated[Path, typer.Option("--sortie", help="résultats M0")] = Path("sortie"),
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
) -> None:
    """Exécuter un programme M1 écrit dans un langage M2 (dossier avec langage.json)."""
    _exit_with(_lancer(langage, programme, demande, mode, sortie, env or [], sans_permission))


@app.command("decrire")
def decrire_command(
    langage: Annotated[Path, typer.Argument(help="dossier du langage M2")],
    output_format: Annotated[
        Format, typer.Option("--format", help="format de sortie du catalogue")
    ] = Format.MD,
) -> None:
    """Exporter ce que le langage M2 dit de lui-même (catalogue du prompt LLM)."""
    _exit_with(_decrire(langage, output_format))


@app.command("benchmark-llm")
def benchmark_command(
    langages: Annotated[
        list[Path],
        typer.Argument(exists=True, file_okay=False, help="dossiers de langages (benchmark.json)"),
    ],
    modeles: Annotated[
        str,
        typer.Option("--modeles", help="modèles Ollama, séparés par des virgules"),
    ],
    reparations: Annotated[
        int, typer.Option("--reparations", help="réparations par les diagnostics")
    ] = 2,
    strategie: Annotated[
        str,
        typer.Option(
            "--strategie",
            help="prompt : éléments joints par « + » parmi source, catalogue, programmes, "
            "tirsN, ragN (ex. catalogue+rag3) ; « defaut » = catalogue+rag5, "
            "« base » = source+programmes",
        ),
    ] = "defaut",
    jeux: Annotated[
        str,
        typer.Option(
            "--jeux",
            help="jeux de cas (dev, test, hard), séparés par des virgules ; défaut : tous",
        ),
    ] = "",
    sortie: Annotated[Path, typer.Option("--sortie", help="dossier des résultats")] = Path(
        "sortie/benchmark-llm"
    ),
    graphiques: Annotated[
        bool,
        typer.Option(
            "--graphiques/--sans-graphiques",
            help="écrire les figures (PNG et SVG, matplotlib) à côté du résumé",
        ),
    ] = True,
) -> None:
    """Mesurer la traduction langage naturel → programme M1 par des LLM."""
    _exit_with(_benchmark(langages, modeles, reparations, strategie, jeux, sortie, graphiques))


@app.command("graphiques-llm")
def graphiques_command(
    fichier: Annotated[
        Path,
        typer.Argument(
            exists=True, dir_okay=False, readable=True, help="resultats-*.json de benchmark-llm"
        ),
    ],
    sortie: Annotated[
        Path | None,
        typer.Option("--sortie", help="dossier des figures ; défaut : celui du fichier"),
    ] = None,
) -> None:
    """Régénérer les figures (PNG et SVG) d'un lot de résultats, sans relancer le banc."""
    _exit_with(_graphiques(fichier, sortie))


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
