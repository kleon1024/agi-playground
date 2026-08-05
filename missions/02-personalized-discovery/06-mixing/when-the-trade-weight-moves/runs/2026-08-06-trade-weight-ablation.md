# Run — mixing-weight ablation: diversity decay and the ad trade rate

**Date:** 2026-08-06
**Command:** `uv run python core/trade_weight_ablation.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only; reuses the stage's
`slate_mixing.py` importably (same seed 42, same catalogue).
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 06's README teaches the constraint-versus-penalty distinction and the
ad-displacement curve in prose. This run measures both on the stage's own
synthetic catalogue — same seed, same beam search, same value function — so
the tradeoffs are numbers, not claims.

## Output

```
A. diversity-decay sweep (penalty strength), beam width 2, no cap
 decay categories                 value@decay  raw value  raw vs no-penalty
  0.00 cooking:1 music:1 news:1 sports:2      1.8673     2.1853            -0.1782
  0.25 cooking:1 music:1 news:1 sports:2      1.9468     2.1853            -0.1782
  0.50 cooking:1 music:1 news:1 sports:2      2.0263     2.1853            -0.1782
  0.75 cooking:1 music:1 news:1 sports:2      2.1126     2.2011            -0.1624
  1.00 cooking:1 news:1 sports:3       2.3634     2.3634            +0.0000

constraint reference (cap=2, decay=1.0): categories {'sports': 2, 'cooking': 2, 'news': 1}, raw value 2.2624

B. ad trade-rate sweep (ad load 4): revenue vs organic value displaced
trade rate   revenue  displaced  per $ revenue
       0.5     0.000    -0.0000          -0.00
       1.0     0.872     0.7821           1.11
       2.0     1.423     1.2659           1.12
       3.0     1.423     1.2659           1.12
       5.0     1.885     2.0264           0.93
      10.0     1.885     2.0264           0.93
```

## Notes

- The no-penalty optimum (decay 1.0) is three sports items — maximum raw
  value, zero diversity. Every penalty setting buys diversity at a measured
  raw-value cost (0.1782 at decay 0.5).
- The hard constraint (cap=2) returns raw value 2.2624 — *higher* than the
  stage's default penalty (decay 0.5, raw 2.1853) — and it is a guarantee
  you can point to. On this catalogue the constraint dominates the penalty
  on both axes; the chapter says so without claiming it generalizes.
- The ad knee sits between trade rates 3 and 5 at load 4: revenue per
  displaced dollar falls from 1.12 to 0.93 as the strongest organic items
  start being pushed out. Rate 3.0 is the stage's default, tuned only to make
  displacement observable; this run shows what sits beyond it.
- Synthetic catalogue, one seed. This is a demonstration of the tradeoff
  shape, not a business recommendation.
