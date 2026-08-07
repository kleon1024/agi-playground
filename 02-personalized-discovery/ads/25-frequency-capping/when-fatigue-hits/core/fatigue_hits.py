"""Fatigue, read: the same ad loses its click value.

Stage 25's decay curve is ad fatigue. This script reads the aggregate
loss of uncapped delivery over a week.

Run:
    uv run python core/fatigue_hits.py
"""

from __future__ import annotations


def main() -> None:
    impressions = 1_000_000
    # Capped at 3 per user: ctrs 0.05, 0.04, 0.03.
    capped_ctr = (0.05 + 0.04 + 0.03) / 3
    # Uncapped: the same users see 7, ctr decays to 0.002.
    uncapped_ctr = (0.05 + 0.04 + 0.03 + 0.02 + 0.01 + 0.005 + 0.002) / 7
    capped_clicks = impressions * capped_ctr
    uncapped_clicks = impressions * uncapped_ctr
    print("fatigue, read (1,000,000 impressions):")
    print(f"  capped at 3:  {capped_clicks:,.0f} expected clicks")
    print(f"  uncapped:     {uncapped_clicks:,.0f} expected clicks")
    print(f"  lost to fatigue: {capped_clicks - uncapped_clicks:,.0f}")
    print("\nreading: more impressions do not buy more clicks once fatigue")
    print("sets in — the uncapped run wastes the same budget for fewer")
    print("clicks. Fatigue is why the cap exists: it concentrates delivery")
    print("where the ad still earns its slot.")


if __name__ == "__main__":
    main()
