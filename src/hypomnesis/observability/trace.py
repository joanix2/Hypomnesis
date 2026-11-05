"""Tracing facade over the OpenTelemetry SDK (§12.3, HYP-015/070).

Span names follow the specification (``hypomnesis.run``, ``estimator.predict``,
``solver.solve``, ``actuator.execute``…). Each :class:`Tracer` owns a private
``TracerProvider`` with an in-memory exporter: the span tree and the JSON export
of the M0 reports are rebuilt from the finished spans. No global provider is
ever installed, so tracers cannot see each other's spans. Optional OTLP/HTTP
export is explicitly local, with bounded requests and no redirects or proxies.

Telemetry never feeds back into reasoning (ADR 0005): ``Tracer(enabled=False)``
uses a no-op provider and changes no result.
"""

from __future__ import annotations

import logging
import math
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack, contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace as otel
from opentelemetry.context import Context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.id_generator import IdGenerator, RandomIdGenerator
from opentelemetry.trace import NoOpTracerProvider, Span, SpanContext, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from hypomnesis.observability.metrics import Metrics, OperationMetrics
from hypomnesis.observability.otlp import local_session, validate_endpoint

_SCOPE = "hypomnesis"
_OTEL_TYPES = (str, bool, int, float)
_ACTIVE: ContextVar[Tracer | None] = ContextVar("hypomnesis_tracer", default=None)
_PROPAGATOR = TraceContextTextMapPropagator()


