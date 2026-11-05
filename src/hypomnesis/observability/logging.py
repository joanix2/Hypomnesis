"""Structured, correlated logs without raw prompts, payloads or exceptions."""

from __future__ import annotations

import json
import logging
import math
import re
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TextIO

REDACTED = "[REDACTED]"
_SENSITIVE = frozenset(
    {
        "prompt",
        "prompts",
        "messages",
        "message",
        "payload",
        "data",
        "input",
        "output",
        "content",
        "text",
        "sensor",
        "sensorvalue",
        "raw",
        "body",
        "request",
        "response",
        "error",
        "detail",
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "authorization",
        "cookie",
        "email",
        "phone",
        "address",
        "name",
        "firstname",
        "lastname",
        "fullname",
        "person",
        "personal",
        "pii",
        "ssn",
        "dateofbirth",
        "exceptionmessage",
        "exceptionstacktrace",
        "exception",
        "excinfo",
        "traceback",
        "stacktrace",
    }
)
_METADATA = frozenset(
    {
        "attributes",
        "run_id",
        "trace_id",
        "span_id",
        "plugin",
        "plugin.version",
        "domain",
        "language",
        "langage",
        "version",
        "schema_id",
        "schema_version",
        "operation",
        "status",
        "mode",
        "kind",
        "command_id",
        "command.state",
        "validation.result",
        "checker",
        "boundary",
        "count",
        "contraintes",
        "source_unit",
        "target_unit",
        "model",
        "scenario",
        "solver",
        "actionneur",
        "capteur",
        "duration_ms",
        "reason_code",
        "http_status",
        "signal",
        "exception.type",
        "exception.message",
        "exception.stacktrace",
    }
)
_EVENT = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")
_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")
_OPERATION = re.compile(r"[a-z][a-z0-9_.-]{0,99}")
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:/@+-]{1,256}")
_VALUES = {
    "status": frozenset(
        {
            "ok",
            "error",
            "accepted",
            "rejected",
            "Created",
            "Validated",
            "Authorized",
            "Dispatched",
            "Accepted",
            "Completed",
            "Rejected",
            "Failed",
            "TimedOut",
            "UnknownOutcome",
            "DryRun",
            "Simulated",
        }
    ),
    "mode": frozenset({"dry-run", "simulate", "production"}),
    "validation.result": frozenset({"accepted", "rejected", "error"}),
    "signal": frozenset({"traces", "metrics", "logs", "telemetry"}),
}
_CORRELATION: ContextVar[Mapping[str, str] | None] = ContextVar(
    "hypomnesis_log_correlation", default=None
)


@dataclass
class _ExportContext:
    signal: str
    run_id: str | None
    trace_id: str | None
    http_status: int | None = None


_SDK_EXPORT: ContextVar[_ExportContext | None] = ContextVar("hypomnesis_sdk_export", default=None)


def _normalized(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.casefold())


@dataclass(frozen=True)
class RedactionPolicy:
    additional_sensitive_keys: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if any(
            not isinstance(key, str) or not _normalized(key)
            for key in self.additional_sensitive_keys
        ):
            raise ValueError("sensitive field names must be nonempty strings")

    def sensitive(self, key: str) -> bool:
        normalized = _normalized(key)
        return normalized in _SENSITIVE or normalized in {
            _normalized(k) for k in self.additional_sensitive_keys
        }

    def span_attributes(self, value: Any, *, _depth: int = 0) -> Any:
        """Preserve trace attribute shapes, but never render arbitrary objects."""
        if _depth >= 8:
            return REDACTED
        if isinstance(value, Mapping):
            return {
                key if isinstance(key, str) else REDACTED: REDACTED
                if not isinstance(key, str) or self.sensitive(key)
                else self.span_attributes(item, _depth=_depth + 1)
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(self.span_attributes(item, _depth=_depth + 1) for item in value)
        if isinstance(value, list):
            return [self.span_attributes(item, _depth=_depth + 1) for item in value]
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        return REDACTED

    def log_fields(self, fields: Mapping[str, Any], *, _depth: int = 0) -> dict[str, Any]:
        if _depth >= 8:
            return {"redacted": True}
        result: dict[str, Any] = {}
        for key, value in fields.items():
            if not isinstance(key, str) or not _KEY.fullmatch(key):
                result["redacted"] = True
            elif self.sensitive(key):
                result[key] = REDACTED
            elif key not in _METADATA:
                result["redacted"] = True
            elif isinstance(value, Mapping):
                result[key] = self.log_fields(value, _depth=_depth + 1)
            elif value is None or (
                key in {"count", "contraintes", "duration_ms", "http_status"}
                and type(value) in (int, float)
                and math.isfinite(value)
                and value >= 0
            ):
                result[key] = value
            elif isinstance(value, str) and _IDENTIFIER.fullmatch(value):
                result[key] = (
                    value
                    if (
                        (key != "operation" or _OPERATION.fullmatch(value))
                        and (key not in _VALUES or value in _VALUES[key])
                    )
                    else REDACTED
                )
            else:
                result[key] = REDACTED
        return result


@dataclass(frozen=True)
class _Event:
    document: Mapping[str, Any]

    def __str__(self) -> str:
        return json.dumps(dict(self.document), ensure_ascii=True, allow_nan=False)


def _document(event: str, level: int, fields: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": logging.getLevelName(level),
        "event": event,
        **fields,
    }


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, _Event):
            return str(record.msg)
        fields: dict[str, Any] = {"message": REDACTED}
        if record.exc_info is not None and record.exc_info[0] is not None:
            fields["exception.type"] = record.exc_info[0].__name__
        return str(
            _Event(_document("external.log", record.levelno, RedactionPolicy().log_fields(fields)))
        )


