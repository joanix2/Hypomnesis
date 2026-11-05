"""Local deployment invariants and exact Grafana verification, without Docker."""

import base64
import copy
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from monitoring import verify as monitoring
from requests import Response
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import HTTPError

from hypomnesis.observability.metrics import Metrics

ROOT = Path(__file__).resolve().parents[2]


def document(samples):
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": labels, "value": [1, str(value)]} for labels, value in samples],
        },
    }


@pytest.fixture
def snapshot():
    metrics = Metrics()
    try:
        metrics.record("hypomnesis_runs_total", status="ok")
        for duration in (0.001, 1.1):
            metrics.record("hypomnesis_run_duration_seconds", duration, status="ok")
        yield metrics.snapshot()
    finally:
        metrics.close()


def prometheus_document(identity, expected):
    return document(
        [
            (
                {
                    "__name__": name,
                    "job": "hypomnesis",
                    "instance": identity,
                    "otel_scope_name": "hypomnesis",
                    **dict(labels),
                },
                value,
            )
            for (name, labels), value in expected.items()
        ]
    )


def test_sdk_histograms_are_checked_bucket_by_bucket_including_empty_buckets(snapshot):
    identity, expected = monitoring.expected_samples(snapshot)
    metric = "hypomnesis_run_duration_seconds"
    assert expected[monitoring.sample_key(metric + "_count", {"status": "ok"})] == 2
    assert expected[monitoring.sample_key(metric + "_sum", {"status": "ok"})] == pytest.approx(
        1.101
    )
    buckets = {
        dict(labels)["le"]: value
        for (name, labels), value in expected.items()
        if name.endswith("_bucket")
    }
    assert buckets["0.001"] == 1
    assert buckets["1.0"] == 1
    assert buckets["2.5"] == buckets["inf"] == 2
    exported = prometheus_document(identity, expected)
    assert monitoring.metrics_complete(exported, identity, expected)
    missing = copy.deepcopy(exported)
    missing["data"]["result"].pop()
    assert not monitoring.metrics_complete(missing, identity, expected)
    doubled = copy.deepcopy(exported)
    doubled["data"]["result"][0]["value"][1] = "2"
    assert not monitoring.metrics_complete(doubled, identity, expected)
    assert not monitoring.metrics_complete(document([]), identity, expected)
    with pytest.raises(ValueError, match="different metric producer"):
        monitoring.metrics_complete(exported, "another-producer", expected)
    duplicate = copy.deepcopy(exported)
    duplicate["data"]["result"].append(duplicate["data"]["result"][0])
    with pytest.raises(ValueError, match="duplicate"):
        monitoring.metrics_complete(duplicate, identity, expected)


def test_bucket_bounds_are_normalized_without_changing_their_values():
    assert monitoring.sample_key("a_bucket", {"le": "1"}) == monitoring.sample_key(
        "a_bucket", {"le": "1.0"}
    )
    assert monitoring.sample_key("a_bucket", {"le": "+Inf"}) == monitoring.sample_key(
        "a_bucket", {"le": "inf"}
    )
    for bound in ("NaN", "-1", "-Inf"):
        with pytest.raises(ValueError, match="invalid histogram bound"):
            monitoring.sample_key("a_bucket", {"le": bound})
    with pytest.raises(ValueError, match="only histogram"):
        monitoring.sample_key("a_total", {"le": "1"})
    with pytest.raises(ValueError, match="unbounded"):
        monitoring.sample_key("a_total", {"run_id": "unbounded"})


def test_inconsistent_sdk_histograms_are_explicit_errors(snapshot):
    for resource in snapshot["resource_metrics"]:
        for scope in resource["scope_metrics"]:
            for metric in scope["metrics"]:
                if metric["name"] == "hypomnesis_run_duration_seconds":
                    metric["data"]["data_points"][0]["count"] += 1
    with pytest.raises(ValueError, match="inconsistent SDK histogram"):
        monitoring.expected_samples(snapshot)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "error"},
        {"status": "success", "data": {"resultType": "scalar", "result": [1, "1"]}},
        {"status": "success", "data": {"resultType": "vector", "result": {}}},
        {"status": "success", "data": {"resultType": "vector", "result": [None]}},
        document([({}, math.nan)]),
        document([({}, math.inf)]),
        document([({}, -1)]),
        document([({}, 1), ({}, 2)]),
    ],
)
def test_invalid_prometheus_outputs_are_not_successes(payload):
    with pytest.raises(ValueError):
        monitoring.metric_value(payload)


def test_sum_queries_can_have_no_series_but_not_multiple_series():
    assert monitoring.metric_value(document([])) == 0
    assert monitoring.metric_value(document([({}, 4)])) == 4


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://example.com",
        "http://localhost:3000/not-a-root",
        "http://name:password@localhost:3000",
        "http://localhost:3000?token=x",
    ],
)
def test_service_urls_must_be_explicit_local_roots(url):
    with pytest.raises(ValueError):
        monitoring.local_base(url)


