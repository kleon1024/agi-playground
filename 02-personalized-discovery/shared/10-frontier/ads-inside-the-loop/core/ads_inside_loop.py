"""Ads inside the answer loop, read from the recorded ads runs.

The chapter's question: when the ad becomes a step in the answer thread,
what survives of the auction? This script reads three committed records --
the ad-externality displacement model, the value-tree auction entry, and
the budget-pacing delivery simulation -- and prints the displacement table
and pacing contrast the argument rests on.

Input (recorded, unchanged):
  ads/18-ad-externality/runs/2026-08-06-ad-externality.md
  shared/05-value-tree/runs/2026-07-30-weight-sweep-and-auction.md
  ads/17-budget-pacing/runs/2026-08-06-budget-pacing.md

Run:
    uv run python core/ads_inside_loop.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

EXTERNALITY = (
    ROOT
    / "02-personalized-discovery/ads/18-ad-externality/"
    "runs/2026-08-06-ad-externality.md"
)
VALUE_TREE = (
    ROOT
    / "02-personalized-discovery/shared/05-value-tree/"
    "runs/2026-07-30-weight-sweep-and-auction.md"
)
PACING = (
    ROOT
    / "02-personalized-discovery/ads/17-budget-pacing/"
    "runs/2026-08-06-budget-pacing.md"
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
    ext = EXTERNALITY.read_text()
    vt = VALUE_TREE.read_text()
    pace = PACING.read_text()

    rows = []
    for m in re.finditer(
        r"^\s*(\d+) ad\(s\):.*displaced ([\d.]+), ad value ([\d.]+)", ext, re.MULTILINE
    ):
        rows.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
    trade_enter = grab_many(
        r"trade_rate=(\d+\.\d+): ad enters, displaces ([\w_]+) \(organic value ([\d.]+)\)",
        vt,
        "entering trade rate",
    )
    naive_hour = grab(r"naive exhausts at hour (\d+)", pace, "naive exhaustion")
    paced = grab_many(
        r"paced survives the day: ([\d.]+) spent, ([\d.]+) unused",
        pace,
        "paced delivery",
    )

    print("ads inside the answer loop, read from the recorded ads runs:\n")
    print(f"{'ads':>3}{'organic displaced':>19}{'ad value':>11}{'net':>9}")
    for n, displaced, value in rows:
        print(f"{n:>3}{displaced:>18.1f}{value:>11.1f}{value - displaced:>9.1f}")
    print(f"\nauction entry: the ad clears only at trade_rate={trade_enter[0]}, displacing")
    print(f"{trade_enter[1]} (organic value {trade_enter[2]})")
    print(f"\npacing: naive delivery exhausts the budget at hour {naive_hour};")
    print(f"paced delivery survives the day ({paced[0]} spent, {paced[1]} unused)")
    print("\nreading: the auction and its budget machinery survive inside the")
    print("answer thread -- what changes is the surface the ad sits in and")
    print("the event that counts as a conversion. Displacement is still the")
    print("price of entry, and the value tree is still where the platform")
    print("decides how much organic it may displace.")


if __name__ == "__main__":
    main()
