"""Verification replacing score, read from the recorded ranking runs.

The chapter's question: when the system generates the answer instead of
ranking the list, which mechanisms persist? This script reads two committed
records -- the LLM listwise-ranking run and the value-tree weight sweep --
and prints the two measured facts the argument rests on: the LLM ranker
reorders without a check, and a calibration break reorders the ranking with
no product-strategy change.

Input (recorded, unchanged):
  recommendation/31-llm-ranking/runs/2026-08-07-llm-ranking.md
  shared/05-value-tree/runs/2026-07-30-weight-sweep-and-auction.md

Run:
    uv run python core/verification_replaces_score.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

LLM_RANK = (
    ROOT
    / "02-personalized-discovery/llm-ranking/"
    "runs/2026-08-07-llm-ranking.md"
)
VALUE_TREE = (
    ROOT
    / "02-personalized-discovery/value-tree/"
    "runs/2026-07-30-weight-sweep-and-auction.md"
)


def grab(pattern: str, text: str, label: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.group(1)


def grab_many(pattern: str, text: str, label: str) -> tuple[str, ...]:
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.groups()


def main() -> None:
    llm = LLM_RANK.read_text()
    vt = VALUE_TREE.read_text()

    changed = grab(r"positions changed:\s*(\d+/\d+)", llm, "positions changed")
    llm_cost = grab(r"The frontier cost is (.*?)\.", llm, "llm frontier cost")
    inflate = grab(r"click predictions inflated ([\d.]+x)", vt, "calibration inflation")
    order_line = grab(r"(order changed.*)", vt, "calibration reorder")
    trade_low = grab_many(
        r"trade_rate=(\d+\.\d+): ad utility ([\d.]+), does not clear", vt, "low trade rate"
    )
    trade_enter = grab_many(
        r"trade_rate=([\d.]+): ad enters, displaces ([\w_]+) \(organic value ([\d.]+)\)",
        vt,
        "entering trade rate",
    )

    print("verification replacing score, read from the recorded ranking runs:\n")
    print(f"LLM listwise reorder: {changed} positions changed -- a reorder with no")
    print(f"check against the pointwise order; the recorded cost is '{llm_cost}'.")
    print(f"\ncalibration break: click predictions inflated {inflate} reorders the")
    print(f"ranking -- {order_line}")
    print(f"\nvalue-tree auction: at trade_rate={trade_low[0]} the ad does not clear;")
    print(f"at trade_rate={trade_enter[0]} it enters and displaces {trade_enter[1]} "
          f"(organic value {trade_enter[2]})")
    print("\nreading: the ranked list does not disappear -- it becomes the")
    print("retrieval input a generator conditions on. What becomes load-bearing")
    print("is the verification step: a reorder without a check and a")
    print("miscalibration that silently reorders are the failures the surface")
    print("must catch before the generated answer is shown.")


if __name__ == "__main__":
    main()
