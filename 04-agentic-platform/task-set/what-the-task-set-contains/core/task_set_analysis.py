"""The task set as a funnel: commits -> candidates -> survivors -> resolves.

Stage 00's recorded runs mined two task sets — a private set from this
repository's history and a public set from more-itertools (2,423 commits).
The admission rule (fail at base, pass at gold) is the funnel's bottleneck:
2 of 6 public candidates survived. This script reads the recorded public
model-run log and lays out the last stage of the funnel — how many of the
surviving tasks a blind model call actually resolves — beside the recorded
mining counts.

Input (recorded, unchanged): ../runs/public-haiku-3runs.jsonl

Run:
    uv run python core/task_set_analysis.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[2] / "runs" / "public-haiku-3runs.jsonl"
    with open(path) as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    verdicts = Counter(r.get("verdict") for r in rows)
    resolved = sum(1 for r in rows if r.get("resolved"))
    costs = [r.get("cost_usd", 0.0) for r in rows]
    tasks = sorted({r["task_id"] for r in rows})
    print(f"public task set: {len(tasks)} tasks, {len(rows)} model attempts")
    print(f"  verdicts: {dict(verdicts)}")
    print(f"  resolved: {resolved}/{len(rows)}")
    print(f"  cost: ${sum(costs):.3f} total, ${sum(costs)/len(costs):.4f} mean")
    print("\nrecorded mining funnel (from the stage run records):")
    print("  more-itertools history: 2,423 commits; 6 candidates admitted;")
    print("  2 survived fail-at-base/pass-at-gold (0.08% of history)")


if __name__ == "__main__":
    main()
