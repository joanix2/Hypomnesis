"""Génère kanban/BOARD.md à partir des tickets et vérifie leur cohérence.

Usage :
    python kanban/board.py          # régénère BOARD.md
    python kanban/board.py --check  # échoue si un ticket est invalide ou BOARD.md périmé

Un ticket est « prêt » s'il est au statut backlog et que toutes ses
dépendances sont done. La colonne Prêt n'est donc jamais saisie à la main.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TICKETS = ROOT / "tickets"
BOARD = ROOT / "BOARD.md"

STATUSES = ("backlog", "in-progress", "review", "done")
PRIORITIES = ("P0", "P1", "P2", "P3")
SIZES = ("S", "M", "L")
EPICS = {
    "FONDATIONS": "Fondations et gouvernance",
    "LANG": "Langage",
    "FORMEL": "Vérification formelle (Lean)",
    "P2-EPISTEMIQUE": "Phase 2 — Moteur épistémique",
    "P3-EXTENSIONS": "Phase 3 — Extensions et contrats",
    "P4-RAISONNEMENT": "Phase 4 — Raisonnement hybride",
    "P5-EFFETS": "Phase 5 — Effets et actionneurs",
    "P6-OBSERVABILITE": "Phase 6 — Observabilité",
    "P7-LLM": "Phase 7 — Intégration LLM",
    "P8-STABILISATION": "Phase 8 — Stabilisation",
    "M3": "Niveau M3 (méta-métamodèle)",
}
COLUMNS = (
    ("in-progress", "En cours"),
    ("review", "En revue"),
    ("ready", "Prêt (dépendances satisfaites)"),
    ("blocked", "Bloqué (dépendances en attente)"),
    ("done", "Terminé"),
)


@dataclass
class Ticket:
    id: str
    title: str
    status: str
    priority: str
    size: str
    epic: str
    path: Path
    depends_on: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    assignee: str = ""

    @property
    def number(self) -> int:
        return int(self.id.split("-")[1])


def _parse_value(raw: str) -> str | list[str]:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [item.strip() for item in raw[1:-1].split(",") if item.strip()]
    return raw.strip('"')


def parse(path: Path) -> Ticket:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError(f"{path.name}: front-matter manquant")
    meta: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        if line.strip():
            key, _, value = line.partition(":")
            meta[key.strip()] = _parse_value(value)
    try:
        return Ticket(
            id=str(meta["id"]),
            title=str(meta["title"]),
            status=str(meta["status"]),
            priority=str(meta["priority"]),
            size=str(meta["size"]),
            epic=str(meta["epic"]),
            path=path,
            depends_on=list(meta.get("depends_on", [])),
            labels=list(meta.get("labels", [])),
            assignee=str(meta.get("assignee", "")),
        )
    except KeyError as exc:
        raise ValueError(f"{path.name}: champ {exc} manquant") from None


def validate(tickets: dict[str, Ticket]) -> list[str]:
    errors = []
    for t in tickets.values():
        if not re.fullmatch(r"HYP-\d{3}", t.id):
            errors.append(f"{t.id}: identifiant invalide")
        if not t.path.name.startswith(t.id + "-"):
            errors.append(f"{t.id}: le nom de fichier doit commencer par l'identifiant")
        if t.status not in STATUSES:
            errors.append(f"{t.id}: statut {t.status!r} invalide ({', '.join(STATUSES)})")
        if t.priority not in PRIORITIES:
            errors.append(f"{t.id}: priorité {t.priority!r} invalide")
        if t.size not in SIZES:
            errors.append(f"{t.id}: taille {t.size!r} invalide")
        if t.epic not in EPICS:
            errors.append(f"{t.id}: epic {t.epic!r} inconnue")
        if t.status == "in-progress" and not t.assignee:
            errors.append(f"{t.id}: un ticket en cours doit avoir un assignee")
        for dep in t.depends_on:
            if dep not in tickets:
                errors.append(f"{t.id}: dépendance inconnue {dep}")
            elif t.status != "backlog" and tickets[dep].status != "done":
                errors.append(f"{t.id}: démarré alors que {dep} n'est pas done")
    errors.extend(_cycles(tickets))
    return errors


def _cycles(tickets: dict[str, Ticket]) -> list[str]:
    state: dict[str, int] = {}
    errors: list[str] = []

    def visit(tid: str, stack: list[str]) -> None:
        if state.get(tid) == 1:
            errors.append("cycle de dépendances : " + " → ".join([*stack, tid]))
            return
        if state.get(tid) == 2 or tid not in tickets:
            return
        state[tid] = 1
        for dep in tickets[tid].depends_on:
            visit(dep, [*stack, tid])
        state[tid] = 2

    for tid in sorted(tickets):
        visit(tid, [])
    return errors


def column(t: Ticket, tickets: dict[str, Ticket]) -> str:
    if t.status != "backlog":
        return t.status
    deps_done = all(tickets[d].status == "done" for d in t.depends_on if d in tickets)
    return "ready" if deps_done else "blocked"


def render(tickets: dict[str, Ticket]) -> str:
    ordered = sorted(tickets.values(), key=lambda t: (t.priority, t.number))
    lines = [
        "# Tableau Kanban — Hypomnesis",
        "",
        "> Fichier généré par `python kanban/board.py` : ne pas éditer à la main.",
        "> Conventions et protocole agent : [README.md](README.md).",
        "",
    ]
    counts = {key: 0 for key, _ in COLUMNS}
    for t in ordered:
        counts[column(t, tickets)] += 1
    lines.append(" · ".join(f"**{label}** : {counts[key]}" for key, label in COLUMNS))
    lines.append("")
    for key, label in COLUMNS:
        selected = [t for t in ordered if column(t, tickets) == key]
        lines += [f"## {label}", ""]
        if not selected:
            lines += ["_Aucun ticket._", ""]
            continue
        lines += [
            "| Ticket | Titre | Prio | Taille | Epic | Dépend de | Labels |",
            "|---|---|---|---|---|---|---|",
        ]
        for t in selected:
            deps = ", ".join(
                d if tickets.get(d) and tickets[d].status == "done" else f"**{d}**"
                for d in t.depends_on
            )
            title = t.title + (f" — _{t.assignee}_" if t.assignee else "")
            link = f"[{t.id}](tickets/{t.path.name})"
            labels = ", ".join(t.labels) or "—"
            cells = [link, title, t.priority, t.size, t.epic, deps or "—", labels]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Par epic", "", "| Epic | Terminés | Total |", "|---|---|---|"]
    for epic, name in EPICS.items():
        members = [t for t in ordered if t.epic == epic]
        if members:
            done = sum(t.status == "done" for t in members)
            lines.append(f"| {name} | {done} | {len(members)} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    tickets: dict[str, Ticket] = {}
    errors: list[str] = []
    for path in sorted(TICKETS.glob("HYP-*.md")):
        try:
            t = parse(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if t.id in tickets:
            errors.append(f"{t.id}: identifiant dupliqué")
        tickets[t.id] = t
    errors += validate(tickets)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    content = render(tickets)
    if "--check" in argv:
        if not BOARD.exists() or BOARD.read_text(encoding="utf-8") != content:
            print("BOARD.md est périmé : lancer python kanban/board.py", file=sys.stderr)
            return 1
        return 0
    BOARD.write_text(content, encoding="utf-8")
    print(f"{len(tickets)} tickets → {BOARD.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
