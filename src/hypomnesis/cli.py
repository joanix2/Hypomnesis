"""Command-line interface: ``hypomnesis run|check|repl``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hypomnesis import __version__
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.session import Session


def _load_files(session: Session, paths: list[Path], *, execute: bool) -> int:
    for path in paths:
        source = path.read_text(encoding="utf-8")
        try:
            result = session.load(source) if execute else session.check(source)
        except HypomnesisError as exc:
            print(exc.render(source, str(path)), file=sys.stderr)
            return 1
        for binding in result.bindings:
            print(binding.render() if execute else binding.render_signature())
    return 0


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


def _lancer(args: argparse.Namespace) -> int:
    from hypomnesis.engine.language import LanguageError, load_language
    from hypomnesis.engine.procedure import render, run_procedure

    try:
        language = load_language(args.langage)
        if args.programme is not None:
            program = args.programme.read_text(encoding="utf-8")
        elif args.demande is not None and "transcriber" in language.manifest:
            program = language.adapter(language.manifest["transcriber"])(args.demande)
        else:
            print("un programme M1 ou une --demande transcriptible est requis", file=sys.stderr)
            return 64
        report = run_procedure(
            language,
            program,
            mode=args.mode,
            out_dir=args.sortie,
            environment=_pairs(args.env),
            permissions=frozenset() if args.sans_permission else None,
        )
        print(render(report))
        return 0
    except (LanguageError, HypomnesisError, ValueError) as exc:
        if isinstance(exc, HypomnesisError):
            message = exc.render(None, str(args.programme or "<programme>"))
        else:
            message = str(exc)
        print(f"refusé : {message}", file=sys.stderr)
        return 1


def _decrire(args: argparse.Namespace) -> int:
    from dataclasses import asdict

    from hypomnesis.engine.language import LanguageError, load_language
    from hypomnesis.llm.describe import catalogue

    try:
        published = catalogue(load_language(args.langage))
    except LanguageError as exc:
        print(f"refusé : {exc}", file=sys.stderr)
        return 1
    text = (
        json.dumps(asdict(published), indent=2, ensure_ascii=False)
        if args.format == "json"
        else published.render()
    )
    print(text)
    print(f"-- {len(text)} caractères (≈ {len(text) // 3} jetons)", file=sys.stderr)
    return 0


def _benchmark(args: argparse.Namespace) -> int:
    from datetime import datetime

    from hypomnesis.llm.benchmark import run_benchmark, summary
    from hypomnesis.llm.ollama import OllamaClient
    from hypomnesis.llm.prompting import Strategy

    models = [m.strip() for m in args.modeles.split(",") if m.strip()]
    results = run_benchmark(
        OllamaClient(),
        models,
        args.langages,
        repairs=args.reparations,
        strategy=Strategy.parse(args.strategie),
        splits=[j.strip() for j in args.jeux.split(",")] if args.jeux else None,
    )
    table = summary(results)
    args.sortie.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (args.sortie / f"resultats-{stamp}.json").write_text(
        json.dumps([r.to_json() for r in results], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (args.sortie / f"resume-{stamp}.md").write_text(table + "\n", encoding="utf-8")
    print("\n" + table)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypomnesis", description=__doc__)
    parser.add_argument("--version", action="version", version=f"hypomnesis {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="type-check and evaluate files, in order")
    run.add_argument("files", nargs="+", type=Path)
    check = commands.add_parser("check", help="type-check files and print their signatures")
    check.add_argument("files", nargs="+", type=Path)
    check.add_argument(
        "--emit-certificate",
        metavar="FILE",
        type=Path,
        help="write the elaborated, annotated Core IR (prelude included) as a JSON certificate",
    )
    commands.add_parser("repl", help="interactive toplevel")
    lancer = commands.add_parser(
        "lancer",
        help="exécuter un programme M1 écrit dans un langage M2 (dossier avec langage.json)",
    )
    lancer.add_argument("langage", type=Path, help="dossier du langage M2")
    lancer.add_argument("programme", type=Path, nargs="?", help="programme M1 (.hyp)")
    lancer.add_argument("--demande", help="demande en langage naturel, transcrite en programme M1")
    lancer.add_argument("--mode", choices=["simulate", "dry-run", "production"], default="dry-run")
    lancer.add_argument("--sortie", type=Path, default=Path("sortie"), help="résultats M0")
    lancer.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="CLE=VALEUR",
        help="option de l'environnement (adaptateurs)",
    )
    lancer.add_argument(
        "--sans-permission", action="store_true", help="n'accorder aucune permission"
    )
    decrire = commands.add_parser(
        "decrire",
        help="exporter ce que le langage M2 dit de lui-même (catalogue du prompt LLM)",
    )
    decrire.add_argument("langage", type=Path, help="dossier du langage M2")
    decrire.add_argument("--format", choices=["md", "json"], default="md")
    bench = commands.add_parser(
        "benchmark-llm", help="mesurer la traduction langage naturel → programme M1 par des LLM"
    )
    bench.add_argument(
        "langages", type=Path, nargs="+", help="dossiers de langages (benchmark.json)"
    )
    bench.add_argument("--modeles", required=True, help="modèles Ollama, séparés par des virgules")
    bench.add_argument("--reparations", type=int, default=2, help="réparations par les diagnostics")
    bench.add_argument(
        "--strategie",
        default="defaut",
        help="prompt : éléments joints par « + » parmi source, catalogue, programmes, tirsN, "
        "ragN (ex. catalogue+rag3) ; « defaut » = catalogue+rag5, « base » = source+programmes",
    )
    bench.add_argument(
        "--jeux",
        default="",
        help="jeux de cas (dev, test, hard), séparés par des virgules ; défaut : tous",
    )
    bench.add_argument("--sortie", type=Path, default=Path("sortie/benchmark-llm"))
    args = parser.parse_args(argv)

    if args.command == "lancer":
        return _lancer(args)
    if args.command == "benchmark-llm":
        return _benchmark(args)
    if args.command == "decrire":
        return _decrire(args)
    session = Session()
    if args.command == "repl":
        return _repl(session)
    status = _load_files(session, args.files, execute=args.command == "run")
    if status == 0 and getattr(args, "emit_certificate", None) is not None:
        status = _emit_certificate(session, args.emit_certificate)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
