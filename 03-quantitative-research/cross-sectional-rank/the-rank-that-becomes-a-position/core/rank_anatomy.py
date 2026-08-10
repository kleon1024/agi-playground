"""The rank-to-position anatomy: the same signal, four sizing rules.

The cross-sectional rank model is not one formula; it is a pipeline —
signal, cross-sectional rank, weight, position — and the sizing rule is
where the strategy lives. This script reads the recorded stage-02 run and
lays out the four rules it measured on the same signal family, so the
anatomy is a table of what each rule's "belief" does to concentration,
turnover, and the cap.

Input (recorded, unchanged): ../runs/2026-07-27-core-cross-sectional-rank.md

Run:
    uv run python core/rank_anatomy.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-27-core-cross-sectional-rank.md"
    ).read_text()
    print("cross-sectional rank anatomy (recorded stage-02 run), read:")
    print(f"  {'rule':<20} {'HHI':>7} {'turnover':>9} {'Sharpe':>7} "
          f"{'constrained gross':>18} {'violations':>11}")
    for row in re.findall(
        r"\| ([\w-]+(?: [\w-]+)*) \| ([\d.]+) \| ([\d.]+) \| ([\d.-]+) \|",
        run,
    ):
        name, hhi, turnover, sharpe = row
        print(f"  {name:<20} {float(hhi):>7.4f} {float(turnover):>9.3f} "
              f"{float(sharpe):>7.2f}")
    gross = re.findall(
        r"gross exposure was ([\d.]+), ([\d.]+), ([\d.]+), and ([\d.]+)",
        run,
    )
    if gross:
        print(f"  gross after naive cap then sector de-mean: {list(gross[0])}")
    viol = re.findall(r"left (\d+), (\d+), (\d+), and (\d+) positions above", run)
    if viol:
        print(f"  cap violations: {list(viol[0])}")
    print("\nreading: the signal is fixed and the rule changes the portfolio —")
    print("equal-weight concentrates on the tails, rank-proportional spreads")
    print("across the full order, and every rule breaks the cap, which is why")
    print("a joint constrained optimizer is necessary.")


if __name__ == "__main__":
    main()
