"""What the harness owns, read from the recorded mission-04 arms.

The chapter's question: what does the software around the model actually own?
This script reads the recorded no-harness, full-harness, public-set, and
closing-the-loop runs and prints, per arm and per tier, the columns a
control-plane audit needs: attempts, delivered, cost per delivered, mean
turns, mean tokens, and mean wall-clock.

Input (recorded, unchanged):
  01-no-harness/runs/no-harness-results.jsonl
  03-cheap-or-expensive/runs/2026-07-29-results.jsonl
  00-task-set/runs/public-haiku-3runs.jsonl
  06-closing-the-loop/runs/closing-the-loop-results.jsonl

Run:
    uv run python core/harness_anatomy.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(rel: str) -> list[dict]:
    path = ROOT / rel
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


ARMS = [
    ("no-harness", "04-agentic-platform/01-no-harness/runs/no-harness-results.jsonl"),
    ("harness (private)", "04-agentic-platform/03-cheap-or-expensive/runs/2026-07-29-results.jsonl"),
    ("harness (public)", "04-agentic-platform/00-task-set/runs/public-haiku-3runs.jsonl"),
    ("closing-the-loop", "04-agentic-platform/06-closing-the-loop/runs/closing-the-loop-results.jsonl"),
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def main() -> None:
    print("what the loop owns, read from the recorded mission-04 arms:\n")
    print(f"{'arm':<20}{'n':>4}{'delivered':>11}{'$/delivered':>12}"
          f"{'turns':>8}{'tokens':>9}{'wall s':>9}")
    for label, rel in ARMS:
        rows = load(rel)
        n = len(rows)
        delivered = sum(1 for r in rows if r["resolved"])
        cost = sum(r["cost_usd"] for r in rows)
        per_delivered = cost / delivered if delivered else float("nan")
        turns = mean([r["turns"] for r in rows if r.get("turns") is not None])
        tokens = mean([r["input_tokens"] + r["output_tokens"] for r in rows])
        wall = mean([r["wall_clock_s"] for r in rows])
        turns_s = f"{turns:>8.1f}" if not math.isnan(turns) else f"{'-':>8}"
        print(f"{label:<20}{n:>4}{delivered:>5}/{n:<5}"
              f"{per_delivered:>12.4f}{turns_s}{tokens:>9.0f}{wall:>9.1f}")

    closing = load(ARMS[3][1])
    retry_resolved = sum(1 for r in closing if r["resolved"])
    retry_applied = sum(1 for r in closing if r.get("patch_applied", False))
    print(f"\nreading: the loop owns delivery -- {retry_resolved}/12 retries")
    print(f"resolved with feedback but no tools, {retry_applied}/12 patches applied;")
    print("the control-plane columns above are what a harness audit must measure")
    print("before any claim about 'the model' is read from a score.")


if __name__ == "__main__":
    main()
