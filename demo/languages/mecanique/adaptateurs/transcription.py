"""Transcription langage naturel → programme M1 du langage « mécanique ».

Tient la place d'un LLM (HYP-081) : un ensemble de règles déterministes qui
produit un programme Hypomnesis. C'est le vérificateur de types du moteur, pas
ce transcripteur, qui décide si le programme est acceptable (§14.3).
"""

from __future__ import annotations

import re

NOMBRE = r"(\d+(?:[.,]\d+)?)"


def _nombre(texte: str) -> float:
    return float(texte.replace(",", "."))


def transcrire(demande: str) -> str:
    dims = re.search(NOMBRE + r"\s*[x×*]\s*" + NOMBRE + r"\s*mm", demande)
    if not dims:
        raise ValueError("dimensions « L × H mm » introuvables dans la demande")
    largeur, hauteur = (_nombre(g) for g in dims.groups())
    epaisseur = re.search(r"épaisseur (?:de )?" + NOMBRE + r"\s*mm", demande)
    masse = re.search(NOMBRE + r"\s*kg", demande)
    nom = re.search(r"nommée? (\w[\w-]*)", demande)
    return (
        "let demande = {\n"
        f"  Plaque.nom = {(nom.group(1) if nom else 'plaque')!r};\n"
        f"  largeur = {largeur!r};\n"
        f"  hauteur = {hauteur!r};\n"
        f"  epaisseur = {f'Some {_nombre(epaisseur.group(1))!r}' if epaisseur else 'None'};\n"
        f"  masse_max = {(_nombre(masse.group(1)) if masse else 0.5)!r};\n"
        "}\n\n"
        "let procedure = Plaque.concevoir demande Plaque.estimateur_regle\n"
    ).replace("'", '"')
