"""Adaptateurs du langage « ventilation » : une pièce simulée (capteur et ventilateur).

Tiennent la place du matériel. Options d'environnement : `temperature` (°C
initiaux), `panne` (le ventilateur ne refroidit pas). Les relevés sont émis
dans l'enveloppe de message standard (§9.6).
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from hypomnesis.effects.dispatcher import Actuator

READING = "https://schemas.example.org/hypomnesis/temperature.reading/1.0.0"


class Piece:
    def __init__(self, installation: Mapping[str, Any], options: Mapping[str, Any]) -> None:
        self.capteur = installation["capteur"]
        self.celsius = float(options.get("temperature", 31.0))
        self.panne = str(options.get("panne", "")).lower() in ("1", "true", "oui")
        self.vitesse = 0
        self._ids = itertools.count(1)

    def message(self) -> dict[str, Any]:
        return {
            "message_id": f"msg-{next(self._ids)}",
            "schema_id": READING,
            "schema_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "correlation_id": "ventilation",
            "payload": {"sensor_id": self.capteur, "celsius": round(self.celsius, 2)},
        }

    def tick(self) -> None:
        self.celsius += 0.2 if self.panne or self.vitesse == 0 else -self.vitesse / 25


def piece(installation: Mapping[str, Any], options: Mapping[str, Any]) -> Piece:
    return Piece(installation, options)


def ventilateur(env: Piece) -> Actuator:
    def executer(payload: Mapping[str, Any]) -> dict[str, Any]:
        env.vitesse = payload["speed_percent"]
        return {"status": "accepted", "speed_percent": env.vitesse}

    return Actuator(
        "fan.set",
        "actuator:fan.set",
        "https://schemas.example.org/hypomnesis/fan.set/1.0.0",
        "https://schemas.example.org/hypomnesis/fan.set.result/1.0.0",
        executer,
    )
