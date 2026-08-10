# Run — the shading-dynamics audit

**Date:** 2026-08-08
**Command:** `uv run python core/shading_dynamics.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.23s.
**Cost:** \$0 (local lane).

## Purpose

The stage run compares first- and second-price revenue under one bid
set. The audit asks the dynamic question: what happens to first-price
revenue as bidders learn to shade? Bidders play a first-price auction
repeatedly; each round they move their bid function partway toward the
best response to the last round's observed competition. Truthful round
1 pays the naive first-price revenue; as shading learns, revenue falls
toward the symmetric equilibrium — for three uniform bidders, the same
expected revenue the second-price auction pays. Simulation: 12 rounds
of 300 auctions, three bidders, values iid U(0,1), fixed seed, damping
0.4.

## Output

```
shading-dynamics audit: 12 rounds x 300 auctions, fixed seed
three bidders, values iid U(0,1); round 1 bids truthfully,
later rounds damped best responses to observed competition

   round  mean revenue
       1        0.7485
       2        0.6522
       3        0.5903
       4        0.5585
       5        0.5120
       6        0.4998
       7        0.4933
       8        0.5038
       9        0.4990
      10        0.4985
      11        0.4968
      12        0.4988

naive round 1:       0.7485
converged (avg 10-12): 0.4980
second-price revenue:   0.5000 (theoretical)
erosion: 33%

reading: first-price revenue is a moving target. The naive
round pays the winner's value; as bidders learn the competition
they shade, and revenue falls toward the symmetric equilibrium —
for three uniform bidders, the same expected revenue the
second-price auction pays. The first-price advantage is a
transient, not a property: it exists only while bidders stay
naive.
```

## Notes

- Naive round 1 pays the winner's value at 0.7485. As bidders learn
  the competition and shade, revenue falls to 0.4980 by rounds 10-12 —
  the symmetric equilibrium for three uniform bidders, equal to the
  second-price expected revenue of 0.5000. Erosion: 33 percent.
- The learning rule is a damped best response (damping 0.4) to the
  last round's highest-competing-bid distribution, declared and
  disclosed in the script. Values, histories, and outcomes drawn with
  a fixed seed. Illustrative and deterministic, not real bidder logs.
