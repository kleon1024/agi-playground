"""The no-harness control: one blind model call per task, no loop around it.

`mission.yaml`'s first baseline: "one model call with the issue text and the
failing test, the patch applied blind, no tools, no test feedback, no second
attempt." Stage 02/03 give the model `Read`, `Glob`, `Grep`, `Bash`, `Edit`,
`Write` and let it iterate against the test command until it stops or gives
up. This script gives it none of that. `--disallowedTools` names every tool
Claude Code has, not just the ones stage 03 happened to grant, for the same
reason `claude_arm.py` denies the web tools explicitly rather than leaving
them off an allow list: absent-by-omission and denied are not the same
guarantee if the tool set is ever widened by accident.

With no `Read`, the model cannot see the file it is meant to patch unless the
prompt puts it there. So this harness does what the literature on this exact
ablation calls "oracle file location": the current contents of `source_files`
-- the file(s) `mine_history`'s task construction already names as the ones
the gold patch touches -- are pasted into the prompt. That is a real
concession to the no-tools model, not a hidden one: it means this baseline is
not measuring "can it find the bug," only "can it fix the bug once told where
it is." The harness loop in stage 02/03 has to find the file itself via
`Grep`/`Read`; this baseline is handed that step for free and still has to
produce a correct patch with no chance to see whether it worked. Recorded
under `does_not_prove` in this stage's README.

The model replies with a unified diff and nothing else -- there is no `Edit`
tool to call, so the diff is the only channel it has. This script applies
that diff with plain `git apply`, blind: no retry, no repair, no second
prompt if it fails to apply. A diff that does not apply is not a harness bug
to work around, it is exactly the outcome mission 04's stage 04 failure
taxonomy needs a category for.

Run:
    python no_harness.py --model haiku --repeats 3 --out results.jsonl
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
MINER_PATH = REPO / "04-agentic-platform/task-set/core/mine_history.py"
SCORING_PATH = REPO / "04-agentic-platform/agent-loop/core/scoring.py"
DEFAULT_MANIFEST = REPO / "04-agentic-platform/tasks/private.jsonl"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


MINER = _load("mine_history", MINER_PATH)
SCORING = _load("scoring", SCORING_PATH)

# Every tool Claude Code exposes, denied by name. There is no allow list here
# at all -- an empty allow list plus a partial deny list is still a bet that
# nothing was missed, which is the exact bet claude_arm.py's own comment
# refuses to make.
DENIED_TOOLS = [
    "Read", "Write", "Edit", "MultiEdit", "NotebookEdit",
    "Bash", "Glob", "Grep", "Task", "TodoWrite", "ExitPlanMode",
    "WebSearch", "WebFetch",
]

MAX_CONTEXT_CHARS = 20_000

NO_HARNESS_PROMPT = """A test in this repository is failing. You get exactly one attempt: no tools, \
no chance to run anything, no feedback on whether this works, no second try.

Test command:
    {command}

Test failure output:
{failure}

Current contents of the file(s) that need the fix:

{context}

Reply with ONLY a unified diff (`--- a/path` / `+++ b/path` headers, applicable \
with `git apply`) that fixes the source. Do not include any explanation, and do \
not wrap the diff in a markdown code fence.

