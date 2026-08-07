# Run — the cap-tightness sweep

**Date:** 2026-08-07
**Command:** `uv run python core/pacing_sweep.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The stage run paces with cap = budget/hours. The audit asks the
case-finding question: how tight should that cap be? It sweeps a
multiplier on the cap over a front-loaded demand curve with an evening
burst (hours 9-10) and reports total spend, late-window spend (hours
9-11), and dark hours — hours with demand but no spend.

## Output

```
cap-tightness audit: budget 100, 12 hours, demand front-loaded
with an evening burst (hours 9-10). cap = multiplier x budget/hours

   mult   total  late 9-11  dark hrs
   0.50    50.0       12.5         0
   0.75    74.4       18.8         0
   1.00    97.3       25.0         0
   1.25   100.0       13.0         1
   1.50   100.0        0.0         3
   2.00   100.0        0.0         5
```

## Notes

- The trade is measured: at multiplier 0.50 the cap is so tight that half
  the budget is never spent (under-delivery, 50.0 of 100.0); at 1.50 and
  above the budget dies before the evening burst and late-window delivery
  collapses to 0.0 with 3-5 dark hours at the end of the day.
- The multiplier that spends the full budget with full evening presence
  is 1.25 here (100.0 total, 13.0 late, one dark hour) — but the choice
  depends on the demand shape, which is exactly why the cap is tuned
  against logged delivery, not fixed once.
- Late-window delivery is the monitoring metric that catches the loose
  cap: total spend looks fine at 1.50 (100.0), while the evening the
  advertiser paid for is gone. Hand-built demand curve, no random draws;
  illustrative and deterministic.
