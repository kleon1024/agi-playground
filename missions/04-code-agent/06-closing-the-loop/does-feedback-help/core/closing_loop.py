"""Does seeing the real outcome help? The closing-the-loop results, read.

Stage 06 gives the agent one retry turn with its prior attempt's real test
outcome and no tools. Its recorded run kept 12 attempts; this script reads
the log and lays out the comparison the stage's question needs: how many
retries resolved, how the prior verdict and prior patch status predict the
retry, and what the feedback cost.

Input (recorded, unchanged): ../runs/closing-the-loop-results.jsonl

Run:
    uv run python core/closing_loop.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[2] / "runs" / "closing-the-loop-results.jsonl"
    with open(path) as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    verdicts = Counter(r["verdict"] for r in rows)
    resolved = [r for r in rows if r["resolved"]]
    applied = sum(1 for r in rows if r.get("patch_applied"))
    prior_verdicts = Counter(r.get("prior_verdict") for r in rows)
    resolved_prior = [(r.get("prior_verdict"), r.get("prior_patch_applied")) for r in resolved]
    costs = [r.get("cost_usd", 0.0) for r in rows]

    print(f"{len(rows)} closing-the-loop attempts (haiku 6, sonnet 3, opus 3)")
    print(f"  verdicts: {dict(verdicts)}")
    print(f"  resolved: {len(resolved)}/{len(rows)}, patch applied: {applied}/{len(rows)}")
    print(f"  prior verdicts: {dict(prior_verdicts)}")
    print(f"  resolved attempts' prior state: {resolved_prior}")
    print(f"  cost: ${sum(costs):.3f} total, ${sum(costs)/len(costs):.4f} mean")


if __name__ == "__main__":
    main()
