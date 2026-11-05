"""SDK aggregation, closed dimensions and real local OTLP metric delivery."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator, Dispatcher
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.engine.validators import LanguageValidator
from hypomnesis.observability.metrics import Metrics, bounded_labels
from hypomnesis.observability.trace import TraceConfig, Tracer
from hypomnesis.session import Session

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/mecanique"
PROGRAM = ROOT / "demo/programs/mecanique/plaque_120x80.hyp"
SCHEMA = "https://schemas.example.org/hypomnesis/metrics-test/1.0.0"


def points(tracer):
    return {
        metric["name"]: metric["data"]["data_points"]
        for resource in tracer.metrics.snapshot()["resource_metrics"]
        for scope in resource["scope_metrics"]
        for metric in scope["metrics"]
    }


@pytest.fixture
def metrics_collector():
    received = []
    responses = [200]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            received.append((self.path, ExportMetricsServiceRequest.FromString(body)))
            self.send_response(responses[0])
            if responses[0] == 302:
                self.send_header("Location", "/redirected")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/metrics", received, responses
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize(
    "labels",
    [
        {"message_id": "m-1"},
        {"trace_id": "0123456789abcdef"},
        {"traceId": "0123456789abcdef"},
        {"knowledge_id": "fact-1"},
        {"correlation_id": "run-1"},
        {"plugin": "unbounded-plugin"},
        {"schema_id": SCHEMA},
        {"status": "trace-0123456789abcdef"},
        {"kind": "my-plugin"},
        {"mode": "run-1"},
        {"direction": "message-1"},
    ],
)
def test_identifiers_are_rejected_even_under_a_permitted_label_name(labels):
    with pytest.raises(ValueError, match="unbounded metric label"):
        bounded_labels(labels)


def test_real_symbolic_pipeline_emits_sdk_metrics_without_inventing_failures_or_tokens(tmp_path):
    report = run_procedure(load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path)
    data = points(report.tracer)
    assert data["hypomnesis_runs_total"][0]["value"] == 1
    assert data["hypomnesis_run_duration_seconds"][0]["count"] == 1
    assert data["hypomnesis_run_duration_seconds"][0]["sum"] > 0
    assert data["hypomnesis_solver_duration_seconds"][0]["count"] == 1
    assert sum(p["value"] for p in data["hypomnesis_estimator_calls_total"]) >= 1
    assert sum(p["value"] for p in data["hypomnesis_schema_validation_total"]) >= 1
    assert sum(p["value"] for p in data["hypomnesis_actuator_commands_total"]) == len(
        report.commands
    )
    assert "hypomnesis_actuator_failures_total" not in data
    assert "hypomnesis_validator_rejections_total" not in data
    assert "hypomnesis_llm_tokens_total" not in data
    calls = data["hypomnesis_plugin_calls_total"]
    assert {p["attributes"]["kind"] for p in calls} >= {"solver", "estimator", "validator"}
    assert sum(p["count"] for p in data["hypomnesis_plugin_duration_seconds"]) == sum(
        p["value"] for p in calls
    )
    for metric_points in data.values():
        for point in metric_points:
            assert point["attributes"] == bounded_labels(point["attributes"])


def test_real_validator_rejection_and_schema_rejection_are_not_successes():
    session = Session()
    session.load('let check (x : int) = if x > 0 then [] else ["must be positive"]')
    validator = LanguageValidator(session, "check", "int")
    registry = SchemaRegistry([{"$id": SCHEMA, "type": "integer"}])
    with Tracer() as tracer, tracer.span("hypomnesis.run"):
        assert validator.validate(1).ok
        assert not validator.validate(-1).ok
        assert registry.issues(SCHEMA, "not an integer")
    data = points(tracer)
    assert data["hypomnesis_validator_rejections_total"][0]["value"] == 1
    assert data["hypomnesis_schema_validation_total"][0]["attributes"] == {"status": "rejected"}
    assert data["hypomnesis_schema_validation_total"][0]["value"] == 1
    assert "hypomnesis_actuator_failures_total" not in data


def test_a_checker_error_is_not_counted_as_a_mathematical_refutation():
    session = Session()
    session.load('let broken (_ : int) : string list = failwith "fixture checker failure"')
    validator = LanguageValidator(session, "broken", "int")
    with Tracer() as tracer, tracer.span("hypomnesis.run"):
        result = validator.validate(1)
        assert not result.ok and result.diagnostics[0].code == "validator.checker"
    data = points(tracer)
    assert "hypomnesis_validator_rejections_total" not in data
    assert data["hypomnesis_plugin_calls_total"][0]["attributes"] == {
        "kind": "validator",
        "status": "error",
    }


@pytest.mark.parametrize("fail", [False, True])
def test_actuator_outcome_is_counted_once_despite_a_duplicate_submission(fail):
    registry = SchemaRegistry([{"$id": SCHEMA, "type": "object"}])
    dispatcher = Dispatcher(registry, {"execute"}, "production")
    calls = []

    def execute(payload):
        calls.append(payload)
        if fail:
            raise OSError("fixture disk failure")
        return {}

    dispatcher.register(Actuator("local", "execute", SCHEMA, SCHEMA, execute))
    with Tracer() as tracer, tracer.span("hypomnesis.run"):
        command = dispatcher.command("local", {})
        outcome = dispatcher.dispatch(command)
        assert dispatcher.dispatch(command) is outcome
    data = points(tracer)
    commands = data["hypomnesis_actuator_commands_total"]
    assert len(calls) == commands[0]["value"] == 1
    assert commands[0]["attributes"] == {
        "mode": "production",
        "state": "Failed" if fail else "Completed",
    }
    if fail:
        assert data["hypomnesis_actuator_failures_total"][0]["value"] == 1
    else:
        assert "hypomnesis_actuator_failures_total" not in data
    actuator = next(
        p for p in data["hypomnesis_plugin_calls_total"] if p["attributes"]["kind"] == "actuator"
    )
    assert actuator["value"] == 1
    assert actuator["attributes"]["status"] == ("error" if fail else "ok")


def test_private_providers_are_isolated_and_tokens_require_an_explicit_measurement():
    with Tracer() as one, Tracer() as two:
        with one.span("hypomnesis.run"):
            one.metrics.record("hypomnesis_llm_tokens_total", 3, direction="input")
        assert points(two) == {}
        assert points(one)["hypomnesis_llm_tokens_total"][0]["value"] == 3
    assert points(one)["hypomnesis_runs_total"][0]["value"] == 1
    with pytest.raises(ValueError, match="closed"):
        one.metrics.record("hypomnesis_runs_total")


def test_failed_trace_setup_closes_the_already_started_metric_provider(
    metrics_collector, monkeypatch
):
    import opentelemetry.exporter.otlp.proto.http.trace_exporter as exporter

    import hypomnesis.observability.trace as tracing

    endpoint, _, _ = metrics_collector
    created = []

    def capture_metrics(**kwargs):
        metrics = Metrics(**kwargs)
        created.append(metrics)
        return metrics

    def fail_exporter(self, **_kwargs):
        raise ValueError("fixture exporter setup failure")

    monkeypatch.setattr(tracing, "Metrics", capture_metrics)
    monkeypatch.setattr(exporter.OTLPSpanExporter, "__init__", fail_exporter)
    with pytest.raises(ValueError, match="fixture exporter setup failure"):
        Tracer(config=TraceConfig(otlp_endpoint=endpoint, otlp_metrics_endpoint=endpoint))
    assert len(created) == 1 and created[0]._closed


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, 1.5])
def test_counter_values_are_nonnegative_finite_integers(value):
    metrics = Metrics()
    try:
        with pytest.raises(ValueError):
            metrics.record("hypomnesis_runs_total", value)
        with pytest.raises(ValueError, match="unknown metric"):
            metrics.record("some_metric")
    finally:
        metrics.close()


def test_real_metrics_protobuf_arrives_at_the_local_endpoint(
    metrics_collector, monkeypatch, tmp_path
):
    endpoint, received, _ = metrics_collector
    monkeypatch.setenv("HYPOMNESIS_OTLP_METRICS_ENDPOINT", endpoint)
    report = run_procedure(load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path)
    exported = [
        metric
        for path, request in received
        for resource in request.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
        if path == "/v1/metrics"
    ]
    assert {m.name for m in exported} == set(points(report.tracer))
    run = next(m for m in exported if m.name == "hypomnesis_runs_total")
    assert run.sum.data_points[0].as_int == 1
    assert run.sum.is_monotonic
    duration = next(m for m in exported if m.name == "hypomnesis_run_duration_seconds")
    assert duration.unit == "s" and duration.histogram.data_points[0].sum > 0
    assert all(
        resource.resource.attributes[0].value.string_value == "hypomnesis"
        for _, request in received
        for resource in request.resource_metrics
    )


@pytest.mark.parametrize("response", [400, 302])
def test_export_failure_is_logged_and_never_redirected(metrics_collector, caplog, response):
    endpoint, received, responses = metrics_collector
    responses[0] = response
    with (
        Tracer(config=TraceConfig(otlp_metrics_endpoint=endpoint, timeout_seconds=0.1)) as tracer,
        tracer.span("hypomnesis.run"),
    ):
        value = 2 + 3
    assert value == 5 and points(tracer)["hypomnesis_runs_total"][0]["value"] == 1
    assert received and {path for path, _ in received} == {"/v1/metrics"}
    assert str(response) in caplog.text


def test_disabled_telemetry_changes_no_symbolic_result_or_metric(tmp_path):
    active = run_procedure(load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path)
    with Tracer(enabled=False) as tracer:
        disabled = run_procedure(
            load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path, tracer=tracer
        )
    assert points(tracer) == {}
    for key in ("result", "knowledge", "commands", "journal", "stopped"):
        assert active.to_json()[key] == disabled.to_json()[key]


@pytest.mark.parametrize(
    "endpoint", ["https://example.com/v1/metrics", "http://secret@localhost/x", "file:///tmp/x"]
)
def test_metric_export_has_the_same_local_endpoint_restriction(endpoint):
    with pytest.raises(ValueError, match="local"):
        TraceConfig(otlp_metrics_endpoint=endpoint)
