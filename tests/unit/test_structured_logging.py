"""Default telemetry never formats raw prompts, personal payloads or exceptions."""

import asyncio
import io
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from hypomnesis.cli import main
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.observability.logging import (
    REDACTED,
    JsonFormatter,
    JsonLogger,
    RedactionPolicy,
    export_diagnostics,
)
from hypomnesis.observability.trace import TraceConfig, Tracer, log_event

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/ventilation"
SECRET = "PRIVATE_PROMPT__do_not_record_this_person_or_payload"


def records(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_default_json_fields_are_redacted_at_every_depth_without_rendering_objects():
    class Unprintable:
        def __repr__(self):
            raise AssertionError("an untrusted object must not be rendered")

    stream = io.StringIO()
    logger = JsonLogger(stream=stream)
    logger.emit(
        "llm.transcription.received",
        prompt=SECRET,
        payload={"person": {"email": SECRET}},
        attributes={
            "plugin": "fixture",
            "messages": [{"role": "user", "content": SECRET}],
            "status": SECRET,
            "unknown": Unprintable(),
            SECRET: SECRET,
        },
        unknown=Unprintable(),
    )
    logger.close()
    assert SECRET not in stream.getvalue()
    document = records(stream)[0]
    assert document["event"] == "llm.transcription.received"
    assert document["prompt"] == document["payload"] == REDACTED
    assert document["attributes"]["plugin"] == "fixture"
    assert document["attributes"]["messages"] == document["attributes"]["status"] == REDACTED
    assert document["redacted"] is True
    assert document["level"] == "INFO" and document["timestamp"]


def test_policy_can_hide_additional_metadata_but_cannot_unprotect_prompts():
    stream = io.StringIO()
    with (
        Tracer(
            log_stream=stream,
            log_policy=RedactionPolicy(additional_sensitive_keys=frozenset({"plugin"})),
        ) as tracer,
        tracer.span("hypomnesis.run", plugin="host-selected", prompt=SECRET),
    ):
        log_event("custom.plugin.called", plugin="host-selected", prompt=SECRET)
    assert "host-selected" not in stream.getvalue() and SECRET not in stream.getvalue()
    assert all(record.get("plugin", REDACTED) == REDACTED for record in records(stream))
    assert tracer.export()["spans"][0]["attributes"] == {"plugin": REDACTED, "prompt": REDACTED}


def test_original_exception_propagates_but_no_message_traceback_notes_or_cause_is_recorded():
    class UnprintableError(ValueError):
        def __str__(self):
            raise AssertionError("exception formatting would leak data")

    error = UnprintableError(SECRET)
    error.add_note(SECRET)
    stream = io.StringIO()
    with (
        pytest.raises(UnprintableError) as caught,
        Tracer(log_stream=stream) as tracer,
        tracer.span("observer.read", payload={"email": SECRET}),
    ):
        raise error
    assert caught.value is error
    span = tracer.spans[0]
    assert span.status.description == "UnprintableError"
    assert span.events[0].attributes == {
        "exception.type": "UnprintableError",
        "exception.message": REDACTED,
        "exception.stacktrace": REDACTED,
    }
    assert span.attributes == {"payload": REDACTED}
    assert SECRET not in stream.getvalue() + json.dumps(tracer.export())
    document = records(stream)[0]
    assert document["event"] == "operation.failed" and document["level"] == "ERROR"
    assert document["operation"] == "observer.read" and document["status"] == "error"
    assert document["run_id"] == tracer.run_id and document["trace_id"] == tracer.trace_id
    assert document["span_id"] == tracer.export()["spans"][0]["span_id"]


def test_generic_log_formatter_does_not_interpolate_arguments_or_exception_messages():
    try:
        raise ValueError(SECRET)
    except ValueError as exc:
        record = logging.LogRecord(
            "fixture",
            logging.ERROR,
            __file__,
            1,
            SECRET + " %s",
            (SECRET,),
            (type(exc), exc, exc.__traceback__),
        )
    encoded = JsonFormatter().format(record)
    assert SECRET not in encoded and "Traceback" not in encoded
    assert json.loads(encoded)["event"] == "external.log"


def test_redaction_is_bounded_even_for_cyclic_structures_and_non_finite_values():
    fields = {"duration_ms": float("nan")}
    fields["attributes"] = fields
    stream = io.StringIO()
    logger = JsonLogger(stream=stream)
    logger.emit("cyclic.metadata.seen", **fields)
    logger.close()
    document = records(stream)[0]
    assert document["duration_ms"] == REDACTED
    assert "redacted" in stream.getvalue()
    policy = RedactionPolicy()
    assert len(repr(policy.span_attributes(fields))) < 1000


def test_threads_and_async_tasks_keep_their_own_log_span_context():
    stream = io.StringIO()
    with Tracer(log_stream=stream) as tracer:

        def thread(name):
            with tracer.span(name):
                log_event("worker.progress", plugin=name)
                return name

        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(thread, ["thread.a", "thread.b"])) == ["thread.a", "thread.b"]

        async def task(name):
            with tracer.span(name):
                await asyncio.sleep(0)
                log_event("worker.progress", plugin=name)

        async def both():
            await asyncio.gather(task("async.a"), task("async.b"))

        asyncio.run(both())
    spans = {span["name"]: span for span in tracer.export()["spans"]}
    progress = [record for record in records(stream) if record["event"] == "worker.progress"]
    assert len(progress) == 4
    for record in progress:
        assert record["span_id"] == spans[record["plugin"]]["span_id"]
        assert record["trace_id"] == tracer.trace_id and record["run_id"] == tracer.run_id


