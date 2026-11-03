"""Diagnostics shared by every stage of the language pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    line: int
    column: int
    end_line: int
    end_column: int

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


class HypomnesisError(Exception):
    """Base error carrying a stage name and an optional source span."""

    stage = "error"

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
        width = max(1, end - start)
        return f"{text}\n  {line}\n  {' ' * (start - 1)}{'^' * width}"


class ParseError(HypomnesisError):
    stage = "syntax error"


class NameResolutionError(HypomnesisError):
    stage = "name error"


class TypeCheckError(HypomnesisError):
    stage = "type error"


class EvaluationError(HypomnesisError):
    stage = "runtime error"
