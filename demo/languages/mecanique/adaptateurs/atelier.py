"""Environnement du langage « mécanique » : l'atelier (répertoire de sortie et
pied à coulisse simulé). Option `mesure` : l'épaisseur que lira l'instrument (mm)."""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

READING = "https://schemas.example.org/hypomnesis/thickness.reading/1.0.0"


class Atelier:
    def __init__(self, options: Mapping[str, Any], out_dir: Path) -> None:
        self.out_dir = out_dir
        self.mesure = float(options.get("mesure", 5.0))
        self._ids = itertools.count(1)

    def message(self, capteur: str) -> dict[str, Any]:
        return {
            "message_id": f"msg-{next(self._ids)}",
            "schema_id": READING,
            "schema_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "payload": {"sensor_id": capteur, "thickness_mm": self.mesure},
        }


def atelier(options: Mapping[str, Any], out_dir: Path) -> Atelier:
    return Atelier(options, out_dir)
