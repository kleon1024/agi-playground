# Run — the transition-measurement audit

**Date:** 2026-08-08
**Command:** `uv run python core/transition_measurement.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.30s.
**Cost:** \$0 (local lane).

## Purpose

The stage's audit shows first-price revenue erodes as bidders learn to
shade. This detour asks the measurement question a platform faces
after a rule change: when do you sample revenue? It runs the same
learning dynamics for 20 rounds and reads what a platform would
measure at each point after the transition to first price — day one,
the learning period, and the settled state — against the second-price
revenue the market returns to.

## Output

```
transition-measurement audit: 20 rounds x 300 auctions, fixed seed
the market just moved to first price; bidders learn to shade

    measure at  revenue read  vs second price
             1        0.7485           +49.7%
             2        0.6522           +30.4%
             4        0.5585           +11.7%
             8        0.5038            +0.8%
            14        0.4977            -0.5%
            20        0.4766            -4.7%

settled revenue (avg rounds 18-20): 0.4772
second-price revenue: 0.5000
day-one read overstates settled revenue by 57%

reading: after a rule change, revenue is a function of when
you measure it. The day-one read (0.75) is the naive market;
the settled read is the equilibrium the bidders learn to. A
platform that decides on the early number over-invests in the
new rule; one that waits sees the erosion to second-price
revenue. The measurement window is part of the market-design
decision, not a reporting detail.
```

## Notes

- The same market reads 0.7485 (+49.7 percent over second price) on
  day one, 0.5038 (+0.8 percent) at round 8, and settles near the
  second-price revenue by rounds 18-20. The day-one read overstates
  the settled revenue by 57 percent.
- A platform that decides on the early number over-invests in the new
  rule; one that waits sees the erosion. The measurement window is
  part of the market-design decision, not a reporting detail.
- Same learning model as the stage audit (damped best response,
  fixed seed). Illustrative and deterministic, not real bidder logs.
