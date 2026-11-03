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


def _demo(args: argparse.Namespace) -> int:
    from hypomnesis.demos.plaque.pipeline import EXPORT_PERMISSION, TranscriptionError, render, run

    permissions = frozenset() if args.sans_permission else frozenset({EXPORT_PERMISSION})
    try:
        report = run(
            args.demande,
            estimator=args.estimateur,
            mode=args.mode,
            out_dir=args.sortie,
            masse_max=args.masse_max,
            permissions=permissions,
            mesure=args.mesure,
        )
    except (TranscriptionError, HypomnesisError) as exc:
        print(f"demande refusée : {exc}", file=sys.stderr)
        return 1
    print(render(report))
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
    demo = commands.add_parser("demo", help="démonstrateurs de bout en bout")
    demo.add_argument("scenario", choices=["plaque"])
    demo.add_argument(
        "--demande",
        default="Crée une plaque de 120 × 80 mm, estime son épaisseur, "
        "vérifie sa validité et exporte sa géométrie.",
    )
    demo.add_argument("--estimateur", choices=["regle", "abaque"], default="regle")
    demo.add_argument("--mode", choices=["simulate", "dry-run", "production"], default="dry-run")
    demo.add_argument("--sortie", type=Path, default=Path("sortie-plaque"))
    demo.add_argument("--masse-max", type=float, default=0.5, help="kg")
    demo.add_argument("--mesure", type=float, help="épaisseur mesurée ensuite (mm) : révision")
    demo.add_argument("--sans-permission", action="store_true", help="refuser l'export")
    args = parser.parse_args(argv)

    if args.command == "demo":
        return _demo(args)
    session = Session()
    if args.command == "repl":
        return _repl(session)
    status = _load_files(session, args.files, execute=args.command == "run")
    if status == 0 and getattr(args, "emit_certificate", None) is not None:
        status = _emit_certificate(session, args.emit_certificate)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