def test_local_service_urls():
    assert monitoring.local_base("http://127.0.0.1:3000/") == "http://127.0.0.1:3000"
    assert monitoring.local_base("http://[::1]:3000") == "http://[::1]:3000"


def test_retry_budget_and_transient_errors(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(monitoring.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        monitoring.time, "sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )
    failures = [RequestConnectionError(), HTTPError(response=Response()), 4]
    failures[1].response.status_code = 503

    def fetch():
        value = failures.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    assert monitoring.wait_for("service", fetch, lambda value: value == 4, 2) == 4
    assert clock[0] == 1
    with pytest.raises(TimeoutError, match="condition not yet satisfied"):
        monitoring.wait_for("service", lambda: 0, bool, 1.5)
    assert clock[0] == 1.5


def test_nontransient_http_errors_are_not_retried_or_disclosed():
    response = Response()
    response.status_code = 401
    response._content = b"fixture confidential body"

    def fetch():
        raise HTTPError("fixture confidential diagnostic", response=response)

    with pytest.raises(RuntimeError, match=r"^service: HTTP 401$"):
        monitoring.wait_for("service", fetch, bool, time.monotonic() + 1)


def test_real_local_http_ignores_environment_proxy_and_refuses_redirects(monkeypatch):
    paths = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            self.send_response(302 if self.path == "/redirect" else 200)
            if self.path == "/redirect":
                self.send_header("Location", "/secret")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert monitoring.request(base + "/ready", time.monotonic() + 3) == b""
        with pytest.raises(HTTPError):
            monitoring.request(base + "/redirect", time.monotonic() + 3)
        with pytest.raises(TimeoutError, match="deadline"):
            monitoring.request(base, time.monotonic() - 1)
        assert paths == ["/ready", "/redirect"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_trace_ids_support_both_otlp_json_encodings_and_require_all_spans():
    trace, one, two = "12" * 16, "34" * 8, "56" * 8
    payload = {
        "batches": [
            {
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": base64.b64encode(bytes.fromhex(trace)).decode(),
                                "spanId": one,
                            }
                        ]
                    }
                ]
            }
        ]
    }
    assert monitoring.trace_complete(payload, trace, {one})
    assert not monitoring.trace_complete(payload, trace, {one, two})
    assert not monitoring.trace_complete({}, trace, {one})
    with pytest.raises(ValueError, match="different trace"):
        monitoring.trace_complete(payload, "78" * 16, {one})
    for invalid in ("?", "AA==", 42):
        with pytest.raises(ValueError):
            monitoring.otel_id(invalid, 16)
    with pytest.raises(ValueError, match="list of span objects"):
        list(monitoring.spans({"spans": [None]}))


def test_compose_is_local_bounded_pinned_and_provisions_matching_sources():
    directory = ROOT / "monitoring"
    compose = yaml.safe_load((directory / "docker-compose.yml").read_text())
    assert compose["name"] == "hypomnesis-monitoring"
    services = compose["services"]
    assert set(services) == {"collector", "prometheus", "tempo", "grafana"}
    for service in services.values():
        tag, digest = service["image"].split("@sha256:")
        assert ":" in tag and len(bytes.fromhex(digest)) == 32
        assert all(port.startswith("127.0.0.1:") for port in service["ports"])
        assert 0 < service["cpus"] <= 1
        assert service["mem_limit"] in {"256m", "512m"}
        assert service["cap_drop"] == ["ALL"]
        assert service["security_opt"] == ["no-new-privileges:true"]
    grafana = services["grafana"]["environment"]
    for key in ("GF_ANALYTICS_REPORTING_ENABLED", "GF_ANALYTICS_CHECK_FOR_UPDATES"):
        assert grafana[key] == "false"
    assert grafana["GF_PLUGINS_PREINSTALL_DISABLED"] == "true"
    sources = yaml.safe_load(
        (directory / "grafana/provisioning/datasources/sources.yml").read_text()
    )["datasources"]
    assert {(source["uid"], source["url"]) for source in sources} == {
        ("hypomnesis-prometheus", "http://prometheus:9090"),
        ("hypomnesis-tempo", "http://tempo:3200"),
    }
    assert all(not source["editable"] and source["access"] == "proxy" for source in sources)
    prometheus = yaml.safe_load((directory / "prometheus.yml").read_text())
    scrape = prometheus["scrape_configs"][0]
    assert scrape["honor_labels"] is True
    assert scrape["static_configs"] == [{"targets": ["collector:8889"]}]
    collector = yaml.safe_load((directory / "collector.yml").read_text())
    pipeline = collector["service"]["pipelines"]
    assert pipeline["metrics"]["processors"] == ["memory_limiter", "batch"]
    assert pipeline["metrics"]["exporters"] == ["prometheus"]
    assert pipeline["traces"]["exporters"] == ["otlp_grpc/tempo"]
