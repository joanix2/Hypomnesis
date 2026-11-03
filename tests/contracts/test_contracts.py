import json
from pathlib import Path

import pytest
from jsonschema.exceptions import SchemaError

from hypomnesis.contracts.registry import MANIFEST_ID, ContractError, SchemaRegistry

FIXTURES = Path(__file__).parent / "fixtures"
MOTOR_ID = "https://schemas.example.org/hypomnesis/motor.move/1.0.0"


@pytest.fixture
def registry() -> SchemaRegistry:
    reg = SchemaRegistry.with_builtin_schemas()
    reg.add(json.loads((FIXTURES / "motor.move-1.0.0.json").read_text()))
    return reg


def envelope(payload, **overrides):
    message = {
        "message_id": "msg-1",
        "schema_id": MOTOR_ID,
        "schema_version": "1.0.0",
        "timestamp": "2026-11-03T10:00:00Z",
        "correlation_id": "run-001",
        "trace_context": {"traceparent": "00-" + "a" * 32 + "-" + "b" * 16 + "-01"},
        "payload": payload,
    }
    message.update(overrides)
    return message


COMMAND = {"command_id": "cmd-42", "motor_id": "motor_1", "position_deg": 90, "speed_deg_s": 20}

MANIFEST = {
    "id": "motor.move",
    "version": "1.0.0",
    "role": "Actuator",
    "signature": {"input": "Motor.move_command", "output": "Motor.move_result"},
    "input_schema": MOTOR_ID,
    "output_schema": "https://schemas.example.org/hypomnesis/motor.move.result/1.0.0",
    "permissions": ["actuator:motor.move"],
    "backend": {"kind": "python", "entry_point": "robotics.motor:move"},
    "error_policy": {"idempotent": False, "timeout_seconds": 5, "max_attempts": 1},
}


def test_valid_command_passes(registry):
    assert registry.validate_message(envelope(COMMAND)) == COMMAND


@pytest.mark.parametrize(
    "change",
    [
        {"position_deg": 181},
        {"speed_deg_s": 0},
        {"motor_id": ""},
        {"unexpected": True},
    ],
)
def test_invalid_command_is_rejected(registry, change):
    with pytest.raises(ContractError) as info:
        registry.validate_message(envelope({**COMMAND, **change}))
    assert info.value.schema_id == MOTOR_ID


def test_missing_field_is_reported_with_path(registry):
    payload = dict(COMMAND)
    del payload["speed_deg_s"]
    issues = registry.issues(MOTOR_ID, payload)
    assert len(issues) == 1 and "speed_deg_s" in issues[0].message


def test_envelope_is_validated(registry):
    with pytest.raises(ContractError):
        registry.validate_message(envelope(COMMAND, timestamp="yesterday"))
    with pytest.raises(ContractError):
        registry.validate_message(envelope(COMMAND, trace_context={"traceparent": "nope"}))


def test_schema_version_must_match_schema_id(registry):
    with pytest.raises(ContractError, match="schema_version"):
        registry.validate_message(envelope(COMMAND, schema_version="1.1.0"))


def test_unknown_payload_schema(registry):
    with pytest.raises(ContractError, match="unknown schema"):
        registry.validate_message(
            envelope(COMMAND, schema_id="https://schemas.example.org/x/1.0.0")
        )


def test_manifest_validation(registry):
    registry.validate(MANIFEST_ID, MANIFEST)


def test_non_idempotent_extensions_cannot_retry(registry):
    manifest = {**MANIFEST, "error_policy": {**MANIFEST["error_policy"], "max_attempts": 3}}
    with pytest.raises(ContractError):
        registry.validate(MANIFEST_ID, manifest)


def test_manifest_role_is_restricted(registry):
    with pytest.raises(ContractError):
        registry.validate(MANIFEST_ID, {**MANIFEST, "role": "Wizard"})


def test_registry_rejects_invalid_or_conflicting_schemas(registry):
    with pytest.raises(SchemaError):
        registry.add({"$id": "https://schemas.example.org/broken/1.0.0", "type": "nonsense"})
    with pytest.raises(ValueError, match="different content"):
        registry.add({"$id": MOTOR_ID, "type": "object"})
    with pytest.raises(ValueError, match=r"\$id"):
        registry.add({"type": "object"})
