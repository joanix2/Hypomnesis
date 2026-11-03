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
    args = parser.parse_args(argv)

    if args.command == "lancer":
        return _lancer(args)
    session = Session()
    if args.command == "repl":
        return _repl(session)
    status = _load_files(session, args.files, execute=args.command == "run")
    if status == 0 and getattr(args, "emit_certificate", None) is not None:
        status = _emit_certificate(session, args.emit_certificate)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
