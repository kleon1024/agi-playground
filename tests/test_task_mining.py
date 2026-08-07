"""Structural checks on the private task set.

These do not run the miner — verification materializes git worktrees and
installs dependency groups, which belongs in `runs/`, not in CI. What CI can
cheaply defend is that the committed manifest still describes scoreable tasks:
the answer withheld, the goal in the base state, and the two never mixed.
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINER_PATH = ROOT / "04-agentic-platform/00-task-set/core/mine_history.py"
MANIFEST_PATH = ROOT / "04-agentic-platform/tasks/private.jsonl"
CANDIDATES_PATH = ROOT / "04-agentic-platform/tasks/candidates.jsonl"

SPEC = importlib.util.spec_from_file_location("mine_history", MINER_PATH)
assert SPEC is not None and SPEC.loader is not None
MINER = importlib.util.module_from_spec(SPEC)
# `@dataclass` resolves its annotations through `sys.modules[cls.__module__]`,
# so a module loaded by path must be registered before it is executed.
sys.modules["mine_history"] = MINER
SPEC.loader.exec_module(MINER)


def _tasks():
    return [json.loads(line) for line in MANIFEST_PATH.read_text().splitlines() if line]


def test_files_are_sorted_into_the_three_roles():
    """Tests define the goal, source files are the answer, environment files
    are neither and must ride with the base state — see the README."""
    assert MINER.classify("tests/test_decode_correctness.py") == "test"
    assert MINER.classify("pyproject.toml") == "env"
    assert MINER.classify("uv.lock") == "env"
    assert MINER.classify("01-language-model/05-serve/core/engine.py") == "source"
    # A lockfile nested inside a package is that package's business, not the
    # environment the task runs in.
    assert MINER.classify("site/package-lock.json") == "source"


def test_pytest_exit_codes_are_not_collapsed_to_a_boolean():
    """Exit 5 means *no tests ran*. Reading it as a failure is what made the
    first version of this miner reject its best task; reading it as a pass
    would admit a task no patch can ever satisfy. It is neither.
    """
    assert MINER.PYTEST_NOTHING_COLLECTED not in (
        MINER.PYTEST_PASSED,
        MINER.PYTEST_FAILED,
    )


def test_manifest_tasks_withhold_their_answer():
    tasks = _tasks()
    assert tasks, "the private task set is empty"
    for task in tasks:
        name = task["task_id"]
        assert task["target_tests"], f"{name} has no test to score against"
        assert task["source_files"], f"{name} has no gold patch, so nothing is withheld"
        # The one mixture that would break scoring: a test file inside the gold
        # patch is a goal the agent is handed instead of asked to satisfy.
        leaked = [f for f in task["source_files"] if MINER.classify(f) != "source"]
        assert not leaked, f"{name} leaks {leaked} into the gold patch"
        assert all(f in task["test_files"] for f in task["target_tests"])


def test_the_task_set_is_drawn_from_the_candidate_set():
    """`mine` writes candidates; `verify --write` writes tasks. They are
    separate files because they were once one, and re-running `mine` replaced
    the verified set with the unverified one. This cannot detect that on
    contents alone -- nothing can, they are the same shape -- but it does catch
    a manifest that drifted from the history it claims to come from."""
    candidates = {
        json.loads(line)["task_id"]
        for line in CANDIDATES_PATH.read_text().splitlines()
        if line
    }
    for task in _tasks():
        assert task["task_id"] in candidates, (
            f"{task['task_id']} is in the task set but not in the candidate set; "
            "re-run mine_history.py mine, then verify --write"
        )


def test_manifest_records_a_command_that_names_its_target():
    """`verify` rewrites each task's command to whichever one actually collects
    its tests, so a manifest command that does not mention the target has not
    been through verification."""
    for task in _tasks():
        command = task["test_command"]
        assert command[:2] == ["uv", "run"]
        for target in task["target_tests"]:
            assert target in command, f"{task['task_id']} command does not run {target}"
