"""Static editor checks using fresh compiler sessions, never language adapters."""

from __future__ import annotations

from pathlib import Path

from lsprotocol import types

from hypomnesis.engine.errors import LanguageError, SourceError
from hypomnesis.engine.layers import ENTRY, check_layers, resolve_layers
from hypomnesis.language import ast as A
from hypomnesis.language.errors import HypomnesisError, Span
from hypomnesis.language.parser import parse_program
from hypomnesis.session import Session


def language_root(path: Path, workspace: Path, configured: str | None) -> Path | None:
    if configured:
        root = Path(configured)
        return (root if root.is_absolute() else workspace / root).resolve()
    for parent in path.parents:
        if (parent / ENTRY).is_file():
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
                if (candidate / ENTRY).is_file():
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
    message: str,
    stage: str,
    span: Span | None,
    source: str,
    encoding: str = "utf-16",
    *,
    severity: types.DiagnosticSeverity = types.DiagnosticSeverity.Error,
) -> types.Diagnostic:
    start = _position(source, span.line, span.column, encoding) if span else types.Position(0, 0)
    end = _position(source, span.end_line, span.end_column, encoding) if span else start
    return types.Diagnostic(
        range=types.Range(start=start, end=end),
        message=message,
        severity=severity,
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
    try:
        session = Session(execute_prelude=False)
        program = parse_program(source)
        declares_language = any(isinstance(item, A.LanguageItem) for item in program.items)
        root = path if declares_language else language_root(path, workspace, configured)
        if root is not None:
            plan = resolve_layers(root, {**overlays, str(path): source}, stop_at=path)
            owner = next(
                (
                    entry
                    for entry, layer in plan.layers.items()
                    if any(item.path == path for item in layer.sources)
                ),
                None,
            )
            session = check_layers(plan, strict=False, stop_at=path, entry=owner, overlays=overlays)
            if owner is not None:
                return _warnings(session, path, source, encoding)
        session.check_program(program, filename=str(path), overlays=overlays, source_text=source)
    except SourceError as exc:
        if exc.path == path:
            return [diagnostic(exc.message, exc.stage_id, exc.span, source, encoding)]
        return [diagnostic(exc.render(), exc.stage_id, None, source)]
    except HypomnesisError as exc:
        return [diagnostic(exc.message, exc.stage_id, exc.span, source, encoding)]
    except (OSError, UnicodeError, LanguageError) as exc:
        return [diagnostic(str(exc), "configuration", None, source)]
    return _warnings(session, path, source, encoding)


def _warnings(session: Session, path: Path, source: str, encoding: str) -> list[types.Diagnostic]:
    return [
        diagnostic(
            warning.message,
            warning.stage_id,
            warning.span,
            source,
            encoding,
            severity=types.DiagnosticSeverity.Warning,
        )
        for warning in session.warnings
        if warning.filename == str(path)
    ]
