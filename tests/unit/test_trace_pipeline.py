"""Real run trees, concurrent contexts, envelopes and bounded OTLP delivery."""

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from hypomnesis.cli import main
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator, Dispatcher
from hypomnesis.effects.transports import FileTransport, MemoryTransport
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.language.errors import EvaluationError, NameResolutionError
from hypomnesis.observability.trace import (
    TraceConfig,
    Tracer,
    current_tracer,
    extract_context,
    trace_context,
)

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/mecanique"
PROGRAM = ROOT / "demo/programs/mecanique/plaque_120x80.hyp"
PARENT = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"


@pytest.fixture
def collector():
    received = []
    responses = [200]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            received.append((self.path, ExportTraceServiceRequest.FromString(body)))
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
        yield f"http://127.0.0.1:{server.server_port}/v1/traces", received, responses
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_real_cli_tree_and_saved_report_include_the_root(tmp_path, capsys):
    assert main(["lancer", str(LANGUAGE), str(PROGRAM), "--sortie", str(tmp_path)]) == 0
    capsys.readouterr()
    data = json.loads((tmp_path / "rapport.json").read_text())
    spans = data["trace"]["spans"]
    roots = [s for s in spans if s["parent_id"] is None]
    assert [s["name"] for s in roots] == ["hypomnesis.run"]
    names = {s["name"] for s in spans}
    assert {
        "language.parse",
        "language.typecheck",
        "knowledge.resolve",
        "estimator.predict",
        "solver.solve",
        "validator.check",
        "actuator.authorize",
    } <= names
    assert "llm.transcribe" not in names
    assert "actuator.execute" not in names
    assert all(s["span_id"] != s["parent_id"] for s in spans)
    estimator = next(s for s in spans if s["name"] == "estimator.predict")
    assert estimator["attributes"]["plugin"] == "Plaque.estimer_regle"
    assert estimator["attributes"]["plugin.version"] == "0.2.0"
    assert "language" in estimator["attributes"]


def test_received_otlp_is_protobuf_with_the_actual_run_tree(collector, tmp_path):
    endpoint, received, _ = collector
    with Tracer(config=TraceConfig(otlp_endpoint=endpoint)) as tracer:
        report = run_procedure(
            load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path, tracer=tracer
        )
    exported = [
        span
        for path, request in received
        for resource in request.resource_spans
        for scope in resource.scope_spans
        for span in scope.spans
        if path == "/v1/traces"
    ]
    assert exported
    assert {s.name for s in exported} == {s["name"] for s in report.tracer.export()["spans"]}
    assert {s.trace_id.hex() for s in exported} == {tracer.trace_id}
    root = next(s for s in exported if s.name == "hypomnesis.run")
    assert not root.parent_span_id


def test_real_sensor_and_local_export_are_traced_only_when_called(tmp_path):
    source = (PROGRAM.parent / "plaque_mesuree.hyp").read_text()
    report = run_procedure(load_language(LANGUAGE), source, out_dir=tmp_path, mode="production")
    names = [s["name"] for s in report.tracer.export()["spans"]]
    assert "observer.read" in names
    assert "actuator.execute" in names
    assert names.index("actuator.authorize") < names.index("actuator.execute")
    assert not any(span.links for span in report.tracer.spans if span.name == "observer.read")


def test_actual_post_execution_verification_and_deduplication():
    schema = "https://schemas.example.org/hypomnesis/test/1.0.0"
    registry = SchemaRegistry([{"$id": schema, "type": "object"}])
    dispatcher = Dispatcher(registry, {"execute"}, "production")
    calls = []

    def execute(payload):
        calls.append(payload)
        return {}

    dispatcher.register(
        Actuator("local", "execute", schema, schema, execute, observe_effects=lambda _p, _r: [])
    )
    with Tracer() as tracer, tracer.span("hypomnesis.run"):
        command = dispatcher.command("local", {})
        outcome = dispatcher.dispatch(command)
        assert outcome.state == "Completed"
        assert dispatcher.dispatch(command) is outcome
    names = [s.name for s in tracer.spans]
    assert names.count("actuator.execute") == names.count("observer.verify") == len(calls) == 1


def test_otlp_refusal_is_logged_without_affecting_execution(collector, tmp_path, caplog):
    endpoint, received, responses = collector
    responses[0] = 400
    with Tracer(config=TraceConfig(otlp_endpoint=endpoint, timeout_seconds=0.1)) as tracer:
        failed_export = run_procedure(
            load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path, tracer=tracer
        )
    assert received
    assert "400" in caplog.text
    normal = run_procedure(load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path)
    for key in ("result", "knowledge", "commands", "journal", "stopped"):
        assert failed_export.to_json()[key] == normal.to_json()[key]


def test_remote_parent_and_tracestate_are_extracted():
    with Tracer(parent_context={"traceparent": PARENT, "tracestate": "vendor=value"}) as tracer:
        with tracer.span("receiver"):
            assert current_tracer() is tracer
            assert trace_context()["traceparent"].split("-")[1] == PARENT.split("-")[1]
            assert trace_context()["tracestate"] == "vendor=value"
        [span] = tracer.spans
        assert span.parent.is_remote
        assert span.parent.span_id == int(PARENT.split("-")[2], 16)
        assert span.context.trace_state.get("vendor") == "value"
        assert tracer.tree()[0].startswith("receiver ")
    assert current_tracer() is None


