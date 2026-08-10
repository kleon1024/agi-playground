"""Turn a public repository's own fix commits into agent tasks.

`mine_history.py` mines this repository's own history: a contamination
control, because agi-playground is in no model's training data. This module
applies the identical rule --

    base  = P, plus C's changes to test and environment files
    gold  = C's changes to everything else
    task  = make the failing test pass, without touching the tests

-- to a small, public, permissively-licensed repository instead:
more-itertools (MIT, https://github.com/more-itertools/more-itertools). Its
history is exactly what the private set is built to *not* be: possibly inside
a model's training data. Report the two sets separately, per
`../README.md` and `mission.yaml`'s guardrail that neither is pooled into the
other.

The source repository is not vendored. It is cloned on demand into
`../data/cache/more-itertools` (gitignored, matching the `**/data/cache/`
convention mission 05 and 07 established for fetched datasets) and pinned to
one commit, `PUBLIC_REPO_PIN`, so re-mining is reproducible rather than
mining a moving target. Cloning happens only during mining -- a one-time, $0
data-curation step -- not during a scored agent attempt, which still runs with
no network access, same as the private set.

Task shape is identical to `mine_history.py`'s `Task`: same ten fields, same
JSON-lines manifest, same scorer contract. `source="public"` and
`task_id` prefixed `public-` are the only markers distinguishing where a task
came from; everything downstream (`02-agent-loop/core/run_task.py`,
`scoring.py`) reads it exactly like a private task once materialized.

One real difference: the target repository is pure Python with no
project-specific dependencies beyond pytest, and its own `pyproject.toml`
travels along with `git archive`'s full-tree export of the base commit. Test
commands here run `uv run --no-project --with pytest pytest ...` rather than
`uv run pytest ...` -- `--no-project` skips that foreign `pyproject.toml`
instead of trying to build the package through it, and `--with pytest` gets
the one dependency the tests actually need, resolved from uv's existing
package cache.

Usage:
    python mine_public.py candidates
    python mine_public.py mine            # -> ../tasks/public-candidates.jsonl
    python mine_public.py verify --write  # -> ../tasks/public.jsonl
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TASKS = REPO / "04-agentic-platform/tasks"
CANDIDATES_PATH = TASKS / "public-candidates.jsonl"
VERIFIED_PATH = TASKS / "public.jsonl"

PUBLIC_REPO_URL = "https://github.com/more-itertools/more-itertools.git"
# Pinned so `mine`/`verify` re-run against the exact history this set was
# built from, not whatever the upstream default branch has moved to since.
PUBLIC_REPO_PIN = "9ddc55c57390707d97d96302eea1992919c8d930"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache" / "more-itertools"

TEST_PREFIXES = ("tests/",)
ENV_FILES = {"pyproject.toml", "uv.lock", "package.json", "package-lock.json"}
# `--with=pytest` as one token, not `--with pytest` as two: `instrument()` in
# `../02-agent-loop/core/scoring.py` finds *the first* list element equal to
# the literal string "pytest" and splices JUnit flags in right after it. Two
# separate tokens put a false match there -- the `--with` value -- before the
# real pytest subcommand, and every flag lands in the wrong place. One token
# has no element that reads as exactly "pytest" except the subcommand itself.
TEST_RUNNER = ["uv", "run", "--no-project", "--with=pytest"]


def ensure_source_repo() -> Path:
    """Clone the public repo into the gitignored cache, pinned to one commit.

    Idempotent: a repeat call against an already-pinned cache does no network
    work at all -- the commit's presence is checked locally first. This is the
    only function in this file that can touch the network, and only mining a
    fresh cache needs it; a scored agent attempt never calls it cold.
    """
    if not CACHE_DIR.exists():
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--quiet", PUBLIC_REPO_URL, str(CACHE_DIR)], check=True
        )
    have_pin = subprocess.run(
        ["git", "cat-file", "-e", f"{PUBLIC_REPO_PIN}^{{commit}}"],
        cwd=CACHE_DIR, capture_output=True, check=False,
    ).returncode == 0
    if not have_pin:
        subprocess.run(["git", "fetch", "--quiet", "origin", PUBLIC_REPO_PIN], cwd=CACHE_DIR, check=True)
    subprocess.run(["git", "checkout", "-q", PUBLIC_REPO_PIN], cwd=CACHE_DIR, check=True)
    return CACHE_DIR


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def classify(path: str) -> str:
    if path.startswith(TEST_PREFIXES):
        return "test"
    if path in ENV_FILES:
        return "env"
    return "source"


@dataclass
class Task:
    task_id: str
    source: str  # "public" -- the label that keeps these out of pooled scores
    commit: str
    base_commit: str
    subject: str
    test_files: list[str]
    source_files: list[str]
    env_files: list[str]
    target_tests: list[str]
    test_command: list[str]


def _changed(sha: str, repo: Path) -> list[str]:
    out = git("show", "--name-only", "--format=", sha, cwd=repo).strip()
    return [line for line in out.splitlines() if line]


def _is_python_fix(files: list[str]) -> bool:
    kinds = {classify(f) for f in files}
    has_python_source = any(classify(f) == "source" and f.endswith(".py") for f in files)
    return "test" in kinds and has_python_source


def find_candidates(repo: Path) -> list[tuple[str, str]]:
    log = git("log", "--format=%H%x00%s", "--all", cwd=repo).strip().split("\n")
    out = []
    for line in log:
        sha, _, subject = line.partition("\0")
        # Same rule as mine_history.py: a lowercase "fix" prefix, not "Fix" --
        # this repository's own convention, applied unchanged to a repository
        # that does not share it. It is a narrowing, not a relaxation: fewer
        # candidates pass, never more.
        if not subject.startswith("fix"):
            continue
        try:
            files = _changed(sha, repo)
        except subprocess.CalledProcessError:
            continue
        if _is_python_fix(files):
            out.append((sha, subject))
    return out


def build_task(sha: str, subject: str, repo: Path) -> Task:
    files = _changed(sha, repo)
    buckets: dict[str, list[str]] = {"test": [], "env": [], "source": []}
    for f in files:
        buckets[classify(f)].append(f)

    targets = [f for f in buckets["test"] if f.endswith(".py")]
    return Task(
        task_id=f"public-{sha[:7]}",
        source="public",
        commit=sha,
        base_commit=git("rev-parse", f"{sha}^", cwd=repo).strip(),
        subject=subject,
        test_files=buckets["test"],
        source_files=buckets["source"],
        env_files=buckets["env"],
        target_tests=targets,
        test_command=[*TEST_RUNNER, "pytest", "-q", *targets],
    )


def _extract(commit: str, dest: Path, repo: Path, paths: list[str] | None = None) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "state.tar"
        args = ["archive", "--format=tar", "-o", str(archive), commit]
        if paths:
            args += ["--", *paths]
        git(*args, cwd=repo)
        with tarfile.open(archive) as tf:
            tf.extractall(dest, filter="data")


def materialize(task: Task, dest: Path) -> None:
    """Same construction as `mine_history.py materialize` -- a standalone
    one-commit repository, base state plus the fix's test/env files laid on
    top, no route back to the answer -- pointed at the cached public clone
    instead of this repository.
    """
    repo = ensure_source_repo()
    _extract(task.base_commit, dest, repo)
    paths = task.test_files + task.env_files
    if paths:
        _extract(task.commit, dest, repo, paths)

    identity = ["-c", "user.name=task-harness", "-c", "user.email=harness@localhost"]
    git("init", "-q", "-b", "main", cwd=dest)
    git("add", "-A", cwd=dest)
    git(*identity, "commit", "--no-verify", "-q", "-m", "task base state", cwd=dest)


def apply_gold(task: Task, dest: Path) -> None:
    if task.source_files:
        _extract(task.commit, dest, ensure_source_repo(), task.source_files)


def cleanup(dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)


PYTEST_PASSED = 0
PYTEST_FAILED = 1
PYTEST_NOTHING_COLLECTED = 5


def run_tests(command: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr)[-2000:]


def resolve_test_command(task: Task, cwd: Path) -> list[str] | None:
    command = [*TEST_RUNNER, "pytest", "-q", *task.target_tests]
    code, _ = run_tests(command, cwd)
    return None if code == PYTEST_NOTHING_COLLECTED else command


def verify(task: Task) -> tuple[bool, str]:
    """Identical admission rule to `mine_history.py verify`: fails at base,
    passes with gold, or the task is not shipped."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "wt"
        materialize(task, work)
        try:
            command = resolve_test_command(task, work)
            if command is None:
                return False, "no candidate command collects the target tests"
            task.test_command = command

            base_code, base_log = run_tests(command, work)
            if base_code == PYTEST_PASSED:
                return False, "target tests already PASS at base state"
            if base_code != PYTEST_FAILED:
                return False, f"base run exited {base_code}, not a test failure:\n{base_log[-600:]}"

            apply_gold(task, work)
            gold_code, gold_log = run_tests(command, work)
            if gold_code != PYTEST_PASSED:
                return False, f"target tests still fail after gold patch:\n{gold_log[-600:]}"
            return True, f"fails at base, passes with gold ({len(task.target_tests)} test files)"
        finally:
            cleanup(work)


