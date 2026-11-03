"""Outillage du Kanban (.agentkanban) : vérification, état des dépendances, graphe.

Usage :
    python scripts/kanban.py check            # format et dépendances ; code 1 si invalide
    python scripts/kanban.py status [--json]  # tâches prêtes, bloquées, en cours
    python scripts/kanban.py graph [--wait]   # injecte les tâches dans graphify-out/graph.json

Bibliothèque standard uniquement : les hooks git l'exécutent avec n'importe quel python3.

Une tâche est *prête* si son couloir est `todo` et que toutes ses dépendances sont `done`.
Les dépendances sont lues dans la ligne de métadonnées du premier message
(`**Dépend de** HYP-001, HYP-002`).

Injection dans Graphify : nœuds `HYP-NNN · titre` et relations
  depends_on   tâche → tâche dont elle dépend
  defined_in   tâche → fichier de la tâche
  touches      tâche → fichier ou dossier de « Fichiers concernés »
  references   tâche → document de « Références »
  contains     dossier → fichiers du graphe qu'il contient
Tout ce qui est injecté porte `_origin: "kanban"` et est remplacé à chaque injection
(idempotent). L'écriture se fait sous le verrou de reconstruction de Graphify
(`graphify-out/.rebuild.lock`), et `--wait` attend la fin d'une reconstruction en cours :
c'est le mode utilisé par les hooks git, après la reconstruction lancée par Graphify.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KANBAN = ROOT / ".agentkanban"
TASKS = KANBAN / "tasks"
GRAPH_DIR = ROOT / "graphify-out"
GRAPH = GRAPH_DIR / "graph.json"
LOCK = GRAPH_DIR / ".rebuild.lock"

ORIGIN = "kanban"
ANCHOR = (
    ".agentkanban/board.yaml"  # source_file des éléments injectés : stable entre reconstructions
)
REQUIRED_FIELDS = ("title", "lane", "created", "updated", "description")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
TASK_NAME = re.compile(r"task_\d{8}_hyp(\d{3})_[a-z0-9-]+\.md")
HYP_ID = re.compile(r"HYP-\d{3}")


@dataclass
class Task:
    id: str
    title: str
    lane: str
    path: str
    priority: str = ""
    size: str = ""
    epic: str = ""
    depends_on: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ lecture


def _unquote(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw[1:-1]
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw


def _front_matter(text: str) -> dict[str, str] | None:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip():
            fields[key.strip()] = _unquote(value)
    return fields


def _section_paths(text: str, heading: str) -> list[str]:
    """Chemins entre backticks des puces de la section ``#### heading`` du premier message."""
    match = re.search(rf"^#### {re.escape(heading)}\n(.*?)(?=^#{{2,4}} |\Z)", text, re.S | re.M)
    if not match:
        return []
    paths = []
    for line in match.group(1).splitlines():
        found = re.match(r"\s*-\s*`([^`\s]+)`", line)
        if found:
            paths.append(found.group(1))
    return paths


def _meta(text: str, name: str) -> str:
    match = re.search(rf"\*\*{re.escape(name)}\*\* ([^·\n]+)", text)
    return match.group(1).strip() if match else ""


def lanes() -> list[str]:
    board = (KANBAN / "board.yaml").read_text(encoding="utf-8")
    return re.findall(r"^\s*-\s*([\w-]+)\s*$", board, re.M)


def load(errors: list[str]) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for path in sorted(TASKS.glob("*.md")):
        if path.name.startswith("todo_"):
            continue
        rel = path.relative_to(ROOT).as_posix()
        name_match = TASK_NAME.fullmatch(path.name)
        if not name_match:
            errors.append(f"{rel}: nom attendu task_<AAAAMMJJ>_hypNNN_<slug>.md")
            continue
        text = path.read_text(encoding="utf-8")
        fm = _front_matter(text)
        if fm is None:
            errors.append(f"{rel}: front-matter absent")
            continue
        for key in REQUIRED_FIELDS:
            if not fm.get(key):
                errors.append(f"{rel}: champ `{key}` manquant")
        if "\n## Conversation\n\n### user\n" not in text:
            errors.append(
                f"{rel}: la conversation doit commencer par `## Conversation` puis `### user`"
            )
        task_id = f"HYP-{name_match.group(1)}"
        title_id = HYP_ID.match(fm.get("title", ""))
        if not title_id or title_id.group(0) != task_id:
            errors.append(f"{rel}: le titre doit commencer par {task_id}")
        if _meta(text, "Ticket") and _meta(text, "Ticket") != task_id:
            errors.append(f"{rel}: métadonnée **Ticket** différente de {task_id}")
        if task_id in tasks:
            errors.append(f"{rel}: identifiant {task_id} déjà utilisé par {tasks[task_id].path}")
            continue
        deps = _meta(text, "Dépend de")
        labels = _meta(text, "Labels")
        tasks[task_id] = Task(
            id=task_id,
            title=fm.get("title", ""),
            lane=fm.get("lane", ""),
            path=rel,
            priority=_meta(text, "Priorité"),
            size=_meta(text, "Taille"),
            epic=_meta(text, "Epic"),
            depends_on=HYP_ID.findall(deps),
            labels=[x.strip() for x in labels.split(",") if x.strip()],
            files=_section_paths(text, "Fichiers concernés"),
            references=_section_paths(text, "Références"),
        )
    return tasks