@dataclass(frozen=True)
class TraceConfig:
    enabled: bool = True
    otlp_endpoint: str | None = None
    timeout_seconds: float = 3.0
    otlp_metrics_endpoint: str | None = None

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("telemetry enabled must be a boolean")
        if (
            isinstance(self.timeout_seconds, bool)
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("telemetry timeout must be positive and finite")
        for endpoint in (self.otlp_endpoint, self.otlp_metrics_endpoint):
            if endpoint is not None:
                validate_endpoint(endpoint)

    @classmethod
    def from_environment(cls) -> TraceConfig:
        enabled = os.environ.get("HYPOMNESIS_TELEMETRY", "1")
        if enabled not in ("0", "1"):
            raise ValueError("HYPOMNESIS_TELEMETRY must be 0 or 1")
        return cls(
            enabled=enabled == "1",
            otlp_endpoint=os.environ.get("HYPOMNESIS_OTLP_TRACES_ENDPOINT"),
            timeout_seconds=float(os.environ.get("HYPOMNESIS_TELEMETRY_TIMEOUT", "3")),
            otlp_metrics_endpoint=os.environ.get("HYPOMNESIS_OTLP_METRICS_ENDPOINT"),
        )


def extract_context(carrier: Mapping[str, str]) -> Context:
    """Reject malformed remote parents instead of silently inventing a new trace."""
    context = _PROPAGATOR.extract(dict(carrier))
    if not otel.get_current_span(context).get_span_context().is_valid:
        raise ValueError("invalid W3C trace_context")
    return context


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
    def __init__(
        self,
        enabled: bool | None = None,
        *,
        config: TraceConfig | None = None,
        parent_context: Mapping[str, str] | None = None,
    ) -> None:
        if config is None:
            config = (
                TraceConfig.from_environment() if enabled is None else TraceConfig(enabled=enabled)
            )
        self._root = extract_context(parent_context) if parent_context is not None else Context()
        remote = otel.get_current_span(self._root).get_span_context()
        trace_id = remote.trace_id if remote.is_valid else RandomIdGenerator().generate_trace_id()
        self.trace_id = _hex_id(trace_id, 32)
        self.enabled = config.enabled
        self.config = config
        self._closed = False
        self._exporter = InMemorySpanExporter()
        provider: otel.TracerProvider
        self._provider: TracerProvider | None = None
        with ExitStack() as cleanup:
            self.metrics = Metrics(
                enabled=self.enabled,
                endpoint=config.otlp_metrics_endpoint,
                timeout_seconds=config.timeout_seconds,
            )
            cleanup.callback(self.metrics.close)
            if self.enabled:
                sdk_provider = TracerProvider(
                    id_generator=_FixedTraceId(trace_id),
                    resource=Resource({"service.name": "hypomnesis"}),
                )
                cleanup.callback(sdk_provider.shutdown)
                sdk_provider.add_span_processor(OperationMetrics(self.metrics))
                sdk_provider.add_span_processor(SimpleSpanProcessor(self._exporter))
                if config.otlp_endpoint is not None:
                    try:
                        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                            OTLPSpanExporter,
                        )
                    except ImportError as exc:
                        raise ValueError("OTLP export requires the 'telemetry' extra") from exc
                    sdk_provider.add_span_processor(
                        SimpleSpanProcessor(
                            OTLPSpanExporter(
                                endpoint=config.otlp_endpoint,
                                timeout=config.timeout_seconds,
                                session=local_session(),
                            )
                        )
                    )
                provider = sdk_provider
                self._provider = sdk_provider
            else:
                provider = NoOpTracerProvider()
            self._tracer = provider.get_tracer(_SCOPE)
            self._stack: ContextVar[tuple[tuple[str, Span], ...]] = ContextVar(
                "hypomnesis_spans", default=()
            )
            cleanup.pop_all()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            if self._provider is not None:
                self._provider.shutdown()
            self.metrics.close()

    def __enter__(self) -> Tracer:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        # The parent is explicit (own stack, never the ambient context), and a root
        # starts from an empty context, so a span of another tracer is never adopted.
        if self._closed:
            raise ValueError("tracer is closed")
        stack = self._stack.get()
        parent = otel.set_span_in_context(stack[-1][1]) if stack else self._root
        s = self._tracer.start_span(
            name,
            context=parent,
            attributes={k: _attribute(v) for k, v in attributes.items()},
            record_exception=False,
            set_status_on_exception=False,
        )
        token = self._stack.set((*stack, (name, s)))
        active = _ACTIVE.set(self)
        try:
            yield s
        except Exception as exc:
            s.record_exception(exc)
            s.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            _ACTIVE.reset(active)
            self._stack.reset(token)
            s.end()

    def current_context(self) -> SpanContext:
        """Context of the innermost open span (invalid when none is open)."""
        stack = self._stack.get()
        return stack[-1][1].get_span_context() if stack else otel.INVALID_SPAN_CONTEXT

    @property
    def current_operation(self) -> str | None:
        stack = self._stack.get()
        return stack[-1][0] if stack else None

    def link_message(self, span: Span, message: Mapping[str, Any]) -> None:
        carrier = message.get("trace_context")
        if carrier is not None:
            try:
                context = extract_context(carrier)
            except ValueError:
                logging.getLogger(__name__).warning("invalid incoming trace_context ignored")
            else:
                remote = otel.get_current_span(context).get_span_context()
                local = span.get_span_context()
                if (remote.trace_id, remote.span_id) != (local.trace_id, local.span_id):
                    span.add_link(remote)

    @property
    def spans(self) -> Sequence[ReadableSpan]:
        """Finished spans, in start order."""
        return sorted(self._exporter.get_finished_spans(), key=lambda s: s.start_time or 0)

    def tree(self) -> list[str]:
        children: dict[int | None, list[ReadableSpan]] = {}
        local_ids = {_span_id(s) for s in self.spans}
        for s in self.spans:
            parent = _parent_id(s)
            children.setdefault(parent if parent in local_ids else None, []).append(s)

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


def trace_context(tracer: Tracer | None = None) -> dict[str, str]:
    """W3C ``traceparent`` of the current span, as the message envelope expects (§9.6).

    Outside any span (or with telemetry disabled) the span id is all zeros and the
    sampled flag is off: the trace id is still the tracer's, so messages stay correlated.
    """
    tracer = tracer if tracer is not None else _ACTIVE.get()
    if tracer is None:
        return {}
    ctx = tracer.current_context()
    if ctx.is_valid:
        carrier: dict[str, str] = {}
        _PROPAGATOR.inject(carrier, context=otel.set_span_in_context(otel.NonRecordingSpan(ctx)))
        return carrier
    return {"traceparent": f"00-{tracer.trace_id}-{'0' * 16}-00"}


def current_tracer() -> Tracer | None:
    """The explicitly activated run tracer, isolated by thread and async task."""
    return _ACTIVE.get()


def operation(name: str, **attributes: Any) -> AbstractContextManager[Span | None]:
    tracer = current_tracer()
    return tracer.span(name, **attributes) if tracer is not None else nullcontext()


def traced_message(message: Mapping[str, Any]) -> dict[str, Any]:
    """Copy an outgoing envelope, never its payload, preserving recorded parents on replay."""
    data = dict(message)
    tracer = current_tracer()
    if "trace_context" not in data and tracer is not None and tracer.current_context().is_valid:
        data["trace_context"] = trace_context(tracer)
    return data
