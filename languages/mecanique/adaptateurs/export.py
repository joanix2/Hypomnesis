"""Adaptateur d'effet du langage « mécanique » : écrit la géométrie d'une pièce.

Seule la frontière avec le monde extérieur (le système de fichiers) est en
Python. Le contenu de la commande est construit en Hypomnesis
(`Plaque.commande_export`) et validé par le contrat avant d'arriver ici.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from hypomnesis.effects.dispatcher import Actuator

COMMAND = "https://schemas.example.org/hypomnesis/geometry.export/1.0.0"
RESULT = "https://schemas.example.org/hypomnesis/geometry.export.result/1.0.0"


def actionneur(out_dir: Path) -> Actuator:
    out_dir = out_dir.resolve()

    def contraintes(payload: Mapping[str, Any]) -> list[str]:
        target = (out_dir / payload["path"]).resolve()
        problems = []
        if out_dir not in target.parents:
            problems.append("chemin hors du répertoire de sortie")
        if not payload["path"].endswith("." + payload["format"]):
            problems.append("extension différente du format")
        return problems

    def executer(payload: Mapping[str, Any]) -> dict[str, Any]:
        part = payload["part"]
        path = out_dir / payload["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if payload["format"] == "json":
            text = json.dumps(part, indent=2, ensure_ascii=False)
        else:
            w, h = part["width_mm"], part["height_mm"]
            text = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 20}mm" height="{h + 20}mm" '
                f'viewBox="-10 -10 {w + 20} {h + 20}">\n'
                f'  <rect x="0" y="0" width="{w}" height="{h}" fill="none" stroke="black"/>\n'
                f'  <text x="{w / 2}" y="{h / 2}" text-anchor="middle" font-size="6">'
                f"{part['name']} {w}×{h}×{part['thickness_mm']} mm</text>\n</svg>\n"
            )
        path.write_text(text, encoding="utf-8")
        return {"status": "written", "path": str(path), "bytes": len(text.encode())}

    return Actuator(
        id="geometry.export",
        permission="actuator:geometry.export",
        command_schema=COMMAND,
        result_schema=RESULT,
        execute=executer,
        constraints=contraintes,
        simulate=lambda p: {"status": "simulated", "path": p["path"]},
    )
