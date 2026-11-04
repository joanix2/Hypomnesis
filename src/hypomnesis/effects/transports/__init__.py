"""Synchronous envelope transports; contracts do not depend on storage."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.runtime.json import data_to_json


class Transport(Protocol):
    def send(self, message: Mapping[str, Any]) -> None: ...

    def receive(self) -> dict[str, Any] | None: ...


def _encode(registry: SchemaRegistry, message: Mapping[str, Any]) -> str:
    data = dict(message)
    encoded = json.dumps(data, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    data_to_json(data)
    registry.validate_message(data)
    return encoded


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member: {key}")
        result[key] = value
    return result


def _decode(registry: SchemaRegistry, encoded: str) -> dict[str, Any]:
    data = json.loads(encoded, object_pairs_hook=_object)
    if not isinstance(data, dict):
        raise ValueError("a message must be a JSON object")
    _encode(registry, data)
    return data


class MemoryTransport:
    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry
        self._messages: deque[str] = deque()

    def send(self, message: Mapping[str, Any]) -> None:
        self._messages.append(_encode(self.registry, message))

    def receive(self) -> dict[str, Any] | None:
        if not self._messages:
            return None
        message = _decode(self.registry, self._messages[0])
        self._messages.popleft()
        return message


class FileTransport:
    """Single-process append-only JSONL FIFO, with a reader-local byte cursor."""

    def __init__(self, path: Path, registry: SchemaRegistry) -> None:
        self.path = path
        self.registry = registry
        self._offset = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def send(self, message: Mapping[str, Any]) -> None:
        encoded = _encode(self.registry, message)
        with self.path.open("ab") as stream:
            stream.write((encoded + "\n").encode("utf-8"))

    def receive(self) -> dict[str, Any] | None:
        with self.path.open("rb") as stream:
            stream.seek(self._offset)
            line = stream.readline()
            if not line:
                return None
            if not line.endswith(b"\n"):
                raise ValueError(f"incomplete message at byte {self._offset} in {self.path}")
            message = _decode(self.registry, line.decode("utf-8"))
            self._offset = stream.tell()
        return message


def replay(source: Transport, target: Transport) -> int:
    """Copy a finite recorded scenario before allowing target writes."""
    if source is target:
        raise ValueError("replay requires distinct transports")
    messages = []
    while (message := source.receive()) is not None:
        messages.append(message)
    for message in messages:
        target.send(message)
    return len(messages)
