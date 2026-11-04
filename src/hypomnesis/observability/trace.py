"""Tracing facade over the OpenTelemetry SDK (§12.3, HYP-015).

Span names follow the specification (``hypomnesis.run``, ``estimator.predict``,
``solver.solve``, ``actuator.execute``…). Each :class:`Tracer` owns a private
``TracerProvider`` with an in-memory exporter: the span tree and the JSON export
of the M0 reports are rebuilt from the finished spans. No global provider is
ever installed, so tracers cannot see each other's spans. Exporting through OTLP
to a collector is HYP-070.

Telemetry never feeds back into reasoning (ADR 0005): ``Tracer(enabled=False)``
uses a no-op provider and changes no result.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace as otel
from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.id_generator import IdGenerator, RandomIdGenerator
from opentelemetry.trace import NoOpTracerProvider, Span, SpanContext, Status, StatusCode

_SCOPE = "hypomnesis"
_OTEL_TYPES = (str, bool, int, float)


class _FixedTraceId(IdGenerator):
    """Random span ids under a trace id fixed up front (known before any span exists)."""

    def __init__(self, trace_id: int) -> None:
        self._trace_id = trace_id
        self._random = RandomIdGenerator()

    def generate_span_id(self) -> int:
        return self._random.generate_span_id()

    def generate_trace_id(self) -> int:
        return self._trace_id


def _attribute(value: Any) -> str | bool | int | float:
    # OpenTelemetry only accepts scalar attribute values; anything else is rendered.
    return value if isinstance(value, _OTEL_TYPES) else repr(value)


def _hex_id(value: int, width: int) -> str:
    return format(value, f"0{width}x")


class Tracer:
    def __init__(self, enabled: bool = True) -> None:
        trace_id = RandomIdGenerator().generate_trace_id()
        self.trace_id = _hex_id(trace_id, 32)
        self.enabled = enabled
        self._exporter = InMemorySpanExporter()
        provider: otel.TracerProvider
        if enabled:
            sdk_provider = TracerProvider(id_generator=_FixedTraceId(trace_id))
            sdk_provider.add_span_processor(SimpleSpanProcessor(self._exporter))
            provider = sdk_provider
        else:
            provider = NoOpTracerProvider()
        self._tracer = provider.get_tracer(_SCOPE)
        self._stack: list[Span] = []

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        # The parent is explicit (own stack, never the ambient context), and a root
        # starts from an empty context, so a span of another tracer is never adopted.
        parent = otel.set_span_in_context(self._stack[-1]) if self._stack else Context()
        s = self._tracer.start_span(
            name,
            context=parent,
            attributes={k: _attribute(v) for k, v in attributes.items()},
            record_exception=False,
            set_status_on_exception=False,
        )
        self._stack.append(s)
        try:
            yield s
        except Exception as exc:
            s.record_exception(exc)
            s.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            self._stack.pop()
            s.end()

    def current_context(self) -> SpanContext:
        """Context of the innermost open span (invalid when none is open)."""
        return self._stack[-1].get_span_context() if self._stack else otel.INVALID_SPAN_CONTEXT

    @property
    def spans(self) -> Sequence[ReadableSpan]:
        """Finished spans, in start order."""
        return sorted(self._exporter.get_finished_spans(), key=lambda s: s.start_time or 0)

    def tree(self) -> list[str]:
        children: dict[int | None, list[ReadableSpan]] = {}
        for s in self.spans:
            children.setdefault(_parent_id(s), []).append(s)

        def walk(parent: int | None, depth: int) -> list[str]:
            lines = []
            for s in children.get(parent, []):
                mark = "" if _status(s) == "ok" else f" [{_status(s)}]"
                lines.append(f"{'  ' * depth}{s.name} ({_duration_ms(s)} ms){mark}")
                lines.extend(walk(_span_id(s), depth + 1))
            return lines

        return walk(None, 0)

    def export(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "spans": [
                {
                    "name": s.name,
                    "span_id": _hex_id(_span_id(s), 16),
                    "parent_id": None if s.parent is None else _hex_id(s.parent.span_id, 16),
                    "duration_ms": _duration_ms(s),
                    "status": _status(s),
                    "attributes": dict(s.attributes or {}),
                }
                for s in self.spans
            ],
        }


def _span_id(s: ReadableSpan) -> int:
    # A finished SDK span always has a context; the type merely allows None.
    ctx = s.get_span_context()
    if ctx is None:
        raise ValueError(f"span {s.name!r} has no context")
    return ctx.span_id


def _parent_id(s: ReadableSpan) -> int | None:
    return None if s.parent is None else s.parent.span_id


def _status(s: ReadableSpan) -> str:
    return "error" if s.status.status_code is StatusCode.ERROR else "ok"


def _duration_ms(s: ReadableSpan) -> float:
    return round(((s.end_time or 0) - (s.start_time or 0)) / 1e6, 2)


def trace_context(tracer: Tracer) -> dict[str, str]:
    """W3C ``traceparent`` of the current span, as the message envelope expects (§9.6).

    Outside any span (or with telemetry disabled) the span id is all zeros and the
    sampled flag is off: the trace id is still the tracer's, so messages stay correlated.
    """
    ctx = tracer.current_context()
    if ctx.is_valid:
        flags = _hex_id(int(ctx.trace_flags), 2)
        return {"traceparent": f"00-{tracer.trace_id}-{_hex_id(ctx.span_id, 16)}-{flags}"}
    return {"traceparent": f"00-{tracer.trace_id}-{'0' * 16}-00"}
