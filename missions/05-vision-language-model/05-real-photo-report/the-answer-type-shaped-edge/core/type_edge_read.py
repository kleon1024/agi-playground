"""The answer-type-shaped edge, read from the recorded API log.

Stage 05's report found the hosted API's edge is answer-type-shaped: 63.7%
on yes/no, 24.0% on number questions. This script reads the recorded raw
log and recomputes the per-type split, so the shape is the log's own
numbers, not the report's prose.

Input (recorded, unchanged): ../runs/hosted-api-raw.jsonl

Run:
    uv run python core/type_edge_read.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    rows = [
        json.loads(line)
        for line in (
            Path(__file__).resolve().parents[2] / "runs" / "hosted-api-raw.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]
    by_type: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        atype = r.get("type") or "other"
        pred = (r.get("pred_raw") or "").strip().lower()
        ans = (r.get("answer") or "").strip().lower()
        by_type[atype].append(1 if pred == ans else 0)
    print("hosted API accuracy by answer type (recomputed from the log), read:")
    for atype, results in sorted(by_type.items()):
        print(f"  {atype:<10} {sum(results)}/{len(results)} "
              f"({sum(results)/len(results):.3f})")
    print("\nreading: the API is strongest on the easiest type (yes/no) and")
    print("weakest where counting is required (number) — the type split is")
    print("where a future build could compete instead of head-on.")


if __name__ == "__main__":
    main()
