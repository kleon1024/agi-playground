"""The blind call, read: per-tier resolve and the cost of one success.

Stage 01's recorded matrix (no-harness-results.jsonl, 18 attempts) is the
control for the whole mission: one blind call per task, no tools, no
feedback, no retry. This script reads the recorded JSONL and lays out what
the baseline actually costs per tier — including the reading that a
lower-resolving arm can still cost more per success, and which tiers never
resolved at all.

Input (recorded, unchanged): ../runs/no-harness-results.jsonl

Run:
    uv run python core/blind_call_read.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    rows = [
        json.loads(line)
        for line in (
            Path(__file__).resolve().parents[2] / "runs" / "no-harness-results.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]
    per_tier: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_tier[r["model"]].append(r)

    print("no-harness (one blind call), read per tier:")
    for tier, attempts in sorted(per_tier.items()):
        resolved = sum(1 for a in attempts if a["resolved"])
        cost = sum(a["cost_usd"] for a in attempts)
        cost_per = cost / resolved if resolved else float("nan")
        print(
            f"  {tier:<7} {resolved:>1}/{len(attempts)} resolved"
            f"  ${cost:>6.2f} total"
            f"  ${cost_per:>6.2f}/resolved" if resolved else
            f"  {tier:<7} {resolved:>1}/{len(attempts)} resolved"
            f"  ${cost:>6.2f} total  (never resolved)"
        )
    print("\nreading: the loop is worth nothing if a blind call does the job,")
    print("and worth everything where it cannot — resolve, not cost per")
    print("attempt, is the number the mission turns on.")


if __name__ == "__main__":
    main()
