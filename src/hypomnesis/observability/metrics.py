"""Private SDK metrics with a closed, bounded set of label values (§12.4)."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

from opentelemetry.metrics import Counter, Histogram
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    InMemoryMetricReader,
    MetricReader,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor
from opentelemetry.trace import StatusCode

from hypomnesis.observability.otlp import local_session, validate_endpoint

_PLUGIN_KINDS = {
    "observer.read": "sensor",
    "observer.verify": "sensor",
    "actuator.execute": "actuator",
    "estimator.predict": "estimator",
    "solver.solve": "solver",
    "validator.check": "validator",
    "llm.transcribe": "transcriber",
}
_LABELS = {
    "status": frozenset({"ok", "error", "accepted", "rejected"}),
    "kind": frozenset(_PLUGIN_KINDS.values()),
    "mode": frozenset({"dry-run", "simulate", "production"}),
    "state": frozenset(
        {"Completed", "Rejected", "Failed", "TimedOut", "UnknownOutcome", "DryRun", "Simulated"}
    ),
    "direction": frozenset({"input", "output"}),
}
_COUNTERS = {
    "hypomnesis_runs_total",
    "hypomnesis_plugin_calls_total",
    "hypomnesis_schema_validation_total",
    "hypomnesis_estimator_calls_total",
    "hypomnesis_validator_rejections_total",
    "hypomnesis_actuator_commands_total",
    "hypomnesis_actuator_failures_total",
    "hypomnesis_llm_tokens_total",
}
_HISTOGRAMS = {
    "hypomnesis_run_duration_seconds",
    "hypomnesis_plugin_duration_seconds",
    "hypomnesis_solver_duration_seconds",
}
_FAILURES = frozenset({"Failed", "TimedOut", "UnknownOutcome"})


def bounded_labels(labels: Mapping[str, str]) -> dict[str, str]:
    for key, value in labels.items():
        if key not in _LABELS or type(value) is not str or value not in _LABELS[key]:
            raise ValueError(f"unbounded metric label: {key}")
    return dict(labels)


class Metrics:
    def __init__(
        self, *, enabled: bool = True, endpoint: str | None = None, timeout_seconds: float = 3.0
    ) -> None:
        if type(enabled) is not bool:
            raise ValueError("telemetry enabled must be a boolean")
        if (
            isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("telemetry timeout must be positive and finite")
        if endpoint is not None:
            validate_endpoint(endpoint)
        self.enabled = enabled
        self._closed = False
        self._snapshot: dict[str, Any] = {"resource_metrics": []}
        self._reader = InMemoryMetricReader()
        readers: list[MetricReader] = [self._reader]
        if enabled and endpoint is not None:
            try:
                from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                    OTLPMetricExporter,
                )
            except ImportError as exc:
                raise ValueError("OTLP export requires the 'telemetry' extra") from exc
            readers.append(
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(
                        endpoint=endpoint, timeout=timeout_seconds, session=local_session()
                    ),
                    export_interval_millis=5000,
                    export_timeout_millis=timeout_seconds * 1000,
                )
            )
        self._provider = MeterProvider(
            metric_readers=readers,
            resource=Resource({"service.name": "hypomnesis"}),
            shutdown_on_exit=False,
            views=[
                View(
                    instrument_name="hypomnesis_*duration_seconds",
                    aggregation=ExplicitBucketHistogramAggregation(
                        boundaries=(
                            0.001,
                            0.005,
                            0.01,
                            0.025,
                            0.05,
                            0.1,
                            0.25,
                            0.5,
                            1,
                            2.5,
                            5,
                            10,
                            30,
                            60,
                        )
                    ),
                )
            ],
        )
        meter = self._provider.get_meter("hypomnesis")
        self._counters: dict[str, Counter] = {
            name: meter.create_counter(name) for name in sorted(_COUNTERS)
        }
        self._histograms: dict[str, Histogram] = {
            name: meter.create_histogram(name, unit="s") for name in sorted(_HISTOGRAMS)
        }

    def record(self, name: str, value: int | float = 1, **labels: str) -> None:
        attributes = bounded_labels(labels)
        if name not in _COUNTERS | _HISTOGRAMS:
            raise ValueError(f"unknown metric: {name}")
        if isinstance(value, bool) or not math.isfinite(value) or value < 0:
            raise ValueError("metric values must be nonnegative and finite")
        if name in _COUNTERS and type(value) is not int:
            raise ValueError("counter values must be integers")
        if self._closed:
            raise ValueError("metrics provider is closed")
        if self.enabled:
            if name in _COUNTERS:
                self._counters[name].add(value, attributes)
            else:
                self._histograms[name].record(value, attributes)

    def command(self, state: str, mode: str) -> None:
        self.record("hypomnesis_actuator_commands_total", state=state, mode=mode)
        if state in _FAILURES:
            self.record("hypomnesis_actuator_failures_total", state=state, mode=mode)

    def snapshot(self) -> dict[str, Any]:
        if not self._closed:
            data = self._reader.get_metrics_data()
            self._snapshot = (
                json.loads(data.to_json()) if data is not None else {"resource_metrics": []}
            )
        return self._snapshot

    def close(self) -> None:
        if not self._closed:
            self.snapshot()
            self._closed = True
            self._provider.shutdown()


class OperationMetrics(SpanProcessor):
    def __init__(self, metrics: Metrics) -> None:
        self.metrics = metrics

    def on_end(self, span: ReadableSpan) -> None:
        status = "error" if span.status.status_code is StatusCode.ERROR else "ok"
        duration = max(0, (span.end_time or 0) - (span.start_time or 0)) / 1e9
        attrs = span.attributes or {}
        if span.name == "hypomnesis.run":
            self.metrics.record("hypomnesis_runs_total", status=status)
            self.metrics.record("hypomnesis_run_duration_seconds", duration, status=status)
        kind = _PLUGIN_KINDS.get(span.name)
        if kind is not None:
            self.metrics.record("hypomnesis_plugin_calls_total", kind=kind, status=status)
            self.metrics.record(
                "hypomnesis_plugin_duration_seconds", duration, kind=kind, status=status
            )
        if span.name == "schema.validate":
            result = attrs.get("validation.result")
            self.metrics.record(
                "hypomnesis_schema_validation_total",
                status=result if result in ("accepted", "rejected") else "error",
            )
        if span.name == "solver.solve":
            self.metrics.record("hypomnesis_solver_duration_seconds", duration, status=status)
        if span.name == "estimator.predict":
            self.metrics.record("hypomnesis_estimator_calls_total", status=status)
        if span.name == "validator.check" and attrs.get("validation.result") == "rejected":
            self.metrics.record("hypomnesis_validator_rejections_total")