@pytest.mark.parametrize(
    "parent",
    ["bad", "00-" + "0" * 32 + "-0123456789abcdef-01", PARENT.replace("00-", "ff-", 1)],
)
def test_malformed_remote_context_is_rejected(parent):
    with pytest.raises(ValueError, match="W3C"):
        extract_context({"traceparent": parent})


def test_thread_contexts_do_not_share_a_mutable_stack():
    with Tracer() as tracer:
        barrier = threading.Barrier(2)

        def run(name):
            with tracer.span(name):
                barrier.wait(timeout=5)
                with tracer.span(name + ".child"):
                    assert current_tracer() is tracer

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(run, ["a", "b"]))
        spans = {s["name"]: s for s in tracer.export()["spans"]}
        for name in ("a", "b"):
            assert spans[name]["parent_id"] is None
            assert spans[name + ".child"]["parent_id"] == spans[name]["span_id"]
    assert current_tracer() is None


def test_async_siblings_inherit_only_their_common_parent():
    with Tracer() as tracer:

        async def run(name):
            with tracer.span(name):
                await asyncio.sleep(0)
                with tracer.span(name + ".child"):
                    await asyncio.sleep(0)

        async def scenario():
            with tracer.span("root"):
                await asyncio.gather(run("a"), run("b"))

        asyncio.run(scenario())
        spans = {s["name"]: s for s in tracer.export()["spans"]}
        for name in ("a", "b"):
            assert spans[name]["parent_id"] == spans["root"]["span_id"]
            assert spans[name + ".child"]["parent_id"] == spans[name]["span_id"]


@pytest.mark.parametrize("kind", ["memory", "file"])
def test_actual_transports_propagate_context_without_mutating_the_envelope(kind, tmp_path):
    schemas = SchemaRegistry.with_builtin_schemas()
    schema = "https://schemas.example.org/hypomnesis/test/1.0.0"
    schemas.add({"$id": schema, "type": "object"})
    transport = (
        MemoryTransport(schemas)
        if kind == "memory"
        else FileTransport(tmp_path / "x.jsonl", schemas)
    )
    envelope = {
        "message_id": "m1",
        "timestamp": "2026-11-05T12:00:00Z",
        "schema_id": schema,
        "schema_version": "1.0.0",
        "payload": {"value": 42},
    }
    with Tracer() as sender, sender.span("send"):
        transport.send(envelope)
        expected = trace_context(sender)
    message = transport.receive()
    assert message["trace_context"] == expected
    assert "trace_context" not in envelope
    assert message["payload"] == envelope["payload"]
    with Tracer(parent_context=message["trace_context"]) as receiver, receiver.span("receive"):
        assert receiver.trace_id == sender.trace_id
    transport.send(message)
    assert transport.receive() == message


def test_invalid_incoming_sensor_context_is_reported_without_payload_fallback(capsys):
    with Tracer() as tracer, tracer.span("observer.read") as span:
        tracer.link_message(span, {"trace_context": {"traceparent": "bad"}})
    records = [json.loads(line) for line in capsys.readouterr().err.splitlines()]
    warning = next(record for record in records if record["event"] == "telemetry.context.invalid")
    assert warning["level"] == "WARNING" and warning["reason_code"] == "invalid_trace_context"
    assert warning["trace_id"] == tracer.trace_id


@pytest.mark.parametrize(
    "endpoint",
    ["https://example.com/v1/traces", "file:///tmp/x", "http://secret@localhost/x"],
)
def test_otlp_requires_an_explicit_local_endpoint(endpoint):
    with pytest.raises(ValueError, match="local"):
        TraceConfig(otlp_endpoint=endpoint)


def test_configuration_disable_and_provider_cleanup(monkeypatch, tmp_path):
    monkeypatch.setenv("HYPOMNESIS_TELEMETRY", "0")
    report = run_procedure(load_language(LANGUAGE), PROGRAM.read_text(), out_dir=tmp_path)
    assert report.tracer.export()["spans"] == []
    assert report.tracer._closed
    assert report.tracer._provider is None
    with pytest.raises(ValueError, match="closed"), report.tracer.span("after.close"):
        pass
    monkeypatch.setenv("HYPOMNESIS_TELEMETRY", "not-a-boolean")
    with pytest.raises(ValueError, match="0 or 1"):
        Tracer()


def test_call_instrumentation_is_restored_after_failure(tmp_path):
    language = load_language(LANGUAGE)
    with pytest.raises(EvaluationError, match="Match_failure"):
        run_procedure(
            language, "let procedure = match false with true -> Effect.return 1", out_dir=tmp_path
        )
    assert language.session.interpreter.call_context is None
    assert current_tracer() is None


def test_tracing_references_are_checked_statically(tmp_path):
    (tmp_path / "langage.hyp").write_text(
        'language example = struct let version = "1" '
        'let tracing = [{function = "missing"; operation = "estimator.predict"}] end'
    )
    with pytest.raises(NameResolutionError, match="missing"):
        load_language(tmp_path, execute=False)


def test_otlp_never_follows_collector_redirects(collector, caplog):
    endpoint, received, responses = collector
    responses[0] = 302
    with (
        Tracer(config=TraceConfig(otlp_endpoint=endpoint, timeout_seconds=0.1)) as tracer,
        tracer.span("local.only"),
    ):
        pass
    assert [path for path, _ in received] == ["/v1/traces"]
    assert "302" in caplog.text