Rules:
- The diff may only touch the file(s) shown above.
- Do not touch anything under tests/ -- a diff that does is rejected outright, \
whatever it does.
"""


def read_source_context(work: Path, source_files: list[str]) -> str:
    parts = []
    for rel in source_files:
        text = (work / rel).read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_CONTEXT_CHARS:
            text = text[:MAX_CONTEXT_CHARS] + "\n... [truncated]"
        parts.append(f"### {rel}\n```\n{text}\n```")
    return "\n\n".join(parts)


def invoke(prompt: str, work: Path, model: str, timeout: float) -> dict:
    """One headless Claude Code call, with no tool it could use even if asked."""
    command = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "json",
        "--disallowedTools", *DENIED_TOOLS,
    ]
    try:
        proc = subprocess.run(
            command, cwd=work, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        # A real result, not a harness bug: the wall-clock cap is a declared
        # guardrail (mission.yaml: "a task that hits the cap is a failure,
        # not a retry"), so this is recorded as `timeout`, not retried with a
        # longer cap and not silently swallowed into a crash.
        return {"is_error": True, "timed_out": True, "result": f"no response within {timeout}s"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": (proc.stdout + proc.stderr)[-2000:]}


def extract_diff(text: str) -> str:
    """Strip a markdown fence if the model added one despite being told not to.

    This is software tidying the channel the model replied on, not a second
    attempt at the task -- the model gets no chance to see this happen or
    revise anything as a result of it.
    """
    text = text.strip()
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip() + "\n"


def apply_patch(work: Path, diff_text: str) -> bool:
    """Best-effort mechanical apply. No retry, no repair, no second prompt."""
    diff_text = extract_diff(diff_text)
    if not diff_text.strip():
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as fh:
        fh.write(diff_text)
        patch_path = Path(fh.name)
    try:
        for strip_level in ("-p1", "-p0"):
            proc = subprocess.run(
                ["git", "apply", strip_level, "--whitespace=nowarn", str(patch_path)],
                cwd=work, capture_output=True, text=True, check=False,
            )
            if proc.returncode == 0:
                return True
        return False
    finally:
        patch_path.unlink(missing_ok=True)


@dataclass
class NoHarnessAttempt:
    task_id: str
    model: str
    verdict: str
    resolved: bool
    patch_applied: bool
    wall_clock_s: float
    cost_usd: float
    input_tokens: int
    output_tokens: int
    changed: list[str]
    tampered: list[str]
    regressions: list[str]
    target_failing_after: list[str]
    cli_error: str | None = None


def attempt(
    task: dict, model: str, timeout: float = 300.0, keep: Path | None = None, tag: str = ""
) -> NoHarnessAttempt:
    task_obj = MINER.Task(**task)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "task"
        junit = Path(tmp) / "out.xml"
        MINER.materialize(task_obj, work)
        try:
            target_cmd = SCORING.instrument(task_obj.test_command, junit)
            suite_cmd = SCORING.instrument(task_obj.test_command, junit, targets=["tests"])

            target_before, failure = SCORING.run_and_collect(target_cmd, work, junit)
            if not target_before or not any(
                s in ("failure", "error") for s in target_before.values()
            ):
                raise SystemExit(
                    f"{task_obj.task_id}: target tests do not fail at base state; "
                    f"the manifest is stale or the environment cannot run them.\n{failure[-1500:]}"
                )
            suite_before, _ = SCORING.run_and_collect(suite_cmd, work, junit)

            context = read_source_context(work, task_obj.source_files)
            body = invoke(
                NO_HARNESS_PROMPT.format(
                    command=" ".join(task_obj.test_command), failure=failure, context=context
                ),
                work,
                model,
                timeout,
            )

            if body.get("timed_out"):
                # Nothing was produced, so nothing was applied; the tree is
                # exactly as it was at base state. Re-running the tests would
                # only reconfirm target_before, so this skips straight to a
                # `timeout` verdict rather than re-running for a value already
                # known.
                return NoHarnessAttempt(
                    task_id=task_obj.task_id,
                    model=model,
                    verdict="timeout",
                    resolved=False,
                    patch_applied=False,
                    wall_clock_s=round(time.perf_counter() - started, 1),
                    cost_usd=0.0,
                    input_tokens=0,
                    output_tokens=0,
                    changed=[],
                    tampered=[],
                    regressions=[],
                    target_failing_after=sorted(
                        n for n, s in target_before.items() if s in ("failure", "error")
                    ),
                    cli_error=body.get("result"),
                )

            diff_text = body.get("result", "") if not body.get("is_error") else ""
            patch_applied = apply_patch(work, diff_text) if diff_text.strip() else False

            changed = SCORING.changed_paths(work)
            target_after, _ = SCORING.run_and_collect(target_cmd, work, junit)
            suite_after, _ = SCORING.run_and_collect(suite_cmd, work, junit)
            verdict = SCORING.score(
                task_obj.task_id, changed, target_before, target_after, suite_before, suite_after
            )
            if keep is not None:
                (keep / f"{task_obj.task_id}-{model}{tag}.diff").write_text(diff_text)

            usage = body.get("usage") or {}
            return NoHarnessAttempt(
                task_id=verdict.task_id,
                model=model,
                verdict=verdict.verdict,
                resolved=verdict.resolved,
                patch_applied=patch_applied,
                wall_clock_s=round(time.perf_counter() - started, 1),
                cost_usd=round(body.get("total_cost_usd", 0.0), 4),
                input_tokens=usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                changed=verdict.changed,
                tampered=verdict.tampered,
                regressions=verdict.regressions,
                target_failing_after=verdict.target_failing_after,
                cli_error=body.get("result") if body.get("is_error") else None,
            )
        finally:
            MINER.cleanup(work)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--task-id")
    ap.add_argument("--model", default="haiku", help="haiku | sonnet | opus, or a model id")
    ap.add_argument("--repeats", type=int, default=1, help="independent runs of each task")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--out", type=Path, help="append one JSON line per attempt")
    ap.add_argument("--keep-diffs", type=Path, help="directory to write each produced diff into")
    ap.add_argument(
        "--ceiling", type=float, default=None,
        help="stop before the next attempt if cumulative cost would pass this",
    )
    ap.add_argument(
        "--already-spent", type=float, default=0.0,
        help="cost already consumed elsewhere against the same --ceiling",
    )
    args = ap.parse_args()
    if args.keep_diffs:
        args.keep_diffs.mkdir(parents=True, exist_ok=True)

    tasks = [json.loads(x) for x in args.manifest.read_text().splitlines() if x]
    if args.task_id:
        tasks = [t for t in tasks if t["task_id"] == args.task_id]
        if not tasks:
            raise SystemExit(f"no task {args.task_id!r} in {args.manifest}")

    spent = args.already_spent
    for run_index in range(1, args.repeats + 1):
        for task in tasks:
            if args.ceiling is not None and spent >= args.ceiling:
                print(f"CEILING_EXCEEDED: spent ${spent:.4f} >= ceiling ${args.ceiling:.2f}, stopping")
                return
            record = attempt(
                task,
                args.model,
                timeout=args.timeout,
                keep=args.keep_diffs,
                tag=f"-run{run_index}",
            )
            spent += record.cost_usd
            print(
                f"run {run_index}  {record.verdict:<22} {record.task_id}  "
                f"{record.model}  patch_applied={record.patch_applied}  "
                f"{record.wall_clock_s}s  ${record.cost_usd:.4f}"
            )
            if record.tampered:
                print(f"  GUARDRAIL FIRED: patch touched {record.tampered}")
            if record.cli_error:
                print(f"  cli error: {record.cli_error[:200]}")
            if args.out:
                with args.out.open("a") as fh:
                    fh.write(json.dumps(asdict(record)) + "\n")
    print(f"\ntotal list-price equivalent this run: ${spent - args.already_spent:.4f} "
          f"over {len(tasks) * args.repeats} attempts (cumulative ${spent:.4f})")


if __name__ == "__main__":
    main()
