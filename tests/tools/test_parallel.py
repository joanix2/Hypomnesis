import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
for name in ("kanban", "parallel"):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
parallel = sys.modules["parallel"]


def git(root, *args):
    return parallel.git(root, *args).stdout.strip()


def commit(root, path, text):
    (root / path).write_text(text)
    git(root, "add", path)
    git(root, "commit", "-m", "test change")


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    tasks = root / ".agentkanban/tasks"
    tasks.mkdir(parents=True)
    (tasks.parent / "board.yaml").write_text("lanes:\n  - todo\n  - doing\n  - qa\n  - done\n")
    for num, scope in (("001", "a.txt"), ("002", "b.txt"), ("003", "a.txt")):
        (tasks / f"task_20261104_hyp{num}_test.md").write_text(
            f'---\ntitle: "HYP-{num} · Test"\nlane: todo\ncreated: x\nupdated: x\n'
            "description: x\n---\n\n## Conversation\n\n### user\n\n"
            f"**Ticket** HYP-{num} · **Priorité** P0 · **Labels** python\n\n"
            f"#### Fichiers concernés\n\n- `{scope}`\n"
        )
    (root / "a.txt").write_text("base\n")
    (root / "b.txt").write_text("base\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root


def prepare(repo, ids=("HYP-001",), **kwargs):
    return parallel.prepare(repo, list(ids), repo.parent / "workers", **kwargs)


def worker(repo, identifier):
    return Path(parallel.read_state(repo)["jobs"][identifier]["worktree"])


def valid_command():
    return [sys.executable, "-c", "print('validated')"]


def test_plan_and_status_are_readonly(repo):
    assert not parallel.directory(repo).exists()
    result = parallel.selection(repo, [])
    assert [j["id"] for j in result["selected"]] == ["HYP-001", "HYP-002"]
    assert result["excluded"] == [{"id": "HYP-003", "reason": "overlapping footprint"}]
    assert parallel.status(repo) == {"version": 1, "jobs": {}}
    assert not parallel.directory(repo).exists()
    assert not git(repo, "status", "--porcelain")


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("src/", "src/model.py"),
        ("src/a*.py", "src/abc.py"),
        ("src/*/a.py", "src/model/b.py"),
        ("*.py", "any/file.py"),
    ],
)
def test_conservative_conflicts(a, b):
    assert parallel.overlap(a, b)


def test_prepare_record_integrate(repo):
    state = prepare(repo, ("HYP-001", "HYP-002"))
    assert set(state["jobs"]) == {"HYP-001", "HYP-002"}
    for identifier, path in (("HYP-001", "a.txt"), ("HYP-002", "b.txt")):
        commit(worker(repo, identifier), path, "worker\n")
        parallel.record(repo, identifier, valid_command())
    state = parallel.integrate(repo, ["HYP-001", "HYP-002"])
    integration = Path(state["integration"]["path"])
    assert (integration / "a.txt").read_text() == "worker\n"
    assert (integration / "b.txt").read_text() == "worker\n"
    assert all(j["status"] == "integrated" for j in state["jobs"].values())
    assert (repo / "a.txt").read_text() == "base\n"
    assert git(integration, "rev-list", "--count", "--merges", "HEAD") == "2"


def test_reject_dirty_existing_duplicate_and_lock(repo):
    (repo / "dirty").touch()
    with pytest.raises(parallel.ParallelError, match="dirty"):
        prepare(repo)
    (repo / "dirty").unlink()
    with parallel.locked(repo), pytest.raises(parallel.ParallelError, match="lock"):
        prepare(repo)
    prepare(repo)
    with pytest.raises(parallel.ParallelError, match="assigned"):
        prepare(repo)
    with pytest.raises(parallel.ParallelError, match="duplicate"):
        parallel.selection(repo, ["HYP-002", "HYP-002"])


def test_resume_interrupted_preparation(repo, monkeypatch):
    original = parallel.ensure_worktree
    count = 0

    def interrupt(*args):
        nonlocal count
        count += 1
        if count == 3:
            raise parallel.ParallelError("interrupted")
        return original(*args)

    monkeypatch.setattr(parallel, "ensure_worktree", interrupt)
    with pytest.raises(parallel.ParallelError, match="interrupted"):
        prepare(repo, ("HYP-001", "HYP-002"))
    monkeypatch.setattr(parallel, "ensure_worktree", original)
    state = prepare(repo, ("HYP-001", "HYP-002"), resume=True)
    assert all(j["status"] == "prepared" for j in state["jobs"].values())


def test_stale_validation_and_outside_scope(repo):
    prepare(repo)
    path = worker(repo, "HYP-001")
    commit(path, "a.txt", "first\n")
    parallel.record(repo, "HYP-001", valid_command())
    commit(path, "a.txt", "second\n")
    before = (parallel.directory(repo) / "state.json").read_bytes()
    assert parallel.status(repo)["jobs"]["HYP-001"]["status"] == "stale"
    assert (parallel.directory(repo) / "state.json").read_bytes() == before
    with pytest.raises(parallel.ParallelError, match="stale"):
        parallel.integrate(repo, ["HYP-001"])
    commit(path, "b.txt", "outside\n")
    with pytest.raises(parallel.ParallelError, match="out-of-scope"):
        parallel.record(repo, "HYP-001", valid_command())


