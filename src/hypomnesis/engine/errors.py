"""Errors at the boundary between language packages and compiler sessions."""

from __future__ import annotations

from pathlib import Path

from hypomnesis.language.docs import Declaration
from hypomnesis.language.errors import HypomnesisError


class LanguageError(ValueError):
    pass


class SourceError(HypomnesisError, LanguageError):
    """A compiler error with the original package source, not the importing file."""

    def __init__(self, error: HypomnesisError, path: Path, source: str) -> None:
        super().__init__(error.message, error.span)
        self.stage, self.stage_id = error.stage, error.stage_id
        self.path, self.source = path, source

    def __str__(self) -> str:
        return self.render()

    def render(self, source: str | None = None, filename: str = "<input>") -> str:
        return super().render(self.source, str(self.path))

    def to_diagnostic(self, filename: str = "<input>") -> dict[str, object]:
        return super().to_diagnostic(str(self.path))


class MissingDescriptionError(HypomnesisError, LanguageError):
    stage = "description error"

    def __init__(self, declaration: Declaration, filename: str) -> None:
        super().__init__(
            f"{declaration.kind} {declaration.path} has no description: "
            "add a (** … *) comment before it, tag it @interne or prefix its name with _",
            declaration.span,
        )
        self.declaration = declaration
        self.filename = filename

    def __str__(self) -> str:
        where = f"{self.filename}:{self.span}" if self.span else self.filename
        return f"{where}: {self.stage}: {self.message}"

    def render(self, source: str | None = None, filename: str | None = None) -> str:
        return super().render(source, filename or self.filename)
