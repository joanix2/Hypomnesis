"""Prompting strategies for the translation, as a small composable specification.

A strategy says what the model is shown besides the rules and the request:

- ``source``      the language's Hypomnesis source, comments included;
- ``catalogue``   the catalogue compiled from its self-documentation (docs, tags, types);
- ``programmes``  the static example programs listed by the benchmark/language;
- ``tirsN``       the first N worked examples (request → program) as chat turns;
- ``ragN``        the N worked examples most similar to the request, as chat turns.

Spec syntax: tokens joined by ``+``, e.g. ``catalogue+rag3``. ``base`` is the historical
prompt (``source+programmes``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Strategy:
    source: bool = True
    catalogue: bool = False
    programs: bool = True
    shots: int = 0
    retrieval: bool = False

    @classmethod
    def parse(cls, spec: str) -> Strategy:
        if spec == "base":
            return cls()
        source = catalogue = programs = retrieval = False
        shots = 0
        for token in (t.strip() for t in spec.split("+") if t.strip()):
            match = re.fullmatch(r"(tirs|rag)(\d+)", token)
            if match:
                shots, retrieval = int(match.group(2)), match.group(1) == "rag"
            elif token == "source":
                source = True
            elif token == "catalogue":
                catalogue = True
            elif token == "programmes":
                programs = True
            else:
                raise ValueError(f"élément de stratégie inconnu : {token!r}")
        return cls(source, catalogue, programs, shots, retrieval)

    def __str__(self) -> str:
        parts = [
            name for name, on in (("source", self.source), ("catalogue", self.catalogue)) if on
        ]
        if self.programs:
            parts.append("programmes")
        if self.shots:
            parts.append(f"{'rag' if self.retrieval else 'tirs'}{self.shots}")
        return "+".join(parts) or "rien"


BASE = Strategy()
