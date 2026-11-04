"""Outillage du Kanban (.agentkanban) : vérification, état des dépendances, graphe.

Usage :
    python scripts/kanban.py check            # format et dépendances ; code 1 si invalide
    python scripts/kanban.py status [--json]  # tâches prêtes, bloquées, en cours
    python scripts/kanban.py graph [--wait]   # injecte les tâches dans graphify-out/graph.json

Dépendances : PyYAML (front-matter) et NetworkX (graphe des dépendances), donc à lancer avec
l'environnement du projet (`.venv/bin/python`).

Une tâche est *prête* si son couloir est `todo` et que toutes ses dépendances sont terminées,
c'est-à-dire en `qa` (faites, en attente de vérification humaine) ou en `done` (vérifiées).
Seul l'humain fait passer une tâche de `qa` à `done`, et une tâche ne peut être `done` que si
ses dépendances le sont aussi.
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
(`graphify-out/.rebuild.lock`), et `--wait` attend la fin d'une reconstruction en cours.

`status` affiche aussi le *chemin critique* : la plus longue chaîne de dépendances non terminées
menant à une tâche P0 restante.
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

import networkx as nx
import yaml

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
FINISHED = ("qa", "done")  # une dépendance dans ces couloirs ne bloque plus
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


class _FrontMatterLoader(yaml.SafeLoader):
    """SafeLoader that keeps timestamps as written (the extension writes bare ISO dates)."""


_FrontMatterLoader.yaml_implicit_resolvers = {
    char: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for char, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _front_matter(text: str) -> dict[str, str] | None:
    """Champs du front-matter en chaînes ; None si absent, ValueError si ce n'est pas du YAML."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    try:
        data = yaml.load(match.group(1), Loader=_FrontMatterLoader)
    except yaml.YAMLError as exc:
        raise ValueError(str(exc).replace("\n", " ")) from exc
    if not isinstance(data, dict):
        raise ValueError("un dictionnaire clé: valeur est attendu")
    return {str(key): "" if value is None else str(value) for key, value in data.items()}


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
        try:
            fm = _front_matter(text)
        except ValueError as exc:
            errors.append(f"{rel}: front-matter invalide ({exc})")
            continue
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
            elif t.lane == "done" and tasks[dep].lane != "done":
                late = f"sa dépendance {dep} n'est pas vérifiée (`{tasks[dep].lane}`)"
                errors.append(f"{t.id}: en `done` alors que {late}")
            elif t.lane in ("doing", "qa") and tasks[dep].lane not in FINISHED:
                late = f"sa dépendance {dep} est en `{tasks[dep].lane}`"
                errors.append(f"{t.id}: en `{t.lane}` alors que {late}")
    errors.extend(cycles(tasks))
    return errors


def dependency_graph(tasks: dict[str, Task]) -> nx.DiGraph:
    """Graphe orienté tâche → dépendance (les dépendances inconnues sont ignorées)."""
    graph = nx.DiGraph()
    for tid in sorted(tasks):
        graph.add_node(tid, task=tasks[tid])
    for t in tasks.values():
        graph.add_edges_from((t.id, dep) for dep in t.depends_on if dep in tasks)
    return graph


def cycles(tasks: dict[str, Task]) -> list[str]:
    found = []
    for cycle in nx.simple_cycles(dependency_graph(tasks)):
        start = cycle.index(min(cycle))  # canonical rotation: smallest identifier first
        ring = [*cycle[start:], *cycle[:start]]
        found.append("cycle de dépendances : " + " → ".join([*ring, ring[0]]))
    return sorted(found)


def blockers(task: Task, graph: nx.DiGraph) -> list[str]:
    return [d for d in graph.successors(task.id) if graph.nodes[d]["task"].lane not in FINISHED]


def is_ready(task: Task, graph: nx.DiGraph) -> bool:
    return task.lane == "todo" and not blockers(task, graph)


def unblocks(task_id: str, graph: nx.DiGraph) -> list[str]:
    return sorted(graph.predecessors(task_id))


def critical_path(tasks: dict[str, Task]) -> list[str]:
    """Plus longue chaîne de dépendances non terminées vers une tâche P0 restante.

    Rendue dans l'ordre d'exécution (dépendance d'abord, tâche P0 en dernier).
    """
    graph = dependency_graph(tasks)
    open_tasks = graph.subgraph(t for t in tasks if tasks[t].lane not in FINISHED)
    if not nx.is_directed_acyclic_graph(open_tasks):
        return []  # cycles are reported by `check`; no meaningful path
    best: list[str] = []
    for tid in sorted(t for t in open_tasks if tasks[t].priority == "P0"):
        reach = open_tasks.subgraph({tid, *nx.descendants(open_tasks, tid)})
        path = nx.dag_longest_path(reach)  # tid is the only source, so the path starts there
        if len(path) > len(best):
            best = path
    return best[::-1]


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
            f"Chemin Kanban : {path}",
            "document",
            referenced_path=path,
        )
        prefix = clean + "/"
        for source, file_id in files.items():
            if source.startswith(prefix):
                link(path_id, file_id, "contains")
        return path_id

    deps = dependency_graph(tasks)
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
            ready=is_ready(t, deps),
            blocked_by=blockers(t, deps),
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
    graph = dependency_graph(tasks)
    ordered = sorted(tasks.values(), key=_sort_key)
    return {
        "doing": [asdict(t) for t in ordered if t.lane == "doing"],
        "ready": [
            {**asdict(t), "unblocks": unblocks(t.id, graph)} for t in ordered if is_ready(t, graph)
        ],
        "blocked": [
            {**asdict(t), "blocked_by": blockers(t, graph)}
            for t in ordered
            if t.lane == "todo" and blockers(t, graph)
        ],
        "qa": [asdict(t) for t in ordered if t.lane == "qa"],
        "done": [asdict(t) for t in ordered if t.lane == "done"],
        "critical_path": [
            {
                "id": tid,
                "priority": tasks[tid].priority,
                "title": tasks[tid].title,
                "labels": tasks[tid].labels,
            }
            for tid in critical_path(tasks)
        ],
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
    print(f"\nÀ vérifier — QA ({len(report['qa'])})")
    for t in report["qa"]:
        print(line(t))
    print(f"\nTerminées et vérifiées : {len(report['done'])}")
    path = report["critical_path"]
    if path:
        print(f"\nChemin critique vers P0 ({len(path)})")
        for t in path:
            print(line(t))
    else:
        print("\nChemin critique vers P0 : aucune tâche P0 restante")


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
