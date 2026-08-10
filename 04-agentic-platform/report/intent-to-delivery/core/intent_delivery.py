"""The intent-to-delivery gap, read from the recorded mission-04 arms.

The chapter's question: where does a stakeholder intent stop being delivered?
This script reads the three recorded arms -- no-harness (18 blind calls), the
full harness (18 tool-loop attempts), and closing-the-loop (12 retries with
outcome feedback and still no tools) -- and prints, per arm and per tier, how
many attempts produced a deliverable at all and how many were delivered
(scored resolved).

Input (recorded, unchanged):
  01-no-harness/runs/no-harness-results.jsonl
  03-cheap-or-expensive/runs/2026-07-29-results.jsonl
  06-closing-the-loop/runs/closing-the-loop-results.jsonl

Run:
    uv run python core/intent_delivery.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(rel: str) -> list[dict]:
    path = ROOT / rel
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


NO_HARNESS = load("04-agentic-platform/no-harness/runs/no-harness-results.jsonl")
HARNESS = load("04-agentic-platform/cheap-or-expensive/runs/2026-07-29-results.jsonl")
CLOSING = load("04-agentic-platform/closing-the-loop/runs/closing-the-loop-results.jsonl")


def summarize(rows: list[dict], arm: str) -> None:
    n = len(rows)
    resolved = sum(1 for r in rows if r["resolved"])
    # The harness log has no patch_applied column: a resolved attempt is the
    # scored deliverable. The blind and retry logs record patch_applied, which
    # is the narrower claim (a deliverable exists at all).
    produced = sum(
        1 for r in rows if r.get("patch_applied", r["resolved"])
    )
    cost = sum(r["cost_usd"] for r in rows)
    wall = sum(r["wall_clock_s"] for r in rows)
    print(f"{arm}: {n} attempts, {produced}/{n} produced a deliverable, "
          f"{resolved}/{n} delivered; cost ${cost:.3f} total, "
          f"{wall:.0f}s wall-clock")
    per_tier: dict[str, list[dict]] = {}
    for r in rows:
        per_tier.setdefault(r["model"], []).append(r)
    for tier in sorted(per_tier):
        tr = per_tier[tier]
        t_res = sum(1 for r in tr if r["resolved"])
        t_cost = sum(r["cost_usd"] for r in tr)
        per_delivered = t_cost / t_res if t_res else float("nan")
        print(f"  {tier:<7} {t_res}/{len(tr)} delivered, "
              f"${per_delivered:.4f}/delivered")


def main() -> None:
    print("intent-to-delivery, read from the recorded mission-04 arms:\n")
    summarize(NO_HARNESS, "no-harness (blind call)")
    summarize(HARNESS, "full harness (tool loop)")
    summarize(CLOSING, "closing-the-loop (feedback, no tools)")

    nh = NO_HARNESS
    blind_delivered = sum(1 for r in nh if r["resolved"])
    blind_produced = sum(1 for r in nh if r.get("patch_applied", False))
    blind_wasted = sum(r["cost_usd"] for r in nh if not r["resolved"])
    print("\nreading: intent is delivered only when the loop turns it into a")
    print("deliverable and verifies it. The blind call produced a patch-shaped")
    print(f"object in {blind_produced}/18 attempts but delivered {blind_delivered}/18;")
    print(f"${blind_wasted:.3f} was spent on attempts that never delivered.")


if __name__ == "__main__":
    main()
