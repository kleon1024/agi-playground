"""The bimodal retry, read from the recorded closing-the-loop run.

Stage 06's run gave every failed no-harness attempt one retry turn with
real outcome feedback. The recorded result is bimodal: either the diff
applied and the fix was correct, or it did not apply at all. This script
reads the JSONL and lays out the split.

Input (recorded, unchanged): ../runs/closing-the-loop-results.jsonl

Run:
    uv run python core/bimodal_read.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    rows = [
        json.loads(line)
        for line in (
            Path(__file__).resolve().parents[2]
            / "runs"
            / "closing-the-loop-results.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]
    per_tier: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_tier[r["model"]].append(r)
    print("retry-after-feedback (recorded), read:")
    for tier, attempts in sorted(per_tier.items()):
        applied = sum(1 for a in attempts if a.get("patch_applied"))
        resolved = sum(1 for a in attempts if a.get("resolved"))
        print(f"  {tier:<7} {len(attempts)} retried, {applied} diffs applied, "
              f"{resolved} resolved")
    print("\nreading: ten of twelve corrected diffs were rejected by git apply")
    print("the same way the first ones were — the retry is bimodal, and the")
    print("feedback did not fix the apply failure.")


if __name__ == "__main__":
    main()
