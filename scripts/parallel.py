"""Local Kanban worktree coordinator; it never launches agents or pushes."""

from __future__ import annotations

import argparse
import fcntl
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import kanban

DEFAULT_COMMAND = ["./scripts/validate.sh", "complet"]
RESERVED = (
    ".agentkanban/",
    "TECHNICAL.md",
    "pyproject.toml",
    ".github/",
    "src/hypomnesis/session.py",
    "src/hypomnesis/runtime/natives.py",
    "docs/language/reference.md",
)


class ParallelError(ValueError):
    pass


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args], text=True, capture_output=True, check=False
    )
    if check and result.returncode:
        raise ParallelError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result


def head(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").stdout.strip()


def clean(root: Path) -> None:
    if git(root, "status", "--porcelain").stdout:
        raise ParallelError(f"dirty worktree: {root}")


def directory(root: Path) -> Path:
    return (
        Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
        / "parallel"
    )


def read_state(root: Path) -> dict[str, Any]:
    path = directory(root) / "state.json"
    if not path.exists():
        return {"version": 1, "jobs": {}}
    state = json.loads(path.read_text())
    if (
        not isinstance(state, dict)
        or state.get("version") != 1
        or not isinstance(state.get("jobs"), dict)
    ):
        raise ParallelError("unsupported or malformed parallel state")
    return state


def save(root: Path, state: dict[str, Any]) -> None:
    folder = directory(root)
    temporary = folder / "state.tmp"
    with temporary.open("w") as stream:
        json.dump(state, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(folder / "state.json")


@contextmanager
def locked(root: Path):
    folder = directory(root)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ParallelError("another coordinator holds the parallel lock") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def tasks(root: Path) -> dict[str, kanban.Task]:
    previous = kanban.ROOT, kanban.KANBAN, kanban.TASKS
    kanban.ROOT, kanban.KANBAN, kanban.TASKS = (
        root,
        root / ".agentkanban",
        root / ".agentkanban/tasks",
    )
    try:
        errors: list[str] = []
        found = kanban.load(errors)
        errors += kanban.validate(found, kanban.lanes())
        if errors:
            raise ParallelError("\n".join(errors))
        return found
    finally:
        kanban.ROOT, kanban.KANBAN, kanban.TASKS = previous


def footprint(paths: list[str]) -> list[str]:
    normalized = []
    for path in paths:
        if not path or path.startswith("/") or ".." in Path(path).parts:
            raise ParallelError(f"invalid scope: {path!r}")
        normalized.append(path.removeprefix("./"))
    return sorted(set(normalized))


def prefix(pattern: str) -> str:
    fixed = re.split(r"[*?\[]", pattern, maxsplit=1)[0]
    if fixed != pattern and not fixed.endswith("/"):
        fixed = fixed.rsplit("/", 1)[0] if "/" in fixed else ""
    return fixed.rstrip("/")


def overlap(left: str, right: str) -> bool:
    a, b = prefix(left), prefix(right)
    return not a or not b or a == b or a.startswith(b + "/") or b.startswith(a + "/")


def covered(path: str, scopes: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, scope) or path.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def board_at_head(root: Path, base: str) -> None:
    if base != head(root):
        raise ParallelError("base must be the current checkout HEAD")
    # Read-only planning still refuses uncommitted board metadata.
    if git(root, "status", "--porcelain", "--", ".agentkanban").stdout:
        raise ParallelError("Kanban metadata must be committed")


def selection(
    root: Path,
    ids: list[str],
    *,
    limit: int = 3,
    scopes: dict[str, list[str]] | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    if limit < 1:
        raise ParallelError("limit must be positive")
    board_at_head(root, head(root))
    found = tasks(root)
    if len(set(ids)) != len(ids):
        raise ParallelError("duplicate task selection")
    if set(ids) - found.keys():
        raise ParallelError(f"unknown tasks: {sorted(set(ids) - found.keys())}")
    if set(scopes or {}) - (set(ids) if ids else found.keys()):
        raise ParallelError("scope supplied for an unselected task")
    state = read_state(root)
    graph = kanban.dependency_graph(found)
    active = [j for j in state["jobs"].values() if j["status"] != "integrated"]
    chosen: list[dict[str, Any]] = []
    excluded = []
    candidates = [found[i] for i in ids] if ids else list(found.values())
    for task in sorted(candidates, key=lambda t: (kanban.PRIORITY_ORDER.get(t.priority, 9), t.id)):
        paths = footprint(task.files + (scopes or {}).get(task.id, []))
        reason = ""
        if task.id in state["jobs"]:
            reason = "already assigned"
        elif not kanban.is_ready(task, graph):
            reason = "not ready"
        elif "humain" in task.labels:
            reason = "human decision required"
        elif labels and not set(labels).intersection(task.labels):
            reason = "outside selected labels"
        elif not paths:
            reason = "unknown footprint"
        elif any(overlap(p, shared) for p in paths for shared in RESERVED):
            reason = "coordinator-owned interface"
        elif any(
            dependency in state["jobs"]
            and (
                state["jobs"][dependency]["status"] != "integrated"
                or git(
                    root,
                    "merge-base",
                    "--is-ancestor",
                    state["jobs"][dependency]["merge_sha"],
                    head(root),
                    check=False,
                ).returncode
            )
            for dependency in task.depends_on
        ):
            reason = "dependency not integrated in base"
        elif any(overlap(p, q) for p in paths for job in [*active, *chosen] for q in job["scope"]):
            reason = "overlapping footprint"
        elif len(active) + len(chosen) >= limit:
            reason = "parallel limit reached"
        if reason:
            excluded.append({"id": task.id, "reason": reason})
        else:
            chosen.append({"id": task.id, "scope": paths, "task": task.path})
    return {"base": head(root), "selected": chosen, "excluded": excluded}


def worktrees(root: Path) -> dict[Path, dict[str, str]]:
    entries: dict[Path, dict[str, str]] = {}
    for block in git(root, "worktree", "list", "--porcelain").stdout.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        entries[Path(fields["worktree"]).resolve()] = fields
    return entries


def ensure_worktree(root: Path, path: Path, branch: str, base: str) -> None:
    existing = worktrees(root).get(path.resolve())
    if existing is not None:
        if existing.get("branch") != f"refs/heads/{branch}" or existing.get("HEAD") != base:
            raise ParallelError(f"inconsistent prepared worktree: {path}")
        clean(path)
        return
    if (
        path.exists()
        or git(root, "show-ref", "--verify", f"refs/heads/{branch}", check=False).returncode == 0
    ):
        raise ParallelError(f"path or branch already exists: {path}, {branch}")
    git(root, "worktree", "add", "-b", branch, str(path), base)


def prepare(
    root: Path,
    ids: list[str],
    parent: Path,
    *,
    base: str = "HEAD",
    limit: int = 3,
    scopes: dict[str, list[str]] | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    if not ids:
        raise ParallelError("prepare requires explicit task ids")
    parent = parent.resolve()
    if parent == root or root in parent.parents:
        raise ParallelError("worktrees must be outside the source checkout")
    with locked(root):
        clean(root)
        sha = git(
            root, "rev-parse", "--verify", "--end-of-options", base + "^{commit}"
        ).stdout.strip()
        board_at_head(root, sha)
        state = read_state(root)
        if resume:
            if any(i not in state["jobs"] for i in ids):
                raise ParallelError("no reservation to resume")
            jobs = [state["jobs"][i] for i in ids]
            if any(j["base"] != sha or j["status"] not in ("preparing", "prepared") for j in jobs):
                raise ParallelError("only interrupted preparation at this base can resume")
            if any(Path(j["worktree"]).parent != parent for j in jobs):
                raise ParallelError("resume directory differs from reservation")
        else:
            plan = selection(root, ids, limit=limit, scopes=scopes)
            if plan["excluded"]:
                raise ParallelError(json.dumps(plan["excluded"]))
            jobs = []
            for entry in plan["selected"]:
                jobs.append(
                    {
                        **entry,
                        "base": sha,
                        "branch": f"parallel/{entry['id'].lower()}-{sha[:8]}",
                        "worktree": str(parent / entry["id"].lower()),
                        "status": "preparing",
                    }
                )
            state["jobs"].update({j["id"]: j for j in jobs})
        if "integration" not in state:
            state["integration"] = {
                "path": str(parent / "integration"),
                "branch": f"parallel/integration-{sha[:8]}",
                "base": sha,
            }
        save(root, state)
        integration = state["integration"]
        ensure_worktree(
            root,
            Path(integration["path"]),
            integration["branch"],
            integration.get("head", integration["base"]),
        )
        for job in jobs:
            ensure_worktree(root, Path(job["worktree"]), job["branch"], sha)
            mission = directory(root) / f"{job['id']}.md"
            mission.write_text(
                f"# {job['id']}\n\nWorktree: {job['worktree']}\nBranch: {job['branch']}\n"
                f"Base: {sha}\nTask: {job['task']}\nScope: {json.dumps(job['scope'])}\n\n"
                "Read task/checklist and Graphify before code. Do not edit outside scope.\n"
                "No push, integration, destructive cleanup or automatic done transition.\n"
            )
            job["status"] = "prepared"
            save(root, state)
        return state


def checked_job(root: Path, state: dict[str, Any], identifier: str) -> tuple[dict[str, Any], str]:
    if identifier not in state["jobs"]:
        raise ParallelError(f"unassigned task: {identifier}")
    job = state["jobs"][identifier]
    path = Path(job["worktree"])
    clean(path)
    if git(path, "symbolic-ref", "--short", "HEAD").stdout.strip() != job["branch"]:
        raise ParallelError("worker switched branch")
    sha = head(path)
    if git(root, "merge-base", "--is-ancestor", job["base"], sha, check=False).returncode:
        raise ParallelError("worker history no longer descends from base")
    changed = git(root, "diff", "--name-only", "--no-renames", job["base"], sha).stdout.splitlines()
    if not changed:
        raise ParallelError("worker has no changes")
    outside = [p for p in changed if not covered(p, job["scope"])]
    if outside:
        raise ParallelError(f"out-of-scope changes: {outside}")
    return job, sha


def validate_tree(path: Path, command: list[str], log: Path) -> int:
    if not command:
        raise ParallelError("empty validation command")
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [str(path / ".venv/bin"), str(Path.home() / ".elan/bin"), env.get("PATH", "")]
    )
    with log.open("w") as stream:
        result = subprocess.run(
            command, cwd=path, env=env, stdout=stream, stderr=subprocess.STDOUT, check=False
        )
    return result.returncode


def record(root: Path, identifier: str, command: list[str]) -> dict[str, Any]:
    with locked(root):
        state = read_state(root)
        job, sha = checked_job(root, state, identifier)
        if job["status"] == "integrated":
            raise ParallelError("task already integrated")
        job["status"] = "validating"
        job.pop("validation", None)
        save(root, state)
        log = directory(root) / f"{identifier}-validation.log"
        code = validate_tree(Path(job["worktree"]), command, log)
        job["validation"] = {"sha": sha, "command": command, "returncode": code, "log": str(log)}
        changed_tree = bool(git(Path(job["worktree"]), "status", "--porcelain").stdout)
        job["status"] = "validated" if code == 0 and not changed_tree else "failed"
        save(root, state)
        if changed_tree:
            raise ParallelError("validator modified worker worktree")
        if head(Path(job["worktree"])) != sha:
            job["status"] = "stale"
            save(root, state)
            raise ParallelError("worker changed during validation")
        if code:
            raise ParallelError(f"validation failed ({code}), see {log}")
        return job


def integrate(root: Path, ids: list[str]) -> dict[str, Any]:
    if not ids or len(ids) != len(set(ids)):
        raise ParallelError("explicit, unique integration ids required")
    with locked(root):
        state = read_state(root)
        if "integration" not in state:
            raise ParallelError("no integration worktree")
        integration = state["integration"]
        path = Path(integration["path"])
        clean(path)
        if git(path, "symbolic-ref", "--short", "HEAD").stdout.strip() != integration["branch"]:
            raise ParallelError("integration switched branch")
        expected = integration.get("head", integration["base"])
        if head(path) != expected:
            raise ParallelError("integration HEAD changed; explicit reconciliation required")
        for identifier in ids:
            job, sha = checked_job(root, state, identifier)
            validation = job.get("validation", {})
            if (
                job["status"] != "validated"
                or validation.get("sha") != sha
                or validation.get("returncode") != 0
            ):
                raise ParallelError(f"missing or stale validation: {identifier}")
            job["status"] = "integrating"
            save(root, state)
            merge = git(path, "merge", "--no-ff", "--no-commit", sha, check=False)
            if merge.returncode:
                job["status"] = "conflict"
                save(root, state)
                raise ParallelError(f"merge stopped for {identifier}: {merge.stderr}")
            tree = git(path, "write-tree").stdout.strip()
            log = directory(root) / f"{identifier}-integration.log"
            code = validate_tree(path, validation["command"], log)
            if code:
                job["status"] = "integration-failed"
                save(root, state)
                raise ParallelError(f"integration validation failed ({code}), see {log}")
            # A validator must not rewrite the staged merge or introduce unstaged files.
            if (
                git(path, "write-tree").stdout.strip() != tree
                or git(path, "diff", "--name-only").stdout
                or git(path, "ls-files", "--others", "--exclude-standard").stdout
            ):
                job["status"] = "integration-failed"
                save(root, state)
                raise ParallelError("validator modified the merge worktree")
            git(
                path,
                "commit",
                "-m",
                f"Intégrer {identifier} après validation",
                "-m",
                "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>",
            )
            job["status"] = "integrated"
            job["merge_sha"] = head(path)
            integration["head"] = job["merge_sha"]
            save(root, state)
        return state


def status(root: Path) -> dict[str, Any]:
    state = read_state(root)
    result = json.loads(json.dumps(state))
    actual = worktrees(root)
    if "integration" in result:
        integration = result["integration"]
        path = Path(integration["path"])
        present = actual.get(path.resolve())
        integration["present"] = present is not None
        if present is not None:
            integration["actual_head"] = present.get("HEAD")
            integration["dirty"] = bool(git(path, "status", "--porcelain").stdout)
            integration["needs_reconciliation"] = (
                integration["actual_head"] != integration.get("head", integration["base"])
                or integration["dirty"]
            )
    for job in result["jobs"].values():
        path = Path(job["worktree"])
        present = actual.get(path.resolve())
        job["present"] = present is not None
        if present is not None:
            job["head"] = present.get("HEAD")
            job["dirty"] = bool(git(path, "status", "--porcelain").stdout)
            if job.get("validation", {}).get("sha") not in (None, job["head"]):
                job["status"] = "stale"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=kanban.ROOT)
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("plan", "prepare"):
        p = sub.add_parser(name)
        p.add_argument("ids", nargs="*")
        p.add_argument("--limit", type=int, default=3)
        p.add_argument("--scope", action="append", default=[], metavar="HYP-NNN=PATH")
        if name == "prepare":
            p.add_argument("--directory", type=Path, required=True)
            p.add_argument("--base", default="HEAD")
            p.add_argument("--resume", action="store_true")
        else:
            p.add_argument("--label", action="append")
    sub.add_parser("status")
    p = sub.add_parser("record")
    p.add_argument("id")
    p.add_argument(
        "--command", help="explicit argv parsed without a shell; default: complete validation"
    )
    p = sub.add_parser("integrate")
    p.add_argument("ids", nargs="+")
    args = parser.parse_args(argv)
    try:
        root = Path(git(args.repo, "rev-parse", "--show-toplevel").stdout.strip())
        scopes: dict[str, list[str]] = {}
        for scope in getattr(args, "scope", []):
            if "=" not in scope:
                raise ParallelError("scope must be HYP-NNN=PATH")
            identifier, path = scope.split("=", 1)
            scopes.setdefault(identifier, []).append(path)
        if args.action == "plan":
            result = selection(root, args.ids, limit=args.limit, scopes=scopes, labels=args.label)
        elif args.action == "prepare":
            result = prepare(
                root,
                args.ids,
                args.directory,
                base=args.base,
                limit=args.limit,
                scopes=scopes,
                resume=args.resume,
            )
        elif args.action == "record":
            result = record(
                root, args.id, shlex.split(args.command) if args.command else DEFAULT_COMMAND
            )
        elif args.action == "integrate":
            result = integrate(root, args.ids)
        else:
            result = status(root)
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result)
        return 0
    except (ParallelError, OSError, json.JSONDecodeError) as exc:
        print(f"parallel: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