# --------------------------------------------------------------- vérification


def validate(tasks: dict[str, Task], known_lanes: list[str]) -> list[str]:
    errors = []
    for t in tasks.values():
        if t.lane not in known_lanes:
            errors.append(
                f"{t.id}: couloir `{t.lane}` absent de board.yaml ({', '.join(known_lanes)})"
            )
        if t.priority and t.priority not in PRIORITY_ORDER:
            errors.append(f"{t.id}: priorité `{t.priority}` invalide")
        for dep in t.depends_on:
            if dep == t.id:
                errors.append(f"{t.id}: dépend de lui-même")
            elif dep not in tasks:
                errors.append(f"{t.id}: dépendance inconnue {dep}")
            elif t.lane in ("doing", "done") and tasks[dep].lane != "done":
                late = f"sa dépendance {dep} est en `{tasks[dep].lane}`"
                errors.append(f"{t.id}: en `{t.lane}` alors que {late}")
    errors.extend(cycles(tasks))
    return errors


def cycles(tasks: dict[str, Task]) -> list[str]:
    state: dict[str, int] = {}
    found: list[str] = []

    def visit(tid: str, stack: list[str]) -> None:
        if state.get(tid) == 1:
            found.append("cycle de dépendances : " + " → ".join([*stack[stack.index(tid) :], tid]))
            return
        if state.get(tid) == 2 or tid not in tasks:
            return
        state[tid] = 1
        for dep in tasks[tid].depends_on:
            visit(dep, [*stack, tid])
        state[tid] = 2

    for tid in sorted(tasks):
        visit(tid, [])
    return found


def blockers(task: Task, tasks: dict[str, Task]) -> list[str]:
    return [d for d in task.depends_on if d in tasks and tasks[d].lane != "done"]


def is_ready(task: Task, tasks: dict[str, Task]) -> bool:
    return task.lane == "todo" and not blockers(task, tasks)


def unblocks(task_id: str, tasks: dict[str, Task]) -> list[str]:
    return sorted(t.id for t in tasks.values() if task_id in t.depends_on)


# --------------------------------------------------------------------- graphe


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _file_nodes(graph: dict) -> dict[str, str]:
    """source_file -> id du nœud qui représente le fichier lui-même."""
    result = {}
    for node in graph["nodes"]:
        source = node.get("source_file", "")
        if node.get("_origin") != ORIGIN and node.get("label") == os.path.basename(source):
            result.setdefault(source, node["id"])
    return result


def inject(graph: dict, tasks: dict[str, Task]) -> tuple[int, int]:
    """Remplace les éléments `kanban` du graphe ; rend (nœuds, relations) injectés."""
    graph["nodes"] = [n for n in graph["nodes"] if n.get("_origin") != ORIGIN]
    graph["links"] = [e for e in graph["links"] if e.get("_origin") != ORIGIN]
    files = _file_nodes(graph)
    community = max((n.get("community", -1) for n in graph["nodes"]), default=-1) + 1
    community_name = "Kanban : tâches et dépendances"
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    def node(node_id: str, label: str, file_type: str, **extra: object) -> str:
        nodes.setdefault(
            node_id,
            {
                "id": node_id,
                "label": label,
                "norm_label": label.lower(),
                "file_type": file_type,
                "source_file": ANCHOR,
                "source_location": "L1",
                "_origin": ORIGIN,
                "community": community,
                "community_name": community_name,
                **extra,
            },
        )
        return node_id

    def link(source: str, target: str, relation: str) -> None:
        links.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "weight": 1.0,
                "source_file": ANCHOR,
                "source_location": "L1",
                "_origin": ORIGIN,
            }
        )

    def path_target(path: str) -> str:
        """Nœud du graphe pour un chemin cité ; crée un nœud de chemin si Graphify n'en a pas."""
        clean = path.rstrip("/")
        if clean in files:
            return files[clean]
        path_id = node(
            f"kanban_path_{_slug(clean)}",
            path,
            "code" if "." in clean.rsplit("/", 1)[-1] else "document",
        )
        prefix = clean + "/"
        for source, file_id in files.items():
            if source.startswith(prefix):
                link(path_id, file_id, "contains")
        return path_id

    task_ids = {t.id: f"kanban_{_slug(t.id)}" for t in tasks.values()}
    for t in tasks.values():
        node(
            task_ids[t.id],
            t.title,
            "document",
            task_id=t.id,
            task_file=t.path,
            lane=t.lane,
            priority=t.priority,
            epic=t.epic,
            ready=is_ready(t, tasks),
            blocked_by=blockers(t, tasks),
        )
    for t in tasks.values():
        source = task_ids[t.id]
        if t.path in files:
            link(source, files[t.path], "defined_in")
        for dep in t.depends_on:
            if dep in task_ids:
                link(source, task_ids[dep], "depends_on")
        for path in t.files:
            link(source, path_target(path), "touches")
        for path in t.references:
            link(source, path_target(path), "references")

    graph["nodes"].extend(nodes.values())
    graph["links"].extend(links)
    graph.setdefault("graph", {})["kanban"] = {
        "tasks": len(tasks),
        "injected_at_commit": graph.get("built_at_commit", ""),
    }
    return len(nodes), len(links)


