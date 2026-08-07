"""One retry turn with real outcome feedback -- still no tools.

`mission.yaml`'s no-harness baseline (stage 01) gives a model one blind call:
issue, failing test, source file contents, produce a diff, applied blind, no
retry. The full harness (stage 03) gives up to 25 turns with `Read`, `Bash`,
and real test execution. Stage 04 catalogued what the no-harness arm's twelve
unresolved attempts actually did: eleven diffs `git apply` rejected outright,
one diff applied but left the target test failing.

Between "zero feedback" and "a full tool loop" sits a question stage 01/03
never isolated: does seeing the real, concrete outcome of your own last
attempt -- not tools, not a chance to explore, just "here is what actually
happened" -- help on its own? This script answers it. For every no-harness
attempt that did not resolve (and did produce a diff), it re-derives the real
outcome of that exact diff on a fresh copy of the task, shows the model its
own prior diff plus that real outcome, and asks for one corrected diff. Still
`--disallowedTools` denies everything stage 01 denies. The only new variable
is outcome-feedback; tool access is stage 02/03's question, not this one.

Reused directly from stage 01's `no_harness.py` (imported, not copied):
`MINER`, `SCORING`, `read_source_context`, `invoke`, `extract_diff`,
`apply_patch`, `NO_HARNESS_PROMPT`'s command/context conventions, and the
`--ceiling`/`--already-spent` cost-guardrail pattern. New in this file: the
retry prompt template, `apply_patch_verbose` (stage 01's `apply_patch` reports
only success/failure; this needs the real `git apply` stderr text to show the
model), the candidate-selection logic that reconstructs which recorded diff
file belongs to which JSONL record, and the reset-to-base-state step that
keeps the retry's "current contents" honestly pre-patch rather than showing
the file with the model's own wrong diff still applied.

Run:
    python close_the_loop.py --model haiku --ceiling 30 --already-spent 14.9034
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
NO_HARNESS_PATH = REPO / "04-agentic-platform/01-no-harness/core/no_harness.py"
DEFAULT_MANIFEST = REPO / "04-agentic-platform/tasks/private.jsonl"
DEFAULT_RESULTS = REPO / "04-agentic-platform/01-no-harness/runs/no-harness-results.jsonl"
DEFAULT_DIFFS_DIR = REPO / "04-agentic-platform/01-no-harness/runs/diffs"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


NOHARNESS = _load("no_harness", NO_HARNESS_PATH)
MINER = NOHARNESS.MINER
SCORING = NOHARNESS.SCORING

RETRY_PROMPT = """A test in this repository is failing. You already made one attempt to fix \
it, shown below -- it did not work. You get exactly one more attempt: no tools, no chance to \
run anything, no feedback beyond what is shown here, no further tries after this.

Test command:
    {command}

Original test failure output:
{failure}

Current contents of the file(s) that need the fix:

{context}

Your previous attempt (a unified diff):
{prior_diff}

What actually happened when that diff was tried:
{outcome}

Reply with ONLY a corrected unified diff (`--- a/path` / `+++ b/path` headers, applicable \
with `git apply`) that fixes the source. Do not include any explanation, and do not wrap the \
diff in a markdown code fence.

