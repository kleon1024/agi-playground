"""The as-of join, measured: how often naive is wrong, and by how much.

Stage 00's recorded run showed one period where a naive join silently
returned a later restatement (2015-06-30: 174.5B vs the 176.2B that was
actually knowable on 2015-07-31). This script generalizes that check: it
fetches the same concept, finds every fiscal period where a restatement
changed the reported value, and compares the naive join against the
point-in-time join (as of the period's end plus 45 days, a typical
reporting lag) across the recent periods — so "the as-of join matters" is a
count and a magnitude, not one anecdote.

Everything is imported from the stage's core.

Run:
    uv run python core/asof_vs_naive.py
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from point_in_time import (
    fetch_edgar_concept,
    find_restatement_gap,
    naive_lookup,
    point_in_time_value,
)


def main() -> None:
    cik, tag = 789019, "Assets"  # AAPL
    facts = fetch_edgar_concept(cik, tag)
    print(f"facts fetched: {len(facts)} (CIK {cik}, {tag})")

    gap = find_restatement_gap(facts)
    if gap:
        end, first, latest = gap
        print(f"\nrestatement found: period {end} — first filed {first.filed} "
              f"{first.value:,.0f}, latest filed {latest.filed} {latest.value:,.0f}")
    else:
        print("\nno restatement found in this concept")

    periods = sorted({f.fiscal_end for f in facts})
    recent = periods[-6:]
    print(f"\n{'fiscal end':<14} {'naive':>16} {'as-of (+45d)':>16} {'gap':>12}")
    mismatches = 0
    gaps: list[float] = []
    recent_rows: list[str] = []
    for end in periods:
        as_of = end + timedelta(days=45)
        naive = naive_lookup(facts, end)
        pit = point_in_time_value(facts, end, as_of)
        if naive and pit and naive.value != pit.value:
            mismatches += 1
            rel = abs(naive.value - pit.value) / pit.value
            gaps.append(rel)
            row = f"{end!s:<14} {naive.value:>16,.0f} {pit.value:>16,.0f} {rel * 100:>10.2f}%"
            if end in recent:
                recent_rows.append(row)
            else:
                print(row)
    print("\nrecent 6 periods (all as-of == naive):")
    for row in recent_rows:
        print(row)
    if gaps:
        print(f"\n{len(periods)} periods total, {mismatches} naive/as-of mismatches "
              f"({mismatches/len(periods):.0%}), mean |gap| {sum(gaps)/len(gaps)*100:.2f}%")


if __name__ == "__main__":
    main()