def cmd_candidates(_args) -> None:
    repo = ensure_source_repo()
    for sha, subject in find_candidates(repo):
        print(f"{sha[:7]}  {subject}")


def cmd_mine(args) -> None:
    repo = ensure_source_repo()
    tasks = [build_task(sha, subject, repo) for sha, subject in find_candidates(repo)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for task in tasks:
            fh.write(json.dumps(asdict(task)) + "\n")
    print(f"wrote {len(tasks)} candidate tasks to {args.out}")
    print("candidates, not tasks: run `verify` before any of these are used")


def cmd_verify(args) -> None:
    tasks = [Task(**json.loads(line)) for line in args.candidates.read_text().splitlines() if line]
    valid = []
    for task in tasks:
        ok, note = verify(task)
        print(f"{'PASS' if ok else 'SKIP'}  {task.task_id}  {task.subject[:52]}")
        print(f"      {note.splitlines()[0] if note else ''}")
        if ok:
            valid.append(task)
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w") as fh:
            for task in valid:
                fh.write(json.dumps(asdict(task)) + "\n")
        print(f"\nwrote {len(valid)} of {len(tasks)} candidates to {args.out}")
    else:
        print(f"\n{len(valid)} of {len(tasks)} verifiable; re-run with --write to publish")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("candidates")
    mine = sub.add_parser("mine")
    mine.add_argument("--out", type=Path, default=CANDIDATES_PATH)
    ver = sub.add_parser("verify")
    ver.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    ver.add_argument("--out", type=Path, default=VERIFIED_PATH)
    ver.add_argument("--write", action="store_true", help="publish the tasks that verified")
    args = ap.parse_args()
    {"candidates": cmd_candidates, "mine": cmd_mine, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
