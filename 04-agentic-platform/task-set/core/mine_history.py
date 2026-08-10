"""Turn this repository's own fix commits into agent tasks.

A task is a repository state where a test fails, plus the knowledge that some
change to non-test code makes it pass. Git history is full of those already:
every commit that fixed a bug and added the test proving it is a task with the
answer attached.

The construction, for a fix commit `C` with parent `P`:

    base  = P, plus C's changes to test and environment files
    gold  = C's changes to everything else
    task  = make the failing test pass, without touching the tests

Why environment files ride along with the tests rather than sitting in the gold
patch: `b81c414` fixed the serving engine *and* added the `torch` dependency
group its new test needs. Leave that in the gold patch and the base state
cannot run the test at all, so the task is unsolvable for a reason that has
nothing to do with the bug. The rule is that the agent is asked to fix code,
not to reconstruct a dependency declaration.

This set is small and it is not a benchmark. It is a **contamination control**:
tasks mined from a repository whose history is not in any model's training
data, to sit beside a public benchmark that may well be. Report the two
separately, never pooled -- see `../README.md`.

`mine` and `verify` deliberately write different files. Candidates go to
`tasks/candidates.jsonl`; only `verify --write` produces `tasks/private.jsonl`,
which is the file everything downstream reads. Pointing both at one path is how
an unverified candidate set gets committed as the task set -- which happened
here on 2026-07-29, and no test caught it, because a candidate and a task are
indistinguishable from their contents alone. The difference is which command
wrote the file, so that is what the filenames record.

Usage:
    python mine_history.py candidates
    python mine_history.py mine            # -> ../tasks/candidates.jsonl
    python mine_history.py verify --write  # -> ../tasks/private.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TASKS = REPO / "04-agentic-platform/tasks"
CANDIDATES_PATH = TASKS / "candidates.jsonl"  # what `mine` produces: unverified
VERIFIED_PATH = TASKS / "private.jsonl"  # what `verify --write` produces

# Three classes of file, because they play three different roles in a task.
TEST_PREFIXES = ("tests/",)
ENV_FILES = {"pyproject.toml", "uv.lock", "package.json", "package-lock.json"}


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd or REPO, capture_output=True, text=True, check=True
    ).stdout


def classify(path: str) -> str:
    """test | env | source. The split that defines what the agent must do."""
    if path.startswith(TEST_PREFIXES):
        return "test"
    if path in ENV_FILES:
        return "env"
    return "source"


@dataclass
class Task:
    task_id: str
    source: str  # "private" -- the label that keeps these out of pooled scores
    commit: str  # the fix, for the record; never shown to the agent
    base_commit: str  # its parent: where the agent starts
    subject: str
    test_files: list[str]
    source_files: list[str]
    env_files: list[str]
    target_tests: list[str]  # what must go from failing to passing
    test_command: list[str]


def _changed(sha: str) -> list[str]:
    out = git("show", "--name-only", "--format=", sha).strip()
    return [line for line in out.splitlines() if line]


def _is_python_fix(files: list[str]) -> bool:
    """A usable candidate changes at least one test and at least one non-test
    Python source file. Commits that only move markdown around are real fixes
    but they are not tasks a test can score."""
    kinds = {classify(f) for f in files}
    has_python_source = any(classify(f) == "source" and f.endswith(".py") for f in files)
    return "test" in kinds and has_python_source


def find_candidates() -> list[tuple[str, str]]:
    log = git("log", "--format=%H%x00%s", "--all").strip().split("\n")
    out = []
    for line in log:
        sha, _, subject = line.partition("\0")
        if not subject.startswith("fix"):
            continue
        try:
            files = _changed(sha)
        except subprocess.CalledProcessError:
            continue
        if _is_python_fix(files):
            out.append((sha, subject))
    return out


def build_task(sha: str, subject: str) -> Task:
    files = _changed(sha)
    buckets: dict[str, list[str]] = {"test": [], "env": [], "source": []}
    for f in files:
        buckets[classify(f)].append(f)

    # Only Python test files can be run as the target. A commit may also touch
    # fixture data under tests/; that belongs in the base state but is not a
    # thing pytest can be pointed at.
    targets = [f for f in buckets["test"] if f.endswith(".py")]
    return Task(
        task_id=f"private-{sha[:7]}",
        source="private",
        commit=sha,
        base_commit=git("rev-parse", f"{sha}^").strip(),
        subject=subject,
        test_files=buckets["test"],
        source_files=buckets["source"],
        env_files=buckets["env"],
        target_tests=targets,
        test_command=["uv", "run", "pytest", "-q", *targets],
    )


def _extract(commit: str, dest: Path, paths: list[str] | None = None) -> None:
    """Export a commit's files -- and only its files -- into `dest`.

    `git archive` rather than `git checkout`, because a checkout needs a
    repository and a repository carries history. See `materialize`.
    """
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "state.tar"
        args = ["archive", "--format=tar", "-o", str(archive), commit]
        if paths:
            args += ["--", *paths]
        git(*args)
        with tarfile.open(archive) as tf:
            tf.extractall(dest, filter="data")


def materialize(task: Task, dest: Path) -> None:
    """Build the base state as a standalone repository containing no history.

    This was a `git worktree` at the parent commit, which was wrong in a way
    that would have invalidated every measurement taken with it. A worktree
    shares the original object database, so from inside the task
    `git log --all` lists the fix commit -- subject line describing the bug
    included -- and `git show <sha>` prints the patch. The answer sits one
    command away from an agent being asked to derive it, and a coding agent
    reads git history early and by habit.

    So the base state is exported with `git archive` instead: the parent
    commit's files, the fix's test and environment files laid on top, and then
    `git init` on the result. The repository an agent sees has exactly one
    commit -- the task -- and no route to the answer.

    That single commit is also what makes the diff mean something. Without it
    `git status` would report the test files the task construction just laid
    down, and the test-tampering guardrail would fire on every attempt,
    scoring every arm at zero while looking like it worked.

    Known limitation: an overlay cannot express a deletion. A fix commit that
    *removed* a test file leaves that file present in the base state. None of
    the current tasks do, and `verify` would reject one that broke because of
    it.
    """
    _extract(task.base_commit, dest)
    paths = task.test_files + task.env_files
    if paths:
        _extract(task.commit, dest, paths)

    identity = ["-c", "user.name=task-harness", "-c", "user.email=harness@localhost"]
    git("init", "-q", "-b", "main", cwd=dest)
    git("add", "-A", cwd=dest)
    git(*identity, "commit", "--no-verify", "-q", "-m", "task base state", cwd=dest)


def apply_gold(task: Task, dest: Path) -> None:
    """Lay the withheld half of the fix commit over a materialized task."""
    if task.source_files:
        _extract(task.commit, dest, task.source_files)


def cleanup(dest: Path) -> None:
    shutil.rmtree(dest, ignore_errors=True)


# pytest's exit code is not a boolean, and treating it as one is how a broken
# task gets admitted to a benchmark. 5 means *nothing was collected* -- the
# module was skipped, or the path matched no tests. That is neither a pass nor
# a failure, and calling it a failure would let through a task whose target
# test never runs, which no patch can ever fix and every patch appears to fail.
PYTEST_PASSED = 0
PYTEST_FAILED = 1
PYTEST_NOTHING_COLLECTED = 5

# Optional dependency groups to try, in order. `tests/test_decode_correctness.py`
# calls `pytest.importorskip("torch")`, so under the default environment it is
# collected as a skip and pytest exits 5. The right test command for a task is
# whichever one actually runs it.
CANDIDATE_GROUPS: list[list[str]] = [[], ["--group", "torch"]]


def run_tests(command: list[str], cwd: Path) -> tuple[int, str]:
    # VIRTUAL_ENV is inherited from whatever shell invoked this and points at
    # the real repository's environment; uv warns and ignores it, but clearing
    # it makes the worktree's own environment the only one in play.
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    proc = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False, env=env
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-2000:]


def resolve_test_command(task: Task, cwd: Path) -> list[str] | None:
    """The first candidate command under which the target tests are collected.

    Returns None when no candidate collects anything, which disqualifies the
    task rather than silently scoring it.
    """
    for group in CANDIDATE_GROUPS:
        command = ["uv", "run", *group, "pytest", "-q", *task.target_tests]
        code, _ = run_tests(command, cwd)
        if code != PYTEST_NOTHING_COLLECTED:
            return command
    return None


def verify(task: Task) -> tuple[bool, str]:
    """A task is valid only if the target tests fail at base and pass once the
    gold patch is applied. Anything else is a broken task, and shipping broken
    tasks is how a benchmark quietly measures the wrong thing.

    Mutates `task.test_command` to whichever command actually collects the
    target tests, so a verified manifest carries a command known to run.
    """
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
                # Import error, usage error, interrupt. The tests did not fail
                # for the reason the task claims, so the task is not usable.
                return False, f"base run exited {base_code}, not a test failure:\n{base_log[-600:]}"

            apply_gold(task, work)
            gold_code, gold_log = run_tests(command, work)
            if gold_code != PYTEST_PASSED:
                return False, f"target tests still fail after gold patch:\n{gold_log[-600:]}"
            return True, f"fails at base, passes with gold ({len(task.target_tests)} test files)"
        finally:
            cleanup(work)


def cmd_candidates(_args) -> None:
    for sha, subject in find_candidates():
        print(f"{sha[:7]}  {subject}")


def cmd_mine(args) -> None:
    tasks = [build_task(sha, subject) for sha, subject in find_candidates()]
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