def _lock_busy() -> bool:
    if not LOCK.exists():
        return False
    try:
        import fcntl
    except ImportError:  # pragma: no cover - Windows : pas de verrou consultatif
        return False
    with open(LOCK, encoding="utf-8") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    return False


@contextmanager
def graph_lock() -> Iterator[None]:
    """Même protocole que Graphify : flock exclusif, fichier supprimé à la libération."""
    try:
        import fcntl
    except ImportError:  # pragma: no cover
        yield
        return
    GRAPH_DIR.mkdir(exist_ok=True)
    with open(LOCK, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            LOCK.unlink(missing_ok=True)
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def wait_for_rebuild(start_grace: float = 20.0, timeout: float = 900.0) -> None:
    """Laisse à une reconstruction Graphify le temps de démarrer, puis attend sa fin."""
    begin = time.monotonic()
    while time.monotonic() - begin < start_grace and not _lock_busy():
        time.sleep(0.5)
    while _lock_busy() and time.monotonic() - begin < timeout:
        time.sleep(1.0)


def write_graph(tasks: dict[str, Task]) -> str:
    if not GRAPH.exists():
        return "graphify-out/graph.json absent : lancer `graphify update .` d'abord"
    with graph_lock():
        graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        n_nodes, n_links = inject(graph, tasks)
        tmp = GRAPH.with_suffix(".json.kanban-tmp")
        tmp.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, GRAPH)
    return f"graphe enrichi : {n_nodes} nœuds et {n_links} relations du Kanban"


# ---------------------------------------------------------------------- CLI


def _sort_key(t: Task) -> tuple[int, str]:
    return (PRIORITY_ORDER.get(t.priority, 9), t.id)


def status(tasks: dict[str, Task]) -> dict[str, list[dict]]:
    ordered = sorted(tasks.values(), key=_sort_key)
    return {
        "doing": [asdict(t) for t in ordered if t.lane == "doing"],
        "ready": [
            {**asdict(t), "unblocks": unblocks(t.id, tasks)} for t in ordered if is_ready(t, tasks)
        ],
        "blocked": [
            {**asdict(t), "blocked_by": blockers(t, tasks)}
            for t in ordered
            if t.lane == "todo" and blockers(t, tasks)
        ],
        "done": [asdict(t) for t in ordered if t.lane == "done"],
    }


def _print_status(report: dict[str, list[dict]]) -> None:
    def line(t: dict, extra: str = "") -> str:
        human = " [humain]" if "humain" in t["labels"] else ""
        return (
            f"  {t['id']}  {t['priority'] or '--'}  {t['title'].split(' · ', 1)[-1]}{human}{extra}"
        )

    print(f"En cours ({len(report['doing'])})")
    for t in report["doing"]:
        print(line(t))
    print(f"\nPrêtes ({len(report['ready'])})")
    for t in report["ready"]:
        print(line(t, f"  → débloque {', '.join(t['unblocks'])}" if t["unblocks"] else ""))
    print(f"\nBloquées ({len(report['blocked'])})")
    for t in report["blocked"]:
        print(line(t, f"  ← attend {', '.join(t['blocked_by'])}"))
    print(f"\nTerminées : {len(report['done'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="vérifier le format et les dépendances")
    status_parser = sub.add_parser("status", help="tâches prêtes, bloquées, en cours")
    status_parser.add_argument("--json", action="store_true")
    graph_parser = sub.add_parser("graph", help="injecter les tâches dans le graphe Graphify")
    graph_parser.add_argument(
        "--wait", action="store_true", help="attendre la reconstruction Graphify en cours"
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    tasks = load(errors)
    errors += validate(tasks, lanes())
    if errors:
        print("\n".join(errors), file=sys.stderr)
        if args.command == "check":
            return 1
        print(
            "(Kanban invalide : `python scripts/kanban.py check` pour le détail)", file=sys.stderr
        )

    if args.command == "check":
        print(f"{len(tasks)} tâches valides")
    elif args.command == "status":
        report = status(tasks)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            _print_status(report)
    else:
        if args.wait:
            wait_for_rebuild()
        print(write_graph(tasks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
