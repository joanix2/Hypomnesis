"""Tracer facade: span tree, JSON export and W3C trace context (HYP-015)."""

import json
import re
from pathlib import Path

import pytest

from hypomnesis.contracts.registry import ENVELOPE_ID, SchemaRegistry
from hypomnesis.engine import procedure
from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure
from hypomnesis.observability.trace import Tracer, trace_context

ROOT = Path(__file__).resolve().parents[2]
MECANIQUE = ROOT / "languages" / "mecanique"
PLAQUE = (ROOT / "programs" / "mecanique" / "plaque_120x80.hyp").read_text()


def scenario() -> Tracer:
    tracer = Tracer()
    with tracer.span("hypomnesis.run", langage="demo", mode="dry-run"):
        with tracer.span("observer.read", capteur="s"):
            pass
        with (
            pytest.raises(ValueError),
            tracer.span("actuator.execute", actionneur="a", count=3),
        ):
            raise ValueError("boom")
        with tracer.span("solver.solve", contraintes=2):
            pass
    return tracer


def test_export_keeps_the_report_format():
    exported = scenario().export()
    assert re.fullmatch(r"[0-9a-f]{32}", exported["trace_id"])
    spans = exported["spans"]
    # Spans are listed in start order, whatever the order they finished in.
    assert [s["name"] for s in spans] == [
        "hypomnesis.run",
        "observer.read",
        "actuator.execute",
        "solver.solve",
    ]
    for s in spans:
        assert set(s) == {"name", "span_id", "parent_id", "duration_ms", "status", "attributes"}
        assert re.fullmatch(r"[0-9a-f]{16}", s["span_id"])
        assert isinstance(s["duration_ms"], float) and s["duration_ms"] >= 0
    root, read, act, solve = spans
    assert root["parent_id"] is None
    assert {read["parent_id"], act["parent_id"], solve["parent_id"]} == {root["span_id"]}
    assert [s["status"] for s in spans] == ["ok", "ok", "error", "ok"]
    assert root["attributes"] == {"langage": "demo", "mode": "dry-run"}
    assert act["attributes"] == {"actionneur": "a", "count": 3}
    assert solve["attributes"] == {"contraintes": 2}
    json.dumps(exported)  # JSON-ready


def test_tree_is_indented_and_marks_errors():
    lines = scenario().tree()
    assert [line.split(" (")[0] for line in lines] == [
        "hypomnesis.run",
        "  observer.read",
        "  actuator.execute",
        "  solver.solve",
    ]
    assert re.fullmatch(r"  actuator\.execute \(\d+(\.\d+)? ms\) \[error\]", lines[2])
    assert re.fullmatch(r"hypomnesis\.run \(\d+(\.\d+)? ms\)", lines[0])


def test_unsupported_attribute_values_are_stringified():
    tracer = Tracer()
    with tracer.span("x", obj=(1, 2), items=[1], flag=True, ratio=0.5, none=None):
        pass
    attrs = tracer.export()["spans"][0]["attributes"]
    assert attrs == {
        "obj": "(1, 2)",
        "items": "[1]",
        "flag": True,
        "ratio": 0.5,
        "none": "None",
    }


def test_each_tracer_has_its_own_provider():
    a, b = Tracer(), Tracer()
    with a.span("only.a"):
        pass
    assert b.export()["spans"] == []
    assert a.trace_id != b.trace_id
    assert [s["name"] for s in a.export()["spans"]] == ["only.a"]


def test_trace_id_is_the_one_of_the_spans():
    tracer = Tracer()
    with tracer.span("x"):
        assert trace_context(tracer)["traceparent"].split("-")[1] == tracer.trace_id
    assert tracer.export()["trace_id"] == tracer.trace_id


def test_trace_context_conforms_to_the_envelope_schema():
    tracer = Tracer()
    registry = SchemaRegistry.with_builtin_schemas()
    contexts = [trace_context(tracer)]  # no active span: unsampled root
    with tracer.span("hypomnesis.run"):
        contexts.append(trace_context(tracer))
    for ctx in contexts:
        message = {
            "message_id": "m-1",
            "schema_id": "https://schemas.example.org/hypomnesis/x/1.0.0",
            "schema_version": "1.0.0",
            "timestamp": "2026-11-03T10:00:00Z",
            "trace_context": ctx,
            "payload": {},
        }
        assert registry.issues(ENVELOPE_ID, message) == []


def test_trace_context_points_to_the_current_span():
    tracer = Tracer()
    with tracer.span("outer"):
        ctx = trace_context(tracer)
    span_id = tracer.export()["spans"][0]["span_id"]
    assert ctx["traceparent"] == f"00-{tracer.trace_id}-{span_id}-01"


def test_trace_context_without_span_uses_an_unsampled_root():
    ctx = trace_context(Tracer())
    assert re.fullmatch(r"00-[0-9a-f]{32}-0{16}-00", ctx["traceparent"])


def test_disabled_telemetry_changes_no_knowledge(tmp_path, monkeypatch):
    language = load_language(MECANIQUE)
    with_trace = run_procedure(language, PLAQUE, out_dir=tmp_path, mode="production")
    assert with_trace.tracer.export()["spans"]

    monkeypatch.setattr(procedure, "Tracer", lambda: Tracer(enabled=False))
    without = run_procedure(load_language(MECANIQUE), PLAQUE, out_dir=tmp_path, mode="production")
    assert without.tracer.export()["spans"] == []
    assert without.tracer.tree() == []

    def knowledge(report):
        data = report.to_json()
        return {k: data[k] for k in ("result", "stopped", "knowledge", "commands", "journal")}

    assert knowledge(without) == knowledge(with_trace)