Rules:
- The diff may only touch the file(s) shown above.
- Do not touch anything under tests/ -- a diff that does is rejected outright, whatever it does.
"""


def apply_patch_verbose(work: Path, diff_text: str) -> tuple[bool, str]:
    """Same apply logic as stage 01's `apply_patch`, but returns the real
    `git apply` stderr instead of discarding it -- the retry prompt needs the
    actual error text, which stage 01 never had a reason to keep."""
    diff_text = NOHARNESS.extract_diff(diff_text)
    if not diff_text.strip():
        return False, "(the previous attempt produced an empty diff)"
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as fh:
        fh.write(diff_text)
        patch_path = Path(fh.name)
    try:
        last_stderr = ""
        for strip_level in ("-p1", "-p0"):
            proc = subprocess.run(
                ["git", "apply", strip_level, "--whitespace=nowarn", str(patch_path)],
                cwd=work, capture_output=True, text=True, check=False,
            )
            if proc.returncode == 0:
                return True, ""
            last_stderr = proc.stderr
        return False, last_stderr
    finally:
        patch_path.unlink(missing_ok=True)


def _manifest_task_order(manifest_path: Path) -> list[str]:
    order: list[str] = []
    for line in manifest_path.read_text().splitlines():
        if not line.strip():
            continue
        tid = json.loads(line)["task_id"]
        if tid not in order:
            order.append(tid)
    return order


def select_candidates(
    results_path: Path, diffs_dir: Path, manifest_path: Path
) -> list[dict]:
    """Every stage-01 attempt that (a) did not resolve, (b) is not a timeout
    (no diff was ever produced), and (c) has a recorded diff file on disk.

    The JSONL does not store which repeat a record came from, so the run
    index is reconstructed from record order: stage 01's own loop is "for
    run_index: for task in manifest order", so the Nth record for a given
    model corresponds to run `N // len(tasks) + 1` and task
    `manifest_order[N % len(tasks)]` -- verified against the actual
    `runs/diffs/` filenames before relying on it here.
    """
    task_order = _manifest_task_order(manifest_path)
    records = [json.loads(line) for line in results_path.read_text().splitlines() if line]

    per_model_count: dict[str, int] = {}
    candidates = []
    for rec in records:
        model = rec["model"]
        i = per_model_count.get(model, 0)
        per_model_count[model] = i + 1
        run_index = i // len(task_order) + 1

        if rec["verdict"] != "target_still_failing":
            continue
        diff_path = diffs_dir / f"{rec['task_id']}-{model}-run{run_index}.diff"
        if not diff_path.exists():
            continue
        candidates.append({**rec, "run_index": run_index, "diff_path": diff_path})
    return candidates


@dataclass
class RetryAttempt:
    task_id: str
    model: str
    prior_run_index: int
    prior_verdict: str
    prior_patch_applied: bool
    outcome_kind: str  # "apply_error" | "test_still_failing"
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


def retry_attempt(
    candidate: dict,
    task: dict,
    model: str,
    timeout: float = 300.0,
    keep: Path | None = None,
) -> RetryAttempt:
    task_obj = MINER.Task(**task)
    prior_diff = candidate["diff_path"].read_text()
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

            # Re-derive the real outcome of the prior diff on this fresh
            # pre-patch tree, rather than trusting the JSONL's own summary --
            # the git-apply error text was never recorded anywhere, and
            # re-running gives one uniform procedure for all candidates,
            # whether the prior diff applied or not.
            prior_applied, apply_stderr = apply_patch_verbose(work, prior_diff)
            if prior_applied:
                _, prior_failure_text = SCORING.run_and_collect(target_cmd, work, junit)
                outcome_kind = "test_still_failing"
                outcome_text = (
                    "The diff applied, but the target test command still failed:\n"
                    f"{prior_failure_text[-4000:]}"
                )
                # Reset to base state: the retry asks for one corrected diff
                # against the original file, not a second patch on top of the
                # first, so "current contents" below must be pre-patch.
                MINER.cleanup(work)
                MINER.materialize(task_obj, work)
            else:
                outcome_kind = "apply_error"
                outcome_text = f"`git apply` rejected this diff:\n{apply_stderr}"

            context = NOHARNESS.read_source_context(work, task_obj.source_files)
            prompt = RETRY_PROMPT.format(
                command=" ".join(task_obj.test_command),
                failure=failure,
                context=context,
                prior_diff=prior_diff,
                outcome=outcome_text,
            )
            body = NOHARNESS.invoke(prompt, work, model, timeout)

            if body.get("timed_out"):
                return RetryAttempt(
                    task_id=task_obj.task_id,
                    model=model,
                    prior_run_index=candidate["run_index"],
                    prior_verdict=candidate["verdict"],
                    prior_patch_applied=candidate["patch_applied"],
                    outcome_kind=outcome_kind,
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
            patch_applied = NOHARNESS.apply_patch(work, diff_text) if diff_text.strip() else False

            changed = SCORING.changed_paths(work)
            target_after, _ = SCORING.run_and_collect(target_cmd, work, junit)
            suite_after, _ = SCORING.run_and_collect(suite_cmd, work, junit)
            verdict = SCORING.score(
                task_obj.task_id, changed, target_before, target_after, suite_before, suite_after
            )
            if keep is not None:
                (keep / f"{task_obj.task_id}-{model}-run{candidate['run_index']}-retry.diff").write_text(
                    diff_text
                )

            usage = body.get("usage") or {}
            return RetryAttempt(
                task_id=verdict.task_id,
                model=model,
                prior_run_index=candidate["run_index"],
                prior_verdict=candidate["verdict"],
                prior_patch_applied=candidate["patch_applied"],
                outcome_kind=outcome_kind,
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
    ap.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    ap.add_argument("--diffs-dir", type=Path, default=DEFAULT_DIFFS_DIR)
    ap.add_argument("--model", help="restrict to one model: haiku | sonnet | opus")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--out", type=Path, help="append one JSON line per attempt")
    ap.add_argument("--keep-diffs", type=Path, help="directory to write each corrected diff into")
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

    tasks_by_id = {
        t["task_id"]: t
        for t in (json.loads(x) for x in args.manifest.read_text().splitlines() if x)
    }
    candidates = select_candidates(args.results, args.diffs_dir, args.manifest)
    if args.model:
        candidates = [c for c in candidates if c["model"] == args.model]

    if args.out and args.out.exists():
        done = {
            (r["model"], r["task_id"], r["prior_run_index"])
            for r in (json.loads(x) for x in args.out.read_text().splitlines() if x)
        }
        candidates = [
            c for c in candidates if (c["model"], c["task_id"], c["run_index"]) not in done
        ]

    spent = args.already_spent
    for candidate in candidates:
        if args.ceiling is not None and spent >= args.ceiling:
            print(f"CEILING_EXCEEDED: spent ${spent:.4f} >= ceiling ${args.ceiling:.2f}, stopping")
            return
        record = retry_attempt(
            candidate,
            tasks_by_id[candidate["task_id"]],
            candidate["model"],
            timeout=args.timeout,
            keep=args.keep_diffs,
        )
        spent += record.cost_usd
        print(
            f"{record.model:<7} {record.task_id}  run{record.prior_run_index}  "
            f"prior={record.prior_verdict}/{record.outcome_kind}  ->  "
            f"{record.verdict:<22} {record.wall_clock_s}s  ${record.cost_usd:.4f}"
        )
        if record.tampered:
            print(f"  GUARDRAIL FIRED: patch touched {record.tampered}")
        if record.cli_error:
            print(f"  cli error: {record.cli_error[:200]}")
        if args.out:
            with args.out.open("a") as fh:
                fh.write(json.dumps(asdict(record)) + "\n")

    print(
        f"\ntotal list-price equivalent this run: ${spent - args.already_spent:.4f} "
        f"over {len(candidates)} retry attempts (cumulative ${spent:.4f})"
    )


if __name__ == "__main__":
    main()
