"""MVP metrics reflect success and genuine failures, never invented counters."""

from dataclasses import replace

import examples.mechanics.mvp as mvp
import pytest

from hypomnesis.observability.trace import Tracer


@pytest.mark.parametrize("scenario", ["success", "denied", "disk_failure"])
def test_mvp_metrics_are_actual_sdk_measurements(scenario, tmp_path, monkeypatch):
    tracers = []

    def capture_tracer():
        tracer = Tracer()
        tracers.append(tracer)
        return tracer

    monkeypatch.setattr(mvp, "Tracer", capture_tracer)
    if scenario == "disk_failure":
        original = mvp.trace_actuator

        def broken_action(action, tracer):
            def execute(_payload):
                raise OSError("fixture disk failure")

            return original(replace(action, execute=execute), tracer)

        monkeypatch.setattr(mvp, "trace_actuator", broken_action)
    if scenario == "success":
        assert mvp.run_mvp(tmp_path)["status"] == "completed"
    else:
        with pytest.raises(RuntimeError, match="Rejected" if scenario == "denied" else "Failed"):
            mvp.run_mvp(
                tmp_path,
                permissions=frozenset()
                if scenario == "denied"
                else frozenset({"actuator:geometry.export"}),
            )
    (tracer,) = tracers
    assert tracer._closed
    metrics = {
        metric["name"]: metric["data"]["data_points"]
        for resource in tracer.metrics.snapshot()["resource_metrics"]
        for scope in resource["scope_metrics"]
        for metric in scope["metrics"]
    }
    assert {
        "hypomnesis_runs_total",
        "hypomnesis_run_duration_seconds",
        "hypomnesis_plugin_calls_total",
        "hypomnesis_plugin_duration_seconds",
        "hypomnesis_schema_validation_total",
        "hypomnesis_solver_duration_seconds",
        "hypomnesis_estimator_calls_total",
        "hypomnesis_actuator_commands_total",
    } <= metrics.keys()
    assert metrics["hypomnesis_runs_total"][0]["value"] == 1
    assert metrics["hypomnesis_runs_total"][0]["attributes"] == {
        "status": "ok" if scenario == "success" else "error"
    }
    commands = metrics["hypomnesis_actuator_commands_total"]
    assert commands[0]["value"] == 1
    assert (
        commands[0]["attributes"]["state"]
        == {"success": "Completed", "denied": "Rejected", "disk_failure": "Failed"}[scenario]
    )
    assert ("hypomnesis_actuator_failures_total" in metrics) == (scenario == "disk_failure")
    assert "hypomnesis_validator_rejections_total" not in metrics
    assert "hypomnesis_llm_tokens_total" not in metrics
