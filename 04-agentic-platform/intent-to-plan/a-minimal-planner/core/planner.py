"""A minimal plan-as-contract generator, fed this mission's real tasks.

The intent-to-plan stage claims a plan is a contract: exact file paths,
exact structures, a test command, and a reviewable shape — before any tool
runs. This file turns the mission's mined task records into that contract.
It is deliberately rule-based: no model is called, so the demo isolates the
*shape* of a plan from the intelligence that fills one.

The contrast the stage cares about is between a vague instruction and a
plan. A task record already contains the grounded facts a plan needs
(`source_files`, `target_tests`, `test_command`, `subject`); the planner
just makes them explicit and checkable. The record proves that grounding
comes from discovery, not from asking the user.

Run:
    python planner.py --tasks ../../../tasks/private.jsonl
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Plan:
    task_id: str
    title: str
    files_to_change: list[str]
    tests_to_satisfy: list[str]
    verification: list[str]
    ground_truth: str


def build_plan(task: dict) -> Plan:
    """A plan is the task's grounded facts made explicit and checkable."""
    title = task.get("subject", "").split(": ", 1)[-1]
    return Plan(
        task_id=task["task_id"],
        title=title,
        files_to_change=task.get("source_files", []),
        tests_to_satisfy=task.get("target_tests", []),
        verification=task.get("test_command", []),
        ground_truth=task.get("commit", ""),
    )


def render(plan: Plan) -> str:
    """The plan as a human would review it before approving execution."""
    files = [f"- `{f}`" for f in plan.files_to_change] or ["- (none yet)"]
    tests = [f"- `{t}`" for t in plan.tests_to_satisfy] or ["- (none yet)"]
    lines = [
        f"# Plan: {plan.title}",
        "",
        f"**Task:** `{plan.task_id}`",
        "",
        "## Files to change",
        *files,
        "",
        "## Tests this must satisfy",
        *tests,
        "",
        "## Verification",
        f"```bash\n{' '.join(plan.verification)}\n```",
        "",
        "## What the plan does not claim",
        "- It does not claim the fix; the test decides that.",
        "- It does not claim the ground truth: that stays in the task record.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", required=True, help="path to a tasks/*.jsonl")
    ap.add_argument("--out", help="write plans as JSONL")
    args = ap.parse_args()

    tasks = [json.loads(line) for line in Path(args.tasks).read_text().splitlines() if line.strip()]
    plans = [build_plan(t) for t in tasks]

    for plan in plans:
        print(render(plan))
        print("=" * 40)
    print(
        f"{len(plans)} plans generated from {Path(args.tasks).name}; "
        "no model called; every field traces to a task record."
    )

    if args.out:
        with open(args.out, "w") as fh:
            for plan in plans:
                fh.write(json.dumps(asdict(plan), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
