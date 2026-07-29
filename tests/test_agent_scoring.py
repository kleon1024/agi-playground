"""The scorer decides whether an agent resolved a task. These are the cases
where believing the agent and believing the observations diverge.

CPU-only: no model, no worktree, no network. `run_task.py` is the part that
needs a repository and an endpoint, and it is exercised in `runs/`.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORING_PATH = ROOT / "missions/04-code-agent/02-agent-loop/core/scoring.py"

SPEC = importlib.util.spec_from_file_location("scoring", SCORING_PATH)
assert SPEC is not None and SPEC.loader is not None
SCORING = importlib.util.module_from_spec(SPEC)
sys.modules["scoring"] = SCORING
SPEC.loader.exec_module(SCORING)

JUNIT = "/tmp/out.xml"


def _score(**overrides):
    kwargs = {
        "task_id": "t",
        "changed": [],
        "target_before": {"a::b": "failure"},
        "target_after": {"a::b": "passed"},
        "suite_before": {"a::b": "failure", "c::d": "passed"},
        "suite_after": {"a::b": "passed", "c::d": "passed"},
    }
    kwargs.update(overrides)
    return SCORING.score(**kwargs)


def test_the_recorded_test_command_survives_instrumentation():
    """A task's command carries the dependency group that makes its tests
    collectable. Rebuilding the command instead of editing it would drop that
    and silently measure a run where nothing was collected."""
    command = ["uv", "run", "--group", "torch", "pytest", "-q", "tests/test_decode.py"]

    instrumented = SCORING.instrument(command, Path(JUNIT))

    assert instrumented[:5] == ["uv", "run", "--group", "torch", "pytest"]
    assert f"--junit-xml={JUNIT}" in instrumented
    assert instrumented[-1] == "tests/test_decode.py"


def test_instrumentation_can_retarget_to_the_whole_suite():
    command = ["uv", "run", "pytest", "-q", "tests/test_decode.py"]

    instrumented = SCORING.instrument(command, Path(JUNIT), targets=["tests"])

    assert instrumented[-1] == "tests"
    assert "tests/test_decode.py" not in instrumented
    assert "-q" in instrumented


def test_a_passing_target_does_not_survive_a_touched_test_file():
    """The case the guardrail exists for. Target green, suite green, nothing
    regressed -- and the patch edited the assertion. Every other signal says
    resolved."""
    result = _score(changed=["tests/test_decode.py", "src/engine.py"])

    assert result.verdict == "tampered"
    assert result.resolved is False
    assert result.tampered == ["tests/test_decode.py"]


def test_a_deleted_test_counts_as_a_regression():
    """Absence is not a pass. A test present in the baseline and missing
    afterwards has to be caught by the same check that catches one that
    started failing, or deleting a file becomes cheaper than fixing it."""
    result = _score(
        changed=["src/engine.py"],
        suite_after={"a::b": "passed"},  # c::d is gone
    )

    assert result.verdict == "regressed"
    assert result.regressions == ["c::d"]


def test_no_outcomes_is_not_a_pass():
    """An empty result set means the tests did not run. Reading it as success
    is how a task nobody solved gets scored as resolved."""
    result = _score(target_after={})

    assert result.verdict == "no_tests_ran"
    assert result.resolved is False


def test_a_real_fix_resolves():
    result = _score(changed=["missions/01-language-model-agent/05-serve/core/engine.py"])

    assert result.verdict == "resolved"
    assert result.resolved is True
    assert result.tampered == []


def test_junit_reports_skips_as_skipped_not_passed(tmp_path):
    xml = tmp_path / "j.xml"
    xml.write_text(
        '<testsuites><testsuite><testcase classname="m" name="ok"/>'
        '<testcase classname="m" name="gone"><skipped message="no torch"/></testcase>'
        '<testcase classname="m" name="bad"><failure message="boom"/></testcase>'
        "</testsuite></testsuites>"
    )

    outcomes = SCORING.parse_junit(xml)

    assert outcomes == {"m::ok": "passed", "m::gone": "skipped", "m::bad": "failure"}
