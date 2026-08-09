"""The automate-versus-gate boundary, read from recorded mission-04 runs.

The chapter's question: when should an agent act on its own, and when must a
human gate it? This script reads the recorded arms and prints the routing
table a product decision needs: per tier and arm, resolve rate, cost per
delivered outcome, and the always-frontier versus cheap-with-loop spread.

Input (recorded, unchanged):
  01-no-harness/runs/no-harness-results.jsonl
  03-cheap-or-expensive/runs/2026-07-29-results.jsonl
  00-task-set/runs/public-haiku-3runs.jsonl
  06-closing-the-loop/runs/closing-the-loop-results.jsonl

Run:
    uv run python core/product_boundary.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load(rel: str) -> list[dict]:
    path = ROOT / rel
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


NO_HARNESS = load("04-agentic-platform/01-no-harness/runs/no-harness-results.jsonl")
HARNESS = load("04-agentic-platform/03-cheap-or-expensive/runs/2026-07-29-results.jsonl")
PUBLIC = load("04-agentic-platform/00-task-set/runs/public-haiku-3runs.jsonl")
CLOSING = load("04-agentic-platform/06-closing-the-loop/runs/closing-the-loop-results.jsonl")


def per_tier(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["model"], []).append(r)
    return out


def main() -> None:
    print("the automate-versus-gate routing table, from recorded runs:\n")
    print(f"{'arm / tier':<20}{'delivered':>11}{'$/delivered':>13}")
    for label, rows in [
        ("no-harness haiku", per_tier(NO_HARNESS)["haiku"]),
        ("no-harness sonnet", per_tier(NO_HARNESS)["sonnet"]),
        ("no-harness opus", per_tier(NO_HARNESS)["opus"]),
        ("harness haiku", per_tier(HARNESS)["haiku"]),
        ("harness sonnet", per_tier(HARNESS)["sonnet"]),
        ("harness opus", per_tier(HARNESS)["opus"]),
        ("public haiku", PUBLIC),
        ("closing-loop pool", CLOSING),
    ]:
        n = len(rows)
        delivered = sum(1 for r in rows if r["resolved"])
        cost = sum(r["cost_usd"] for r in rows)
        per_delivered = cost / delivered if delivered else float("nan")
        print(f"{label:<20}{delivered:>5}/{n:<5}{per_delivered:>13.4f}")

    all_rows = NO_HARNESS + HARNESS + PUBLIC
    total = sum(r["cost_usd"] for r in all_rows)
    print(f"\ntotal recorded spend across the {len(all_rows)} real attempts: "
          f"${total:.4f}")
    retry = sum(1 for r in CLOSING if r["resolved"])
    print(f"feedback-only slice (no tools): {retry}/12 retries resolved")

    print("\nreading: automate the cell where the loop verifies and the price")
    print("clears; gate the cell where delivery is irreversible or the margin")
    print("sits inside the run-to-run spread. The routing table is the product.")


if __name__ == "__main__":
    main()
