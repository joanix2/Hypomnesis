"""Verify real MVP traces and increasing metrics through Grafana's provisioned sources."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, TypeVar
from urllib.parse import urlencode, urlsplit

from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import HTTPError, Timeout

from hypomnesis.observability.metrics import bounded_labels
from hypomnesis.observability.otlp import local_session, validate_endpoint

ROOT = Path(__file__).resolve().parents[1]
PROMETHEUS = "/api/datasources/proxy/uid/hypomnesis-prometheus"
TEMPO = "/api/datasources/proxy/uid/hypomnesis-tempo"
T = TypeVar("T")
Sample = tuple[str, tuple[tuple[str, str], ...]]


def local_base(url: str) -> str:
    validate_endpoint(url)
    if urlsplit(url).path not in ("", "/"):
        raise ValueError("the local service URL must not contain a path")
    return url.rstrip("/")


def request(url: str, deadline: float) -> bytes:
    timeout = min(3.0, deadline - time.monotonic())
    if timeout <= 0:
        raise TimeoutError("verification deadline reached")
    with (
        local_session() as session,
        session.get(url, headers={"Accept": "application/json"}, timeout=timeout) as response,
    ):
        response.raise_for_status()
        return response.content


def wait_for(label: str, fetch: Callable[[], T], accept: Callable[[T], bool], deadline: float) -> T:
    detail = "condition not yet satisfied"
    while time.monotonic() < deadline:
        try:
            value = fetch()
        except HTTPError as exc:
            if exc.response is None:
                raise ValueError(f"{label}: HTTP error without response") from None
            code = exc.response.status_code
            if code not in {404, 408, 429, 500, 502, 503, 504}:
                raise RuntimeError(f"{label}: HTTP {code}") from None
            detail = f"HTTP {code}"
        except (RequestConnectionError, Timeout, TimeoutError) as exc:
            detail = type(exc).__name__
        else:
            if accept(value):
                return value
            detail = "condition not yet satisfied"
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.5, remaining))
    raise TimeoutError(f"{label}: {detail}")


def vector(document: Mapping[str, Any]) -> list[tuple[dict[str, str], float]]:
    if document.get("status") != "success":
        raise ValueError("Prometheus did not return a successful query")
    data = document.get("data")
    if not isinstance(data, dict) or data.get("resultType") != "vector":
        raise ValueError("Prometheus query must return a vector")
    result = data.get("result")
    if not isinstance(result, list):
        raise ValueError("Prometheus query must return a vector")
    parsed = []
    for sample in result:
        if not isinstance(sample, dict):
            raise ValueError("Prometheus sample must be an object")
        labels, pair = sample.get("metric"), sample.get("value")
        if not isinstance(labels, dict) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in labels.items()
        ):
            raise ValueError("Prometheus sample labels must be strings")
        if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[1], str):
            raise ValueError("Prometheus sample must contain a timestamp and value")
        value = float(pair[1])
        if not math.isfinite(value) or value < 0:
            raise ValueError("metric values must be finite and nonnegative")
        parsed.append((labels, value))
    return parsed


def metric_value(document: Mapping[str, Any]) -> float:
    result = vector(document)
    if len(result) > 1:
        raise ValueError("the sum query must return exactly one sample")
    return result[0][1] if result else 0.0


def sample_key(name: str, labels: Mapping[str, str]) -> Sample:
    attributes = dict(labels)
    bound = attributes.pop("le", None)
    bounded_labels(attributes)
    if bound is not None:
        if not name.endswith("_bucket"):
            raise ValueError("only histogram buckets can have an upper bound")
        number = float(bound)
        if math.isnan(number) or number < 0:
            raise ValueError("invalid histogram bound")
        attributes["le"] = str(number)
    return name, tuple(sorted(attributes.items()))


def expected_samples(snapshot: Mapping[str, Any]) -> tuple[str, dict[Sample, float]]:
    resources = snapshot["resource_metrics"]
    if len(resources) != 1:
        raise ValueError("the MVP must have exactly one metric producer")
    resource = resources[0]
    identity = resource["resource"]["attributes"]["service.instance.id"]
    if str(uuid.UUID(identity)) != identity:
        raise ValueError("invalid metric producer identity")
    expected: dict[Sample, float] = {}
    for scope in resource["scope_metrics"]:
        for metric in scope["metrics"]:
            name, data = metric["name"], metric["data"]
            if data["aggregation_temporality"] != 2:
                raise ValueError("the memory reader must be cumulative")
            for point in data["data_points"]:
                labels = bounded_labels(point["attributes"])
                if "value" in point:
                    expected[sample_key(name, labels)] = point["value"]
                else:
                    expected[sample_key(name + "_count", labels)] = point["count"]
                    expected[sample_key(name + "_sum", labels)] = point["sum"]
                    counts, bounds = point["bucket_counts"], point["explicit_bounds"]
                    if len(counts) != len(bounds) + 1 or sum(counts) != point["count"]:
                        raise ValueError("inconsistent SDK histogram")
                    cumulative = 0
                    for count, bound in zip(counts, [*bounds, math.inf], strict=True):
                        cumulative += count
                        expected[sample_key(name + "_bucket", {**labels, "le": str(bound)})] = (
                            cumulative
                        )
    if expected.get(sample_key("hypomnesis_runs_total", {"status": "ok"})) != 1:
        raise ValueError("the MVP must report exactly one successful run")
    return identity, expected


def metrics_complete(
    document: Mapping[str, Any], identity: str, expected: Mapping[Sample, float]
) -> bool:
    actual = {}
    for attributes, value in vector(document):
        labels = dict(attributes)
        if labels.pop("instance", None) != identity or labels.pop("job", None) != "hypomnesis":
            raise ValueError("Prometheus returned a different metric producer")
        name = labels.pop("__name__", None)
        if not isinstance(name, str):
            raise ValueError("Prometheus sample is missing its metric name")
        for key in ("otel_scope_name", "otel_scope_version", "otel_scope_schema_url"):
            labels.pop(key, None)
        key = sample_key(name, labels)
        if key in actual:
            raise ValueError("duplicate Prometheus sample")
        actual[key] = value
    return expected.keys() <= actual.keys() and all(
        math.isclose(actual[key], value, rel_tol=1e-8, abs_tol=1e-10)
        for key, value in expected.items()
    )


def otel_id(value: str, size: int) -> str:
    if not isinstance(value, str):
        raise ValueError("trace/span identifiers must be strings")
    if re.fullmatch(rf"[0-9a-fA-F]{{{size * 2}}}", value):
        return value.lower()
    try:
        decoded = base64.b64decode(value, validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid trace/span identifier encoding") from exc
    if len(decoded) != size:
        raise ValueError("invalid trace/span identifier length")
    return decoded.hex()


def spans(document: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "spans":
                if not isinstance(value, list) or any(not isinstance(s, dict) for s in value):
                    raise ValueError("Tempo must return a list of span objects")
                yield from value
            else:
                yield from spans(value)
    elif isinstance(document, list):
        for value in document:
            yield from spans(value)


def trace_complete(document: Any, trace_id: str, expected_ids: set[str]) -> bool:
    actual = list(spans(document))
    actual_ids = set()
    for span in actual:
        trace = span.get("traceId", span.get("traceID", span.get("trace_id")))
        identity = span.get("spanId", span.get("spanID", span.get("span_id")))
        if otel_id(trace, 16) != trace_id:
            raise ValueError("Tempo returned a different trace")
        actual_ids.add(otel_id(identity, 8))
    return bool(actual) and expected_ids <= actual_ids


def verify(
    *, grafana: str, otlp: str, collector_health: str, output: Path, timeout: float
) -> dict[str, Any]:
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("verification timeout must be positive and finite")
    grafana, otlp, collector_health = (local_base(url) for url in (grafana, otlp, collector_health))
    started = time.time()
    deadline = time.monotonic() + timeout
    wait_for(
        "Grafana database",
        lambda: json.loads(request(grafana + "/api/health", deadline)),
        lambda data: data.get("database") == "ok",
        deadline,
    )
    wait_for("Collector health", lambda: request(collector_health + "/", deadline), bool, deadline)
    wait_for(
        "Tempo via Grafana",
        lambda: request(grafana + TEMPO + "/ready", deadline),
        lambda data: data.strip() == b"ready",
        deadline,
    )

    def query_document(expression: str) -> Any:
        path = "/api/v1/query?" + urlencode({"query": expression})
        return json.loads(request(grafana + PROMETHEUS + path, deadline))

    def query(expression: str) -> float:
        return metric_value(query_document(expression))

    def run_count() -> float:
        return query("sum(hypomnesis_runs_total)")

    wait_for(
        "fresh Collector scrape via Grafana",
        lambda: query('max(timestamp(up{job="hypomnesis"}))'),
        lambda timestamp: timestamp >= started,
        deadline,
    )
    before = wait_for("Prometheus via Grafana", run_count, lambda value: value >= 0, deadline)
    output.mkdir(parents=True, exist_ok=True)

    def launch(number: int) -> tuple[dict[str, Any], float, float]:
        directory = output / f"run-{number}"
        began = time.monotonic()
        subprocess.run(
            [sys.executable, "-m", "examples.mechanics.mvp", "--output", str(directory.resolve())],
            cwd=ROOT,
            env={
                **os.environ,
                "HYPOMNESIS_TELEMETRY": "1",
                "HYPOMNESIS_OTLP_TRACES_ENDPOINT": otlp + "/v1/traces",
                "HYPOMNESIS_OTLP_METRICS_ENDPOINT": otlp + "/v1/metrics",
            },
            stdout=subprocess.PIPE,
            check=True,
            timeout=max(0.001, deadline - time.monotonic()),
        )
        report = json.loads((directory / "rapport_mvp.json").read_text())
        if report["status"] != "completed":
            raise ValueError("MVP did not complete successfully")
        return report, began, time.monotonic()

    traces = []
    producers: set[str] = set()
    for numbers in ((1,), (2,), (3, 4)):
        if len(numbers) == 1:
            results = [launch(numbers[0])]
        else:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(launch, numbers))
            if max(result[1] for result in results) >= min(result[2] for result in results):
                raise ValueError("the concurrent MVP processes did not overlap")
        for number, (report, _, _) in zip(numbers, results, strict=True):
            trace = report["trace"]
            expected_ids = {span["span_id"] for span in trace["spans"]}
            wait_for(
                f"complete trace {number} via Grafana",
                lambda trace=trace: json.loads(
                    request(grafana + TEMPO + "/api/traces/" + trace["trace_id"], deadline)
                ),
                lambda document, trace=trace, expected_ids=expected_ids: trace_complete(
                    document, trace["trace_id"], expected_ids
                ),
                deadline,
            )
            identity, expected = expected_samples(report["sdk_metrics"])
            if identity in producers:
                raise ValueError("independent MVP processes share a metric producer identity")
            producers.add(identity)
            wait_for(
                f"exact SDK counters and histogram buckets for MVP {number}",
                lambda identity=identity: query_document(
                    '{__name__=~"hypomnesis_.+",job="hypomnesis",instance="' + identity + '"}'
                ),
                lambda document, identity=identity, expected=expected: metrics_complete(
                    document, identity, expected
                ),
                deadline,
            )
            traces.append(
                {
                    "trace_id": trace["trace_id"],
                    "spans": len(expected_ids),
                    "metric_producer": identity,
                    "metric_samples_verified": len(expected),
                    "concurrent": len(numbers) > 1,
                }
            )
    after = run_count()
    evidence = {
        "status": "ok",
        "grafana": grafana,
        "runs_before": before,
        "runs_after": after,
        "verified_runs": len(traces),
        "traces": traces,
        "model_mode": "recorded-fixture",
    }
    (output / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grafana", default="http://127.0.0.1:3000")
    parser.add_argument("--otlp", default="http://127.0.0.1:4318")
    parser.add_argument("--collector-health", default="http://127.0.0.1:13133")
    parser.add_argument("--output", type=Path, default=ROOT / "demo/sortie/monitoring-verification")
    parser.add_argument("--timeout", type=float, default=90)
    arguments = parser.parse_args()
    print(json.dumps(verify(**vars(arguments)), indent=2))


if __name__ == "__main__":
    main()
