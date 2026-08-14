"""A deterministic orchestrator dispatching the mission's real tasks.

The orchestration stage claims structured work belongs in a deterministic
skeleton with LLM cells, not free multi-agent conversation. This file is
the skeleton half, made concrete: an orchestrator with a fixed dispatch
plan over the mission's task set, workers that each own one bounded
check, and a summary record. The workers are deterministic checks (task
record completeness, test-file presence) so the demo isolates the
orchestration mechanics from model quality.

The point is not the checks — it is that every step has an owner, an
input, an output, and a place in the record. That is the skeleton the
stage argues production workflows need before any model fills a cell.

Run:
    python orchestrator.py --tasks ../../../tasks/private.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def worker_check_task_record(task: dict) -> dict:
    """Worker 1: every field the mission contract needs must be present."""
    required = {"task_id", "subject", "source_files", "target_tests", "test_command"}
    missing = sorted(required - set(task))
    return {"worker": "task-record", "task": task["task_id"],
            "ok": not missing, "detail": f"missing={missing}" if missing else "complete"}


def worker_check_verification(task: dict) -> dict:
    """Worker 2: the verification contract must be executable on paper."""
    problems = []
    if not task.get("target_tests"):
        problems.append("no target_tests")
    if not task.get("test_command"):
        problems.append("no test_command")
    if not task.get("subject"):
        problems.append("no subject")
    return {"worker": "verification-contract", "task": task["task_id"],
            "ok": not problems, "detail": "; ".join(problems) if problems else "executable"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", required=True)
    args = ap.parse_args()

    tasks = [json.loads(l) for l in Path(args.tasks).read_text().splitlines() if l.strip()]
    tasks_dir = Path(args.tasks).parent

    started = time.monotonic()
    results = []
    for task in tasks:
        # deterministic dispatch: two workers, both owned, both recorded
        r1 = worker_check_task_record(task)
        r2 = worker_check_verification(task)
        results.append({"task_id": task["task_id"], "workers": [r1, r2],
                        "passed": all(r["ok"] for r in (r1, r2))})

    for row in results:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"[{status}] {row['task_id']}: " +
              "; ".join(f"{w['worker']}={w['ok']}" for w in row["workers"]))

    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} tasks passed all deterministic gates in "
          f"{round(time.monotonic() - started, 3)}s; no model called.")
    print("The skeleton is the record: every step has an owner, input, output, "
          "and a place in the summary — the shape an LLM cell would fill.")


if __name__ == "__main__":
    main()
