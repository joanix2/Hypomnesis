"""Adaptateurs du langage « ventilation » : une pièce simulée (capteur et ventilateur).

Tiennent la place du matériel. Options d'environnement : `temperature` (°C
initiaux), `panne` (le ventilateur ne refroidit pas). Les relevés sont émis
dans l'enveloppe de message standard (§9.6).
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.effects.dispatcher import Actuator
from hypomnesis.effects.transports import FileTransport, MemoryTransport, Transport
from hypomnesis.engine.adapters import actuator, environment, sensor

READING = "https://schemas.example.org/hypomnesis/temperature.reading/1.0.0"
REQUEST = "https://schemas.example.org/hypomnesis/temperature.read/1.0.0"
COMMAND = "https://schemas.example.org/hypomnesis/fan.set/1.0.0"
RESULT = "https://schemas.example.org/hypomnesis/fan.set.result/1.0.0"


class Piece:
    def __init__(self, options: Mapping[str, Any], out_dir: Path) -> None:
        self.celsius = float(options.get("temperature", 31.0))
        self.panne = str(options.get("panne", "")).lower() in ("1", "true", "oui")
        self.vitesse = 0
        self._ids = itertools.count(1)
        self._lu = False
        registry = SchemaRegistry.with_builtin_schemas()
        for contract in sorted((Path(__file__).parents[1] / "contrats").glob("*.json")):
            registry.add(json.loads(contract.read_text(encoding="utf-8")))
        kind = options.get("transport", "memory")
        self.transport: Transport
        if kind == "memory":
            self.transport = MemoryTransport(registry)
        elif kind == "files":
            self.transport = FileTransport(out_dir / "scenarios" / f"{uuid4().hex}.jsonl", registry)
        else:
            raise ValueError(f"transport inconnu : {kind}")

    def exchange(
        self, schema: str, payload: Mapping[str, Any], correlation: str = "ventilation"
    ) -> dict[str, Any]:
        envelope = {
            "message_id": f"msg-{next(self._ids)}",
            "schema_id": schema,
            "schema_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "correlation_id": correlation,
            "payload": dict(payload),
        }
        self.transport.send(envelope)
        message = self.transport.receive()
        if message is None:
            raise RuntimeError("le périphérique simulé n'a reçu aucun message")
        return message

    def message(self, capteur: str) -> dict[str, Any]:
        """Relevé du capteur ; la physique avance d'un pas entre deux relevés."""
        request = self.exchange(REQUEST, {"sensor_id": capteur})
        if self._lu:
            self.tick()
        self._lu = True
        return self.exchange(
            READING,
            {"sensor_id": request["payload"]["sensor_id"], "celsius": round(self.celsius, 2)},
            request["message_id"],
        )

    def tick(self) -> None:
        self.celsius += 0.2 if self.panne or self.vitesse == 0 else -self.vitesse / 25


@environment
def piece(options: Mapping[str, Any], out_dir: Any) -> Piece:
    return Piece(options, Path(out_dir))


@sensor("thermo-1")
def lire(env: Piece, identifier: str) -> dict[str, Any]:
    return env.message(identifier)


@actuator("fan.set")
def ventilateur(env: Piece) -> Actuator:
    def executer(payload: Mapping[str, Any]) -> dict[str, Any]:
        command = env.exchange(COMMAND, payload, payload["command_id"])
        env.vitesse = command["payload"]["speed_percent"]
        response = env.exchange(
            RESULT,
            {"status": "accepted", "speed_percent": env.vitesse},
            command["correlation_id"],
        )
        return response["payload"]

    return Actuator(
        "fan.set",
        "actuator:fan.set",
        COMMAND,
        RESULT,
        executer,
    )
