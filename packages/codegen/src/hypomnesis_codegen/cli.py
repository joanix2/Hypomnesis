"""Standalone CLI for natural-language program generation tooling."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from hypomnesis.engine.language import LanguageError, load_language


class Format(StrEnum):
    MD = "md"
    JSON = "json"


def _decrire(langage: Path, output_format: Format, plugin_paths: list[Path] | None = None) -> int:
    from hypomnesis.engine.registry import ExtensionRegistry, RegistryError
    from hypomnesis_codegen.describe import catalogue

    try:
        plugins = ExtensionRegistry()
        plugins.load_paths(plugin_paths or [])
        published = catalogue(load_language(langage, execute=False), plugins=plugins)
    except (LanguageError, RegistryError) as exc:
        print(f"refusé : {exc}", file=sys.stderr)
        return 1
    text = (
        json.dumps(published.to_json(), indent=2, ensure_ascii=False, allow_nan=False)
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
    from hypomnesis_codegen.benchmark import run_benchmark, summary
    from hypomnesis_codegen.ollama import OllamaClient
    from hypomnesis_codegen.prompting import Strategy

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
        from hypomnesis_codegen.plots import normalize, render_all

        for path in render_all([normalize(r) for r in rows], sortie, f"resultats-{stamp}"):
            print(f"graphique : {path}", file=sys.stderr)
    return 0


def _graphiques(fichier: Path, sortie: Path | None) -> int:
    from hypomnesis_codegen.plots import ResultsError, load_results, render_all

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


app = typer.Typer(
    name="hypomnesis-codegen",
    help="Génération de programmes et outils LLM, séparés du moteur symbolique.",
    add_completion=False,
)


def _exit_with(status: int) -> None:
    if status != 0:
        raise typer.Exit(status)


@app.command("decrire")
def decrire_command(
    langage: Annotated[Path, typer.Argument(help="dossier du langage M2")],
    output_format: Annotated[
        Format, typer.Option("--format", help="format de sortie du catalogue")
    ] = Format.MD,
    plugins: Annotated[
        list[Path] | None,
        typer.Option("--plugin", help="manifeste ou dossier de plugins publié par l'hôte"),
    ] = None,
) -> None:
    """Exporter ce que le langage M2 dit de lui-même (catalogue du prompt LLM)."""
    _exit_with(_decrire(langage, output_format, plugins))


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
        "demo/sortie/benchmark-llm"
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
    """Run the CLI, returning Click's exit status without raising ``SystemExit``."""
    try:
        app(args=argv, prog_name="hypomnesis-codegen")
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else int(stop.code is not None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
