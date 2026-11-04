"""Diagnostics shared by every stage of the language pipeline."""

from __future__ import annotations

from dataclasses import dataclass

MAX_LINE = 100


@dataclass(frozen=True)
class Span:
    line: int
    column: int
    end_line: int
    end_column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


DIAGNOSTICS_VERSION = "1.0.0"
DIAGNOSTICS_SCHEMA_ID = f"https://schemas.example.org/hypomnesis/diagnostics/{DIAGNOSTICS_VERSION}"


class HypomnesisError(Exception):
    """Base error carrying a stage name and an optional source span."""

    stage = "error"
    # Stable machine identifier of the stage (``stage`` is the human label of the text output).
    # Subclasses that do not override it report as the generic ``error``.
    stage_id = "error"
    severity = "error"

    def __init__(self, message: str, span: Span | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.span = span

    def render(self, source: str | None = None, filename: str = "<input>") -> str:
        """Format the error with the offending source line underlined."""
        location = f"{filename}:{self.span}" if self.span else filename
        text = f"{location}: {self.stage}: {self.message}"
        if source is None or self.span is None:
            return text
        lines = source.splitlines()
        if not 1 <= self.span.line <= len(lines):
            return text
        line = lines[self.span.line - 1]
        start = self.span.column
        end = self.span.end_column if self.span.end_line == self.span.line else len(line) + 1
        if len(line) > MAX_LINE:  # prose or minified input: keep the diagnostic readable
            if start > MAX_LINE:
                return f"{text}\n  {line[:MAX_LINE]}…"
            line, end = line[:MAX_LINE] + "…", min(end, MAX_LINE + 1)
        width = max(1, end - start)
        return f"{text}\n  {line}\n  {' ' * (start - 1)}{'^' * width}"

    def to_diagnostic(self, filename: str = "<input>") -> dict[str, object]:
        """The error as a JSON-ready diagnostic (see the ``diagnostics`` schema).

        Positions are 1-based; they are ``None`` when the error carries no span.
        """
        span = self.span
        return {
            "stage": self.stage_id,
            "severity": self.severity,
            "message": self.message,
            "file": filename,
            "line": span.line if span else None,
            "column": span.column if span else None,
            "end_line": span.end_line if span else None,
            "end_column": span.end_column if span else None,
        }


class CompilerWarning(HypomnesisError):
    stage = "pattern warning"
    stage_id = "pattern"
    severity = "warning"

    def __init__(self, message: str, span: Span | None = None, filename: str | None = None) -> None:
        super().__init__(message, span)
        self.filename = filename

    def render(self, source: str | None = None, filename: str | None = None) -> str:
        return super().render(source, filename or self.filename or "<input>")

    def to_diagnostic(self, filename: str | None = None) -> dict[str, object]:
        return super().to_diagnostic(filename or self.filename or "<input>")


def diagnostics_document(diagnostics: list[dict[str, object]]) -> dict[str, object]:
    """Wrap diagnostics in the versioned document published by ``check --format json``."""
    return {"version": DIAGNOSTICS_VERSION, "diagnostics": diagnostics}


class ParseError(HypomnesisError):
    stage = "syntax error"
    stage_id = "syntax"


class NameResolutionError(HypomnesisError):
    stage = "name error"
    stage_id = "name"


class TypeCheckError(HypomnesisError):
    stage = "type error"
    stage_id = "type"


class EvaluationError(HypomnesisError):
    stage = "runtime error"
    stage_id = "runtime"
