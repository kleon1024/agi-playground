"""The diff that never applied, read from the recorded no-harness run.

Stage 01's baseline applies each blind call's diff with plain git apply,
no retry. The recorded JSONL holds per-attempt patch_applied flags. This
script reads the record and lays out the apply-vs-resolve relationship —
the first gate a blind call must pass.

Input (recorded, unchanged): ../runs/no-harness-results.jsonl

Run:
    uv run python core/apply_read.py
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
    print("no-harness diff application (recorded), read:")
    for tier, attempts in sorted(per_tier.items()):
        applied = sum(1 for a in attempts if a["patch_applied"])
        resolved = sum(1 for a in attempts if a["resolved"])
        print(f"  {tier:<7} {applied}/{len(attempts)} diffs applied, "
              f"{resolved}/{len(attempts)} resolved")
    print("\nreading: application is the first gate — a diff that does not")
    print("apply resolves nothing, and with no retry the gate is final.")


if __name__ == "__main__":
    main()
