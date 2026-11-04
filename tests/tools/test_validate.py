"""Verify graph migration ordering and failure propagation without running Graphify."""

import os
import subprocess
from pathlib import Path

import pytest

VALIDATE = Path(__file__).resolve().parents[2] / "scripts" / "validate.sh"


@pytest.mark.parametrize(
    ("existing", "failure", "expected_calls"),
    [
        (False, False, ["update .", "scripts/kanban.py graph"]),
        (True, False, ["scripts/kanban.py graph", "update .", "scripts/kanban.py graph"]),
        (True, True, ["scripts/kanban.py graph"]),
    ],
)
def test_graph_refresh_migrates_before_rebuild(tmp_path, existing, failure, expected_calls):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    if existing:
        graph = tmp_path / "graphify-out" / "graph.json"
        graph.parent.mkdir()
        graph.write_text("{}\n", encoding="utf-8")
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    for name in ("python", "graphify"):
        command = bin_dir / name
        command.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\n'
            + ('exit "$FAILURE"\n' if name == "python" else "exit 0\n"),
            encoding="utf-8",
        )
        command.chmod(0o755)
    calls = tmp_path / "calls.txt"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CALLS": str(calls),
        "FAILURE": "1" if failure else "0",
    }
    result = subprocess.run(
        ["bash", str(VALIDATE), "graphe"], cwd=tmp_path, env=env, capture_output=True, text=True
    )
    assert result.returncode == (1 if failure else 0), result.stdout + result.stderr
    assert calls.read_text(encoding="utf-8").splitlines() == expected_calls
