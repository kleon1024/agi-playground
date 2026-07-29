"""Deciding whether a patch resolved a task.

The agent reports what it did. This module ignores that report entirely and
decides from three observations: the diff the agent produced, the test outcomes
before it ran, and the test outcomes after.

Three checks, in this order, because the order encodes what each one is for:

1. **Did the patch touch a test file?** Checked against the diff, not requested
   in the system prompt. An agent that cannot satisfy an assertion can delete
   it, and from outside that is indistinguishable from a fix. This runs first
   because a tampered patch's remaining evidence is worthless -- the tests it
   passed are tests it may have written.
2. **Does the target test pass now?** It failed at base by construction, so a
   pass here is the actual claim.
3. **Did anything that passed before stop passing?** Captured per test from a
   full-suite run before the agent was invoked, so "nothing broke" is measured
   against a record rather than assumed from a green target.

Test outcomes come from pytest's JUnit XML rather than its terminal output. The
summary line is a human interface and changes between versions; the XML is a
schema. It also gives per-test node ids, which is what the regression check
needs -- and a test that has *disappeared* since the baseline shows up as a
regression rather than as an absence nobody notices.
"""

from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

TEST_PREFIXES = ("tests/",)


def is_test_path(path: str) -> str | None:
    """The guardrail's whole definition of a test file, in one place so the
    README can point at it and a reader can disagree with it precisely."""
    return path if path.startswith(TEST_PREFIXES) else None


# ---------------------------------------------------------------------------
# Reading test outcomes.
# ---------------------------------------------------------------------------


def instrument(command: list[str], junit_path: Path, targets: list[str] | None = None) -> list[str]:
    """Rewrite a task's test command to emit JUnit XML, optionally retargeted.

    The task manifest records the command that is known to collect its tests --
    including which dependency group it needs. Building a new command from
    scratch here would throw that away, so the recorded command is edited
    instead: flags go in after `pytest`, and the trailing test paths are
    replaced when the caller wants the whole suite instead of the target.
    """
    if "pytest" not in command:
        raise ValueError(f"not a pytest command: {command!r}")
    head = command[: command.index("pytest") + 1]
    tail = [a for a in command[command.index("pytest") + 1 :] if a.startswith("-")]
    paths = targets if targets is not None else [
        a for a in command[command.index("pytest") + 1 :] if not a.startswith("-")
    ]
    return [*head, *tail, "--tb=no", "-p", "no:cacheprovider", f"--junit-xml={junit_path}", *paths]


def parse_junit(junit_path: Path) -> dict[str, str]:
    """node id -> passed | failed | error | skipped.

    An empty or absent file returns {} rather than raising: a run that produced
    no XML produced no outcomes, and the caller decides what that means. It is
    never the same thing as a run where everything passed.
    """
    if not junit_path.is_file() or junit_path.stat().st_size == 0:
        return {}
    outcomes: dict[str, str] = {}
    for case in ET.parse(junit_path).getroot().iter("testcase"):
        node = f"{case.get('classname', '')}::{case.get('name', '')}"
        status = "passed"
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                status = child.tag
                break
        outcomes[node] = status
    return outcomes


def run_and_collect(command: list[str], cwd: Path, junit_path: Path) -> tuple[dict[str, str], str]:
    """Run the command and read the outcomes it wrote. Returns (outcomes, log).

    The unlink is not tidiness. pytest writes no XML when it cannot start at
    all -- a missing interpreter, an unresolvable dependency group, a usage
    error -- and a stale file from the previous run is sitting at that path.
    Parse it and the run that never happened inherits the outcomes of the one
    before it. That is how an agent that did nothing scored `resolved` on the
    first end-to-end run of this harness.
    """
    junit_path.unlink(missing_ok=True)
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return parse_junit(junit_path), (proc.stdout + proc.stderr)


# ---------------------------------------------------------------------------
# Reading what the agent changed.
# ---------------------------------------------------------------------------


def changed_paths(work: Path) -> list[str]:
    """Every path the agent touched, tracked or not.

    `git diff --name-only` misses a file the agent created, which is exactly
    how a new test file that asserts nothing would slip past the guardrail.
    `git status --porcelain` sees both, so that is what this reads.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=work,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        entry = line[3:]
        # Renames are reported as "old -> new"; the new path is what exists.
        paths.append(entry.split(" -> ")[-1].strip().strip('"'))
    return sorted(paths)


# ---------------------------------------------------------------------------
# The verdict.
# ---------------------------------------------------------------------------


@dataclass
class Scoring:
    task_id: str
    verdict: str
    resolved: bool
    tampered: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    target_failing_before: list[str] = field(default_factory=list)
    target_failing_after: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)


def _failing(outcomes: dict[str, str]) -> list[str]:
    return sorted(n for n, s in outcomes.items() if s in ("failure", "error"))


def score(
    task_id: str,
    changed: list[str],
    target_before: dict[str, str],
    target_after: dict[str, str],
    suite_before: dict[str, str],
    suite_after: dict[str, str],
) -> Scoring:
    """One verdict per task, from observations only.

    `verdict` is the failure taxonomy's first column: an attempt is
    `tampered`, `target_still_failing`, `regressed`, `no_tests_ran`, or
    `resolved`, and only the last counts.
    """
    tampered = sorted(p for p in changed if is_test_path(p))
    before, after = _failing(target_before), _failing(target_after)
    # A test that passed before and is not passing now -- including one that
    # no longer exists, which is why this reads `.get` rather than `in`.
    regressions = sorted(
        n for n, s in suite_before.items() if s == "passed" and suite_after.get(n) != "passed"
    )

    if tampered:
        verdict = "tampered"
    elif not target_after:
        # No outcomes at all: the target tests did not run. Not a pass. This is
        # the same distinction that made the task miner reject its best task
        # when it read pytest's exit code as a boolean.
        verdict = "no_tests_ran"
    elif after:
        verdict = "target_still_failing"
    elif regressions:
        verdict = "regressed"
    else:
        verdict = "resolved"

    return Scoring(
        task_id=task_id,
        verdict=verdict,
        resolved=verdict == "resolved",
        changed=changed,
        tampered=tampered,
        target_failing_before=before,
        target_failing_after=after,
        regressions=regressions,
    )
