# Run — two-sided feedback, does the cut chase both sides away

**Date:** 2026-08-08
**Command:** `uv run python core/two_sided_feedback.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 42's executed sweep prices the take rate against one
volume-response curve: `volume = 1000 x (1 - 1.6 x rate)`. This audit
asks what that curve misses. A marketplace has two sides, and the side
that does not pay still responds. The run models sellers leaving as the
fee rises (same price sensitivity as the stage), buyers shrinking with
the selection (`buyers = sellers`), and transactions as the matches
between the two sides. It measures where the two-sided revenue peak
sits against the one-sided peak and what the one-sided optimum rate
earns once the cross-side feedback is included.

## Output

```
two-sided feedback, audited: does the cut chase both sides away?
  one-sided volume = 1000 x (1 - 1.6 x rate), stage 42's curve
  two-sided: sellers leave with the fee; buyers = sellers;
  transactions = sellers x buyers / 1000

 rate | one-sided volume | two-sided volume | two-sided revenue
    5% |           920 |           846 |           $  42.3
   15% |           760 |           578 |           $  86.6
   25% |           600 |           360 |           $  90.0
   35% |           440 |           194 |           $  67.8
   45% |           280 |            78 |           $  35.3

 one-sided revenue peak:   31.0% / $ 156.2
 two-sided revenue peak:   21.0% / $  92.6
 two-sided revenue at the one-sided peak rate (31.0%): $  78.7 (15.0% below peak)

reading: the one-sided curve prices the fee as if only the
paying side responds. The two-sided model lets the thinner
selection shrink the other side too, and the revenue peak
falls from 31.0% to 21.0% while revenue
at the old peak rate sits below the new one. The cut is a
two-sided price even when only one side pays it.
```

## Notes

- The two-sided model reuses the stage's exact seller price sensitivity
  (`1.6`), so any difference between the curves comes only from the
  buyer side responding to selection.
- The cross-side feedback amplifies every rate: at 35 percent the
  one-sided curve keeps 440 transactions, the two-sided model only 194,
  and revenue is \$67.8 against the one-sided \$154.
- The revenue peak falls from 31.0 percent / \$156.2 to 21.0 percent /
  \$92.6, and the platform that keeps pricing at the one-sided optimum
  (31.0 percent) earns \$78.7, 15.0 percent below the two-sided peak.
- The cut is a two-sided price even when only one side pays it; real
  take-rate decisions need the measured cross-side response, which only
  a live marketplace provides.
