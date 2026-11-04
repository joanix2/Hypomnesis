"""Retrieval of similar worked examples (RAG) for the translation prompt.

A language ships pairs ``{request, program}`` (``examples`` in its manifest). For a new
request, the most similar pairs are shown to the model as demonstrations. Similarity is
lexical (TF-IDF over character n-grams) and blind to numbers: two requests are close when
they are phrased alike — same units, same keywords — not when they share a value.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from hypomnesis.engine.language import Language, LanguageError

EXAMPLES_SCHEMA = "https://schemas.example.org/hypomnesis/language-examples/1.0.0"


@dataclass(frozen=True)
class Example:
    request: str
    program: str
    environment: dict[str, Any] = field(default_factory=dict)


def load_examples(language: Language) -> list[Example]:
    """The worked examples a language ships ([] if it ships none), validated by their schema."""
    reference = language.manifest.get("examples")
    if not reference:
        return []
    data = json.loads((language.root / reference).read_text(encoding="utf-8"))
    issues = language.schemas.issues(EXAMPLES_SCHEMA, data)
    if issues:
        raise LanguageError(f"exemples invalides ({reference}) : " + "; ".join(map(str, issues)))
    return [Example(d["request"], d["program"], d.get("environment", {})) for d in data]


def _normalise(text: str) -> str:
    return re.sub(r"\d+([.,]\d+)?", "0", text.lower())


class Retriever:
    def __init__(self, examples: Sequence[Example]) -> None:
        self.examples = list(examples)
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, strip_accents="unicode"
        )
        self._matrix = (
            self._vectorizer.fit_transform(_normalise(e.request) for e in self.examples)
            if self.examples
            else None
        )

    def top(self, request: str, k: int) -> list[Example]:
        """The ``k`` examples most similar to the request, most similar last (closest to it)."""
        if self._matrix is None or k <= 0:
            return []
        scores = cosine_similarity(self._vectorizer.transform([_normalise(request)]), self._matrix)
        order = scores[0].argsort()[::-1][:k]
        return [self.examples[i] for i in reversed(order)]
