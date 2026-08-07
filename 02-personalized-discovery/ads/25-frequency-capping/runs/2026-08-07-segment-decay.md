# Run — the hidden-slice frequency audit

**Date:** 2026-08-08
**Command:** `uv run python core/segment_decay.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.15s.
**Cost:** \$0 (local lane).

## Purpose

The stage run reads one decay curve and reads a cap off it. The audit
asks the case-finding question at production scale: which segment
carries the fatigue? It draws 20,000 impressions (fixed seed) across
three segments with different fatigue curves and different exposure
distributions, and reports aggregate and per-segment CTR plus the share
of impressions served at or below 0.005 CTR.

## Output

```
hidden-slice audit: 20,000 impressions, fixed seed
three segments, three fatigue curves, three exposure
distributions; 'dead' = CTR at or below 0.005

    segment   share  mean CTR  dead share
     casual   30.0%    0.0458        0.0%
   standard   50.0%    0.0328        7.2%
      power   20.0%    0.0133       40.6%
  aggregate    100%    0.0328       11.7%

fix comparison: one global cap vs per-segment caps
  global cap 3 (from the aggregate curve):
       casual: cut   810 impressions,   28.5 expected clicks lost
     standard: cut  2990 impressions,   38.8 expected clicks lost
        power: cut  2469 impressions,    7.3 expected clicks lost
        total: cut  6269 impressions,   74.5 clicks lost
  per-segment caps (casual 7, standard 3, power 2):
       casual: cut     0 impressions,    0.0 expected clicks lost
     standard: cut  2990 impressions,   38.8 expected clicks lost
        power: cut  3162 impressions,   17.0 expected clicks lost
        total: cut  6152 impressions,   55.8 clicks lost

reading: aggregate CTR 0.03-ish looks healthy while the power
slice runs far below it with a large dead share. A cap read off
the aggregate curve keeps serving the slice that stopped
clicking, and a global cap trades away healthy casual clicks.
Stratifying by segment is how the case is found; per-segment
caps are how the trade is tuned.
```

## Notes

- The aggregate mean CTR is 0.0328 — close to the stage's standard
  curve — while the power slice runs at 0.0133 with 40.6 percent of its
  impressions served at or below 0.005 CTR. A cap read off the
  aggregate curve keeps serving the slice that stopped clicking.
- The fix comparison is the trade: the global cap 3 cuts 6,269
  impressions and sacrifices 28.5 casual expected clicks to save 7.3
  power clicks; per-segment caps (casual 7, standard 3, power 2) cut
  6,152 impressions and lose 0 casual clicks. Stratifying by segment is
  how the case is found; per-segment caps are how the trade is tuned.
- Exposure counts drawn from per-segment distributions with a fixed
  seed; CTR is read off per-segment decay curves. Illustrative and
  deterministic, not real click logs.
