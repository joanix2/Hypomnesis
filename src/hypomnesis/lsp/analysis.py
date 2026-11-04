"""Static editor checks using fresh compiler sessions, never language adapters."""

from __future__ import annotations

import json
from pathlib import Path

from lsprotocol import types

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.language import MANIFEST, MANIFEST_SCHEMA, LanguageError
from hypomnesis.language.errors import HypomnesisError, Span
from hypomnesis.session import Session, prelude_source


def language_root(path: Path, workspace: Path, configured: str | None) -> Path | None:
    if configured:
        root = Path(configured)
        return (root if root.is_absolute() else workspace / root).resolve()
    for parent in path.parents:
        if (parent / MANIFEST).is_file():
            return parent
        if parent == workspace:
            break
    for parent in path.parents:
        if not parent.is_relative_to(workspace):
            break
        if parent.name == "programs":
            relative = path.relative_to(parent)
            if len(relative.parts) > 1:
                candidate = parent.parent / "languages" / relative.parts[0]
                if (candidate / MANIFEST).is_file():
                    return candidate
    return None


def _position(source: str, line: int, column: int, encoding: str) -> types.Position:
    lines = source.split("\n")
    row = min(max(0, line - 1), len(lines) - 1)
    prefix = lines[row][: max(0, column - 1)]
    if encoding == "utf-8":
        character = len(prefix.encode("utf-8"))
    elif encoding == "utf-32":
        character = len(prefix)
    else:
        character = len(prefix.encode("utf-16-le")) // 2
    return types.Position(line=row, character=character)


def diagnostic(
    message: str, stage: str, span: Span | None, source: str, encoding: str = "utf-16"
) -> types.Diagnostic:
    start = _position(source, span.line, span.column, encoding) if span else types.Position(0, 0)
    end = _position(source, span.end_line, span.end_column, encoding) if span else start
    return types.Diagnostic(
        range=types.Range(start=start, end=end),
        message=message,
        severity=types.DiagnosticSeverity.Error,
        source="hypomnesis",
        code=stage,
    )


def analyze(
    path: Path,
    source: str,
    workspace: Path,
    configured: str | None,
    overlays: dict[str, str],
    encoding: str = "utf-16",
) -> list[types.Diagnostic]:
    """Check preceding M2 files, then the unsaved target, with no user evaluation."""
    path = path.resolve()
    current_path, current_source = path, source
    try:
        session = Session(prelude=False)
        session.check(prelude_source())
        root = language_root(path, workspace, configured)
        if root is not None:
            manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
            issues = SchemaRegistry.with_builtin_schemas().issues(MANIFEST_SCHEMA, manifest)
            if issues:
                raise LanguageError("manifeste invalide : " + "; ".join(map(str, issues)))
            for name in manifest["sources"]:
                dependency = (root / name).resolve()
                if not dependency.is_relative_to(root):
                    raise LanguageError(f"source hors du paquet du langage : {name}")
                if dependency == path:
                    break
                current_path = dependency
                current_source = (
                    overlays[str(dependency)]
                    if str(dependency) in overlays
                    else dependency.read_text(encoding="utf-8")
                )
                session.check(current_source)
        current_path, current_source = path, source
        session.check(source)
    except HypomnesisError as exc:
        if current_path == path:
            return [diagnostic(exc.message, exc.stage_id, exc.span, current_source, encoding)]
        return [
            diagnostic(
                f"{current_path}: {exc}",
                exc.stage_id,
                None,
                source,
            )
        ]
    except (OSError, UnicodeError, json.JSONDecodeError, LanguageError) as exc:
        return [diagnostic(str(exc), "configuration", None, source)]
    return []
