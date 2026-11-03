"""Tests de scripts/kanban.py sur un Kanban et un graphe factices."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "kanban.py"
_spec = importlib.util.spec_from_file_location("kanban", SCRIPT)
assert _spec and _spec.loader
kanban = importlib.util.module_from_spec(_spec)
sys.modules["kanban"] = kanban  # requis par dataclasses avant l'exécution du module
_spec.loader.exec_module(kanban)


def task(
    num: str, lane: str = "todo", deps: str = "aucune", files: str = "", title: str = ""
) -> str:
    files_section = f"#### Fichiers concernés\n\n{files}\n\n" if files else ""
    return (
        "---\n"
        f'title: "HYP-{num} · {title or "Tâche " + num}"\n'
        f"lane: {lane}\n"
        "created: 2026-11-03T00:00:00+01:00\n"
        "updated: 2026-11-03T00:00:00+01:00\n"
        'description: "x"\n'
        "---\n\n## Conversation\n\n### user\n\n"
        f"**Ticket** HYP-{num} · **Priorité** P1 · **Taille** S · **Epic** Test"
        f" · **Dépend de** {deps}\n\n"
        f"#### Contexte\n\nTexte.\n\n{files_section}"
    )


@pytest.fixture
def board(tmp_path, monkeypatch):
    root = tmp_path
    tasks_dir = root / ".agentkanban" / "tasks"
    tasks_dir.mkdir(parents=True)
    (root / ".agentkanban" / "board.yaml").write_text(
        "lanes:\n  - todo\n  - doing\n  - qa\n  - done\n"
    )
    monkeypatch.setattr(kanban, "ROOT", root)
    monkeypatch.setattr(kanban, "KANBAN", root / ".agentkanban")
    monkeypatch.setattr(kanban, "TASKS", tasks_dir)
    monkeypatch.setattr(kanban, "GRAPH_DIR", root / "graphify-out")
    monkeypatch.setattr(kanban, "GRAPH", root / "graphify-out" / "graph.json")
    monkeypatch.setattr(kanban, "LOCK", root / "graphify-out" / ".rebuild.lock")

    def add(num: str, slug: str = "t", **kwargs) -> None:
        (tasks_dir / f"task_20261103_hyp{num}_{slug}.md").write_text(
            task(num, **kwargs), encoding="utf-8"
        )

    return add


def errors_of() -> list[str]:
    errors: list[str] = []
    tasks = kanban.load(errors)
    return errors + kanban.validate(tasks, kanban.lanes())


def test_valid_board_and_readiness(board):
    board("001", lane="done")
    board("002", deps="HYP-001")
    board("003", deps="HYP-001, HYP-002")
    assert errors_of() == []
    tasks = kanban.load([])
    report = kanban.status(tasks)
    assert [t["id"] for t in report["ready"]] == ["HYP-002"]
    assert report["ready"][0]["unblocks"] == ["HYP-003"]
    assert report["blocked"][0]["blocked_by"] == ["HYP-002"]


def test_unknown_dependency_and_self_dependency(board):
    board("001", deps="HYP-404")
    board("002", deps="HYP-002")
    errors = errors_of()
    assert any("dépendance inconnue HYP-404" in e for e in errors)
    assert any("dépend de lui-même" in e for e in errors)


def test_cycle_is_reported(board):
    board("001", deps="HYP-003")
    board("002", deps="HYP-001")
    board("003", deps="HYP-002")
    assert any(e.startswith("cycle de dépendances") for e in errors_of())


def test_qa_dependencies_unblock_but_done_requires_verified_dependencies(board):
    board("001", lane="qa")
    board("002", deps="HYP-001")
    board("003", lane="qa", deps="HYP-001")
    assert errors_of() == []
    tasks = kanban.load([])
    report = kanban.status(tasks)
    assert [t["id"] for t in report["ready"]] == ["HYP-002"]
    assert [t["id"] for t in report["qa"]] == ["HYP-001", "HYP-003"]
    board("004", lane="done", deps="HYP-001")
    assert any("HYP-004: en `done`" in e and "pas vérifiée" in e for e in errors_of())


def test_started_before_dependencies(board):
    board("001")
    board("002", lane="doing", deps="HYP-001")
    assert any("HYP-002: en `doing`" in e for e in errors_of())


def test_format_errors(board, tmp_path):
    board("001", lane="nowhere")
    (kanban.TASKS / "task_bad-name.md").write_text("x")
    (kanban.TASKS / "task_20261103_hyp002_x.md").write_text(task("009"))
    errors = errors_of()
    assert any("couloir `nowhere`" in e for e in errors)
    assert any("nom attendu" in e for e in errors)
    assert any("doit commencer par HYP-002" in e for e in errors)


def test_check_command_exit_codes(board, capsys):
    board("001")
    assert kanban.main(["check"]) == 0
    board("002", deps="HYP-999")
    assert kanban.main(["check"]) == 1


def _graph() -> dict:
    return {
        "directed": False,
        "multigraph": False,
        "graph": {},
        "built_at_commit": "abc",
        "nodes": [
            {"id": "src_core", "label": "core.py", "source_file": "src/ir/core.py", "community": 3},
            {
                "id": "src_infer",
                "label": "infer.py",
                "source_file": "src/ts/infer.py",
                "community": 3,
            },
            {
                "id": "src_infer_fn",
                "label": "infer()",
                "source_file": "src/ts/infer.py",
                "community": 3,
            },
        ],
        "links": [{"source": "src_infer", "target": "src_infer_fn", "relation": "contains"}],
    }


def test_injection_links_tasks_dependencies_and_files(board):
    board("001", lane="done", files="- `src/ir/core.py`")
    board("002", deps="HYP-001", files="- `src/ts/`\n- `formal/Core.lean`")
    graph = _graph()
    kanban.inject(graph, kanban.load([]))
    ids = {n["id"]: n for n in graph["nodes"]}
    rel = {(e["source"], e["relation"], e["target"]) for e in graph["links"]}
    assert ids["kanban_hyp_002"]["ready"] is True
    assert ("kanban_hyp_002", "depends_on", "kanban_hyp_001") in rel
    assert ("kanban_hyp_001", "touches", "src_core") in rel
    assert ("kanban_hyp_002", "touches", "kanban_path_src_ts") in rel
    assert ("kanban_path_src_ts", "contains", "src_infer") in rel  # le nœud-fichier, pas le symbole
    assert ("kanban_path_src_ts", "contains", "src_infer_fn") not in rel
    assert ("kanban_hyp_002", "touches", "kanban_path_formal_core_lean") in rel


def test_injection_is_idempotent_and_preserves_graphify_content(board):
    board("001", files="- `src/ir/core.py`")
    graph = _graph()
    kanban.inject(graph, kanban.load([]))
    first = json.dumps(graph, sort_keys=True)
    kanban.inject(graph, kanban.load([]))
    assert json.dumps(graph, sort_keys=True) == first
    assert {"source": "src_infer", "target": "src_infer_fn", "relation": "contains"} in graph[
        "links"
    ]


def test_write_graph_uses_and_releases_lock(board):
    board("001")
    kanban.GRAPH_DIR.mkdir()
    kanban.GRAPH.write_text(json.dumps(_graph()))
    message = kanban.write_graph(kanban.load([]))
    assert "1 nœuds" in message
    assert not kanban.LOCK.exists()
    assert any(n.get("_origin") == "kanban" for n in json.loads(kanban.GRAPH.read_text())["nodes"])
