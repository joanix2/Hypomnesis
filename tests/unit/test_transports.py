"""Transport parity and exact, validated JSONL replay (HYP-063)."""

import json

import pytest

from hypomnesis.contracts.registry import ContractError, SchemaRegistry
from hypomnesis.effects.transports import FileTransport, MemoryTransport, replay
from hypomnesis.language.errors import EvaluationError

SCHEMA = "https://test.example/value/1.0.0"


def registry():
    result = SchemaRegistry.with_builtin_schemas()
    result.add(
        {
            "$id": SCHEMA,
            "type": "object",
            "properties": {"value": {"type": "integer"}},
            "required": ["value"],
            "additionalProperties": False,
        }
    )
    return result


def message(index=1):
    return {
        "message_id": f"msg-{index}",
        "schema_id": SCHEMA,
        "schema_version": "1.0.0",
        "timestamp": "2026-11-04T20:00:00Z",
        "correlation_id": "original-correlation",
        "trace_context": {"traceparent": "00-" + "a" * 32 + "-" + "b" * 16 + "-01"},
        "payload": {"value": index},
    }


@pytest.fixture(params=["memory", "files"])
def transport(request, tmp_path):
    return (
        MemoryTransport(registry())
        if request.param == "memory"
        else FileTransport(tmp_path / "nested/scenario.jsonl", registry())
    )


def test_fifo_detaches_input_and_received_messages(transport):
    first = message()
    transport.send(first)
    first["payload"]["value"] = -1
    transport.send(message(2))
    assert transport.receive() == message()
    assert transport.receive() == message(2)
    assert transport.receive() is None
    transport.send(message(3))
    assert transport.receive() == message(3)


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": "2.0.0"},
        {"timestamp": "yesterday"},
        {"schema_id": "https://test.example/missing/1.0.0"},
        {"payload": {"value": "wrong"}},
        {"extra": True},
    ],
)
def test_invalid_envelope_or_payload_never_enters_queue(transport, change):
    with pytest.raises(ContractError):
        transport.send({**message(), **change})
    assert transport.receive() is None


@pytest.mark.parametrize(
    "payload",
    [
        {"value": float("nan")},
        {"value": (1,)},
        {1: "not a string"},
    ],
)
def test_non_json_values_are_not_coerced(transport, payload):
    with pytest.raises((ValueError, EvaluationError)):
        transport.send({**message(), "payload": payload})
    assert transport.receive() is None


@pytest.mark.parametrize(
    "bad",
    [
        "[]\n",
        '{"x":1,"x":2}\n',
        '{"x":NaN}\n',
        "not json\n",
        json.dumps({**message(), "schema_version": "2.0.0"}) + "\n",
        json.dumps(message()),
    ],
)
def test_corrupt_file_is_reported_without_advancing_reader(tmp_path, bad):
    path = tmp_path / "scenario.jsonl"
    path.write_text(bad, encoding="utf-8")
    reader = FileTransport(path, registry())
    for _ in range(2):
        with pytest.raises((ValueError, ContractError)):
            reader.receive()


def test_replay_preserves_all_envelope_fields_and_original_log(tmp_path):
    path = tmp_path / "scenario.jsonl"
    writer = FileTransport(path, registry())
    messages = [message(i) for i in range(4)]
    for item in messages:
        writer.send(item)
        assert writer.receive() == item
    original = path.read_bytes()
    target = MemoryTransport(registry())
    assert replay(FileTransport(path, registry()), target) == len(messages)
    assert [target.receive() for _ in messages] == messages
    assert target.receive() is None
    assert path.read_bytes() == original


def test_failed_replay_validates_source_before_delivering_any_message(tmp_path):
    path = tmp_path / "scenario.jsonl"
    path.write_text(json.dumps(message()) + "\n{}\n", encoding="utf-8")
    target = MemoryTransport(registry())
    with pytest.raises(ContractError):
        replay(FileTransport(path, registry()), target)
    assert target.receive() is None


def test_replay_rejects_a_transport_into_itself(transport):
    with pytest.raises(ValueError, match="distinct"):
        replay(transport, transport)
