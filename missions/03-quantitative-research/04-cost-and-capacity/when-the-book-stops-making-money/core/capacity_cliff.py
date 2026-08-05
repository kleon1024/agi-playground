"""The capacity curve, measured: where the book stops making money.

Stage 04's recorded run reports one point on the capacity curve (at a
10m book) plus the discrete-sweep peak and breakeven. This script sweeps the
book size across the full log range on the same measured inputs (real ADV
and volatility) and the same declared assumptions, so the curve — net
dollar return rising, peaking, falling, turning negative — is laid out
instead of summarized.

Run:
    uv run python core/capacity_cliff.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from cost_capacity import (
    IMPACT_COEFFICIENT_Y,
    average_daily_dollar_volume,
    capacity_curve,
    fetch_daily_bars,
    find_capacity,
    realized_daily_vol,
)


def main() -> None:
    closes, volumes = fetch_daily_bars("AAPL", "2y")
    adv = average_daily_dollar_volume(closes, volumes)
    vol = realized_daily_vol(closes)
    gross, turnover = 0.12, 6.0
    print(f"measured inputs: ADV ${adv/1e9:.2f}B, daily vol {vol*100:.2f}% "
          f"(assumptions: Y={IMPACT_COEFFICIENT_Y}, gross {gross:.0%}, turnover {turnover})")

    book_sizes = [10 ** (7 + i * 0.25) for i in range(17)]  # 10m .. ~1e11
    curve = capacity_curve(gross, turnover, adv, vol, book_sizes)
    print(f"\n{'book':>14} {'participation':>13} {'annual cost':>12} {'net pct':>9} {'net dollar':>14}")
    for row in curve:
        print(
            f"{row['book_size']:>14,.0f} {row['participation_rate']*100:>12.4f}% "
            f"{row['annual_cost_frac']*100:>11.4f}% {row['net_return_pct']*100:>8.3f}% "
            f"{row['net_dollar_return']:>14,.0f}"
        )

    cap = find_capacity(curve)
    print(f"\npeak book (max net dollar return): ${cap['peak_book_size']/1e9:.1f}B")
    print(f"breakeven (net return turns negative): ${cap['breakeven_book_size']/1e9:.1f}B")


if __name__ == "__main__":
    main()