class JsonLogger:
    def __init__(
        self,
        *,
        enabled: bool = True,
        stream: TextIO | None = None,
        policy: RedactionPolicy | None = None,
    ) -> None:
        if type(enabled) is not bool:
            raise ValueError("structured logs enabled must be a boolean")
        self.policy = policy if policy is not None else RedactionPolicy()
        self._closed = False
        self._logger = logging.Logger("hypomnesis.telemetry", level=logging.INFO)
        self._logger.propagate = False
        self._logger.disabled = not enabled
        self._handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
        self._handler.setFormatter(JsonFormatter())
        self._logger.addHandler(self._handler)

    def emit(self, event: str, *, level: int = logging.INFO, **fields: Any) -> None:
        if self._closed:
            raise ValueError("logger is closed")
        if not isinstance(event, str) or not _EVENT.fullmatch(event):
            raise ValueError("log event must be a dotted identifier")
        if level not in (
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ):
            raise ValueError("unsupported log level")
        safe = self.policy.log_fields({**fields, **(_CORRELATION.get() or {})})
        self._logger.log(level, _Event(_document(event, level, safe)))

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._logger.disabled = True
            self._logger.removeHandler(self._handler)
            self._handler.close()


@contextmanager
def correlation(run_id: str, trace_id: str, span_id: str) -> Iterator[None]:
    token = _CORRELATION.set({"run_id": run_id, "trace_id": trace_id, "span_id": span_id})
    try:
        yield
    finally:
        _CORRELATION.reset(token)


class _SDKFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = _SDK_EXPORT.get()
        if context is None or isinstance(record.msg, _Event):
            return True
        fields: dict[str, Any] = {
            "signal": context.signal,
            "run_id": context.run_id,
            "trace_id": context.trace_id,
        }
        fields.update(_CORRELATION.get() or {})
        if isinstance(record.args, tuple):
            codes = [arg for arg in record.args if type(arg) is int and 100 <= arg <= 599]
            if codes:
                fields["http_status"] = codes[0]
        if context.http_status is not None:
            fields["http_status"] = context.http_status
        if record.exc_info is not None and record.exc_info[0] is not None:
            fields["exception.type"] = record.exc_info[0].__name__
        record.msg = _Event(
            _document(
                "telemetry.export.failed", record.levelno, RedactionPolicy().log_fields(fields)
            )
        )
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


_SDK_FILTER = _SDKFilter()
_SDK_LOGGERS = (
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "opentelemetry.exporter.otlp.proto.http.metric_exporter",
    "opentelemetry.exporter.otlp.proto.http._transport",
    "opentelemetry.exporter.otlp.common.http",
    "opentelemetry.exporter.otlp.proto.common._internal",
    "opentelemetry.sdk._shared_internal",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk.metrics._internal.export",
)


@contextmanager
def export_diagnostics(signal: str, run_id: str | None, trace_id: str | None) -> Iterator[None]:
    """Redact only this host's SDK exports, never reconfigure application handlers."""
    for name in _SDK_LOGGERS:
        logger = logging.getLogger(name)
        if _SDK_FILTER not in logger.filters:
            logger.addFilter(_SDK_FILTER)
    token = _SDK_EXPORT.set(_ExportContext(signal, run_id, trace_id))
    try:
        yield
    finally:
        _SDK_EXPORT.reset(token)


def export_response(status: int) -> None:
    context = _SDK_EXPORT.get()
    if context is not None:
        context.http_status = status
