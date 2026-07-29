"""Run a task through Claude Code headlessly, and score it the same way.

The scorer does not care what produced the diff. That is the property this file
exploits: a production coding agent gets the same task, the same guardrail, and
the same three checks as the from-scratch harness next to it, so the comparison
is between harnesses rather than between measurement methods.

It also solves the cost problem. `claude -p --output-format json` reports
`total_cost_usd` and full token usage per invocation. On a subscription that
figure is the list-price equivalent rather than money charged, and every
`runs/` entry says so -- but it is measured, not estimated, and it is per
attempt.

Three things are forced, and each closes a way the number could be wrong:

**No network.** `WebSearch` and `WebFetch` are disallowed. Every task here is a
public commit in a public repository, and an agent that fetches the upstream
fix has demonstrated retrieval, not repair.

**No history.** Handled upstream by `mine_history.materialize`, which exports a
one-commit repository. Without it `git log --all` inside the task lists the fix
commit with a subject line describing the bug.

**No test edits are prevented -- only scored.** Claude Code is given write
access to the whole task tree, tests included. A guardrail that blocks the
behaviour cannot measure it.

Run:
    python claude_arm.py --model haiku
    python claude_arm.py --model opus --task-id private-b81c414 --out arm.jsonl
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import scoring
from run_task import DEFAULT_MANIFEST, MINER, PROMPT

# Read-only tools plus the two that change files. The web tools are absent by
# construction and denied explicitly below, because "absent from the allow
# list" and "denied" are not the same guarantee if the allow list is ever
# widened by accident.
ALLOWED_TOOLS = ["Read", "Glob", "Grep", "Bash", "Edit", "Write"]
DENIED_TOOLS = ["WebSearch", "WebFetch"]


@dataclass
class ClaudeAttempt:
    task_id: str
    model: str
    verdict: str
    resolved: bool
    turns: int
    wall_clock_s: float
    cost_usd: float
    input_tokens: int
    output_tokens: int
    changed: list[str]
    tampered: list[str]
    regressions: list[str]
    target_failing_after: list[str]
    cli_error: str | None = None


def invoke(prompt: str, work: Path, model: str, timeout: float) -> dict:
    """One headless Claude Code run inside the task directory."""
    command = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        *ALLOWED_TOOLS,
        "--disallowedTools",
        *DENIED_TOOLS,
    ]
    proc = subprocess.run(
        command, cwd=work, capture_output=True, text=True, timeout=timeout, check=False
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"is_error": True, "result": (proc.stdout + proc.stderr)[-2000:]}


def attempt(
    task: dict, model: str, timeout: float = 900.0, keep: Path | None = None, tag: str = ""
) -> ClaudeAttempt:
    task_obj = MINER.Task(**task)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "task"
        junit = Path(tmp) / "out.xml"
        MINER.materialize(task_obj, work)
        try:
            target_cmd = scoring.instrument(task_obj.test_command, junit)
            suite_cmd = scoring.instrument(task_obj.test_command, junit, targets=["tests"])

            target_before, failure = scoring.run_and_collect(target_cmd, work, junit)
            if not target_before or not any(
                s in ("failure", "error") for s in target_before.values()
            ):
                raise SystemExit(
                    f"{task_obj.task_id}: target tests do not fail at base state; "
                    f"the manifest is stale or the environment cannot run them.\n{failure[-1500:]}"
                )
            suite_before, _ = scoring.run_and_collect(suite_cmd, work, junit)

            body = invoke(
                PROMPT.format(command=" ".join(task_obj.test_command), failure=failure),
                work,
                model,
                timeout,
            )

            changed = scoring.changed_paths(work)
            target_after, _ = scoring.run_and_collect(target_cmd, work, junit)
            suite_after, _ = scoring.run_and_collect(suite_cmd, work, junit)
            verdict = scoring.score(
                task_obj.task_id, changed, target_before, target_after, suite_before, suite_after
            )
            if keep is not None:
                # The patch itself, kept because a resolve rate with no diffs
                # behind it is a claim about work nobody looked at.
                # `-N` registers new files as intent-to-add so `git diff` shows
                # them; a plain diff omits untracked files entirely, which is
                # exactly where a fabricated test would hide.
                subprocess.run(
                    ["git", "add", "-A", "-N"], cwd=work, capture_output=True, check=False
                )
                (keep / f"{task_obj.task_id}-{model}{tag}.diff").write_text(
                    subprocess.run(
                        ["git", "diff"], cwd=work, capture_output=True, text=True, check=False
                    ).stdout
                )
            usage = body.get("usage") or {}
            return ClaudeAttempt(
                task_id=verdict.task_id,
                model=model,
                verdict=verdict.verdict,
                resolved=verdict.resolved,
                turns=body.get("num_turns", 0),
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
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--out", type=Path, help="append one JSON line per attempt")
    ap.add_argument("--keep-diffs", type=Path, help="directory to write each produced diff into")
    args = ap.parse_args()
    if args.keep_diffs:
        args.keep_diffs.mkdir(parents=True, exist_ok=True)

    tasks = [json.loads(x) for x in args.manifest.read_text().splitlines() if x]
    if args.task_id:
        tasks = [t for t in tasks if t["task_id"] == args.task_id]
        if not tasks:
            raise SystemExit(f"no task {args.task_id!r} in {args.manifest}")

    spent = 0.0
    for run_index in range(1, args.repeats + 1):
        for task in tasks:
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
                f"{record.model}  {record.turns} turns  {record.wall_clock_s}s  "
                f"${record.cost_usd:.4f}"
            )
            if record.tampered:
                print(f"  GUARDRAIL FIRED: patch touched {record.tampered}")
            if record.cli_error:
                print(f"  cli error: {record.cli_error[:200]}")
            if args.out:
                with args.out.open("a") as fh:
                    fh.write(json.dumps(asdict(record)) + "\n")
    print(f"\ntotal list-price equivalent: ${spent:.4f} over {len(tasks) * args.repeats} attempts")


if __name__ == "__main__":
    main()