def test_distinct_runs_under_the_same_remote_trace_do_not_share_a_run_id():
    parent = {"traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"}
    streams = [io.StringIO(), io.StringIO()]
    with (
        Tracer(parent_context=parent, log_stream=streams[0]) as a,
        Tracer(parent_context=parent, log_stream=streams[1]) as b,
    ):
        with a.span("first.operation"):
            pass
        with b.span("second.operation"):
            pass
    assert a.trace_id == b.trace_id and a.run_id != b.run_id
    assert records(streams[0])[0]["run_id"] != records(streams[1])[0]["run_id"]


@pytest.mark.parametrize("variable", ["HYPOMNESIS_LOGS", "HYPOMNESIS_TELEMETRY"])
def test_log_disable_is_explicit_and_accepts_only_boolean_flags(variable, monkeypatch):
    monkeypatch.setenv(variable, "0")
    stream = io.StringIO()
    with Tracer(log_stream=stream) as tracer, tracer.span("hypomnesis.run"):
        log_event("custom.value.seen", prompt=SECRET)
    assert stream.getvalue() == ""
    monkeypatch.setenv(variable, "invalid")
    with pytest.raises(ValueError, match="0 or 1"):
        Tracer()


def test_json_cli_stdout_stays_semantic_and_stderr_contains_only_safe_telemetry(tmp_path, capsys):
    program = tmp_path / "secret_note.hyp"
    program.write_text(f'let procedure = Effect.note "{SECRET}" >>= fun () -> Effect.return "done"')
    assert (
        main(
            [
                "lancer",
                str(LANGUAGE),
                str(program),
                "--format",
                "json",
                "--sortie",
                str(tmp_path / "out"),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["report"]["notes"] == [SECRET]
    assert SECRET not in captured.err
    logs = [json.loads(line) for line in captured.err.splitlines()]
    spans = {span["span_id"] for span in result["report"]["trace"]["spans"]}
    assert logs and all(log["span_id"] in spans for log in logs)
    assert len({log["run_id"] for log in logs}) == 1
    assert {log["trace_id"] for log in logs} == {result["report"]["trace"]["trace_id"]}


def test_log_switch_changes_no_result_knowledge_or_command(tmp_path):
    language = ROOT / "demo/languages/mecanique"
    source = (ROOT / "demo/programs/mecanique/plaque_120x80.hyp").read_text()
    stream = io.StringIO()
    with (
        Tracer(log_stream=stream) as active,
        Tracer(config=TraceConfig(logs_enabled=False), log_stream=stream) as disabled,
    ):
        one = run_procedure(load_language(language), source, out_dir=tmp_path, tracer=active)
        before = len(stream.getvalue())
        two = run_procedure(load_language(language), source, out_dir=tmp_path, tracer=disabled)
        assert len(stream.getvalue()) == before
    for key in ("result", "knowledge", "commands", "journal", "stopped"):
        assert one.to_json()[key] == two.to_json()[key]
    finished = [
        record for record in records(stream) if record["event"] == "actuator.command.finished"
    ]
    assert len(finished) == len(one.commands)
    assert all(record["status"] == "DryRun" for record in finished)
    assert all("payload" not in record for record in finished)


def test_sdk_diagnostics_redact_args_and_tracebacks_only_inside_our_export(caplog):
    sdk = logging.getLogger("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    with export_diagnostics("traces", "a" * 32, "b" * 32):
        try:
            raise ValueError(SECRET)
        except ValueError:
            sdk.exception("refused %s %s", 400, SECRET)
    assert SECRET not in caplog.text and "400" in caplog.text
    safe = json.loads(caplog.records[-1].getMessage())
    assert safe["event"] == "telemetry.export.failed" and safe["trace_id"] == "b" * 32
    assert safe["run_id"] == "a" * 32 and safe["http_status"] == 400
    sdk.warning("unrelated SDK diagnostic")
    assert caplog.records[-1].getMessage() == "unrelated SDK diagnostic"


@pytest.mark.parametrize("signal", ["traces", "metrics"])
def test_actual_collector_error_body_never_reaches_diagnostic_logs(signal, caplog):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers["Content-Length"])))
            body = SECRET.encode()
            self.send_response(400)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/v1/{signal}"
    stream = io.StringIO()
    config = TraceConfig(
        otlp_endpoint=endpoint if signal == "traces" else None,
        otlp_metrics_endpoint=endpoint if signal == "metrics" else None,
        timeout_seconds=0.1,
    )
    try:
        with (
            pytest.raises(ValueError, match=SECRET),
            Tracer(config=config, log_stream=stream) as tracer,
            tracer.span("hypomnesis.run"),
        ):
            raise ValueError(SECRET)
        assert received and SECRET.encode() not in b"".join(received)
        assert SECRET not in caplog.text + stream.getvalue()
        errors = [
            json.loads(record.getMessage())
            for record in caplog.records
            if record.name.startswith("opentelemetry") and record.levelno >= logging.ERROR
        ]
        assert errors
        assert all(error["http_status"] == 400 for error in errors)
        assert all(error["run_id"] == tracer.run_id for error in errors)
        assert all(error["trace_id"] == tracer.trace_id for error in errors)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_invalid_log_configuration_is_explicit_and_closed_loggers_cannot_silently_drop_events():
    with pytest.raises(ValueError, match="nonempty"):
        RedactionPolicy(additional_sensitive_keys=frozenset({""}))
    logger = JsonLogger(stream=io.StringIO())
    with pytest.raises(ValueError, match="dotted"):
        logger.emit("invalid freeform event")
    with pytest.raises(ValueError, match="level"):
        logger.emit("valid.event", level=12)
    logger.close()
    with pytest.raises(ValueError, match="closed"):
        logger.emit("valid.event")