def test_validation_failure_preserved(repo):
    prepare(repo)
    commit(worker(repo, "HYP-001"), "a.txt", "worker\n")
    with pytest.raises(parallel.ParallelError, match="validation failed"):
        parallel.record(repo, "HYP-001", [sys.executable, "-c", "raise SystemExit(4)"])
    assert parallel.read_state(repo)["jobs"]["HYP-001"]["validation"]["returncode"] == 4
    with pytest.raises(parallel.ParallelError, match="missing"):
        parallel.integrate(repo, ["HYP-001"])


def test_conflicting_merge_stops(repo):
    prepare(repo)
    commit(worker(repo, "HYP-001"), "a.txt", "first\n")
    parallel.record(repo, "HYP-001", valid_command())
    parallel.integrate(repo, ["HYP-001"])
    prepare(repo, ("HYP-003",))
    commit(worker(repo, "HYP-003"), "a.txt", "conflict\n")
    parallel.record(repo, "HYP-003", valid_command())
    with pytest.raises(parallel.ParallelError, match="merge stopped"):
        parallel.integrate(repo, ["HYP-003"])
    state = parallel.read_state(repo)
    assert state["jobs"]["HYP-003"]["status"] == "conflict"
    assert git(Path(state["integration"]["path"]), "diff", "--name-only", "--diff-filter=U")


def test_merged_validation_can_fail_without_committing(repo):
    prepare(repo, ("HYP-001", "HYP-002"))
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; import sys; "
        "sys.exit(9 if Path('a.txt').read_text() == Path('b.txt').read_text() == 'worker' else 0)",
    ]
    for identifier, path in (("HYP-001", "a.txt"), ("HYP-002", "b.txt")):
        commit(worker(repo, identifier), path, "worker")
        parallel.record(repo, identifier, command)
    parallel.integrate(repo, ["HYP-001"])
    with pytest.raises(parallel.ParallelError, match="integration validation failed"):
        parallel.integrate(repo, ["HYP-002"])
    state = parallel.read_state(repo)
    assert state["jobs"]["HYP-002"]["status"] == "integration-failed"
    assert git(Path(state["integration"]["path"]), "rev-list", "--count", "--merges", "HEAD") == "1"


def test_cli_json_and_invalid_ref(repo):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "parallel.py"), "--repo", str(repo), "--json", "plan"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert len(json.loads(result.stdout)["selected"]) == 2
    with pytest.raises(parallel.ParallelError):
        prepare(repo, base="does-not-exist")
    with pytest.raises(parallel.ParallelError, match="positive"):
        parallel.selection(repo, [], limit=0)


def test_unknown_human_and_dependency_filters(repo):
    task = repo / ".agentkanban/tasks/task_20261104_hyp001_test.md"
    commit(
        repo,
        str(task.relative_to(repo)),
        task.read_text().replace("**Labels** python", "**Labels** humain"),
    )
    task = repo / ".agentkanban/tasks/task_20261104_hyp002_test.md"
    commit(
        repo,
        str(task.relative_to(repo)),
        task.read_text().replace("**Labels** python", "**Dépend de** HYP-001 · **Labels** python"),
    )
    task = repo / ".agentkanban/tasks/task_20261104_hyp003_test.md"
    commit(repo, str(task.relative_to(repo)), task.read_text().replace("- `a.txt`", ""))
    result = parallel.selection(repo, [])
    assert not result["selected"]
    assert {j["reason"] for j in result["excluded"]} == {
        "human decision required",
        "not ready",
        "unknown footprint",
    }


def test_existing_destination_and_parallel_limit(repo):
    parent = repo.parent / "workers"
    (parent / "hyp-001").mkdir(parents=True)
    with pytest.raises(parallel.ParallelError, match="already exists"):
        prepare(repo)
    assert parallel.read_state(repo)["jobs"]["HYP-001"]["status"] == "preparing"
    with pytest.raises(parallel.ParallelError, match="limit"):
        prepare(repo, ("HYP-002",), limit=1)


def test_worker_validator_modification_is_not_attested(repo):
    prepare(repo)
    commit(worker(repo, "HYP-001"), "a.txt", "worker\n")
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('a.txt').write_text('changed')",
    ]
    with pytest.raises(parallel.ParallelError, match="modified"):
        parallel.record(repo, "HYP-001", command)
    assert parallel.read_state(repo)["jobs"]["HYP-001"]["status"] == "failed"


def test_integration_validator_cannot_stage_mutations(repo):
    prepare(repo)
    path = worker(repo, "HYP-001")
    commit(path, "a.txt", "worker\n")
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; import subprocess; "
        "integration = Path.cwd().name == 'integration'; "
        "Path('a.txt').write_text('modified') if integration else None; "
        "subprocess.run(['git','add','a.txt'],check=True) if integration else None",
    ]
    parallel.record(repo, "HYP-001", command)
    with pytest.raises(parallel.ParallelError, match="modified"):
        parallel.integrate(repo, ["HYP-001"])
    state = parallel.status(repo)
    assert state["jobs"]["HYP-001"]["status"] == "integration-failed"
    assert state["integration"]["needs_reconciliation"]


def test_dependency_qa_in_worker_does_not_unlock_successor(repo):
    prepare(repo)
    task = repo / ".agentkanban/tasks/task_20261104_hyp001_test.md"
    commit(repo, str(task.relative_to(repo)), task.read_text().replace("lane: todo", "lane: qa"))
    task = repo / ".agentkanban/tasks/task_20261104_hyp002_test.md"
    commit(
        repo,
        str(task.relative_to(repo)),
        task.read_text().replace("**Labels** python", "**Dépend de** HYP-001 · **Labels** python"),
    )
    result = parallel.selection(repo, ["HYP-002"])
    assert result["excluded"] == [{"id": "HYP-002", "reason": "dependency not integrated in base"}]
