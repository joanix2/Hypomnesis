"""Minimal tracing: nested spans recorded as JSON-ready dicts (§12.3).

Span names follow the specification (``hypomnesis.run``, ``estimator.predict``,
``solver.solve``, ``actuator.execute``…). This is the in-process stand-in for
OpenTelemetry (HYP-070): same structure, exportable later through OTLP.
Telemetry never feeds back into reasoning (ADR 0005).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    span_id: str
    parent_id: str | None
    start: float
    end: float | None = None
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return round(((self.end or self.start) - self.start) * 1000, 2)


class Tracer:
    def __init__(self) -> None:
        self.trace_id = uuid.uuid4().hex
        self.spans: list[Span] = []
        self._stack: list[Span] = []

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        parent = self._stack[-1].span_id if self._stack else None
        s = Span(name, uuid.uuid4().hex[:16], parent, time.perf_counter(), attributes=attributes)
        self.spans.append(s)
        self._stack.append(s)
        try:
            yield s
        except Exception:
            s.status = "error"
            raise
        finally:
            s.end = time.perf_counter()
            self._stack.pop()

    def tree(self) -> list[str]:
        children: dict[str | None, list[Span]] = {}
        for s in self.spans:
            children.setdefault(s.parent_id, []).append(s)

        def walk(parent: str | None, depth: int) -> list[str]:
            lines = []
            for s in children.get(parent, []):
                mark = "" if s.status == "ok" else f" [{s.status}]"
                lines.append(f"{'  ' * depth}{s.name} ({s.duration_ms} ms){mark}")
                lines.extend(walk(s.span_id, depth + 1))
            return lines

        return walk(None, 0)

    def export(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "spans": [
                {
                    "name": s.name,
                    "span_id": s.span_id,
                    "parent_id": s.parent_id,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "attributes": s.attributes,
                }
                for s in self.spans
            ],
        }
