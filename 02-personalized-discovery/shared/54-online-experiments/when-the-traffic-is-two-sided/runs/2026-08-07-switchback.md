# Run — switchback false positives and the price of block units

**Date:** 2026-08-07
**Command:** `uv run python core/switchback.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.5s.
**Cost:** \$0 (local lane).

## Purpose

Measure how per-minute analysis behaves under a time-block-randomized
switchback, whether block-level analysis restores validity, and what the
block unit costs in detectable effect size.

## Output

```
simulation 1 -- 7 days of half-hour blocks, AR(1) phi=0.9, 100 repetitions under the null (declared alpha 5%)
per-minute t-test rejected 53 (53%)
per-block t-test rejected 3 (3%)
median block-mean lag-1 rho1: 0.19 (gate threshold 0.2)

the cost of block-level analysis: 168 half-hour blocks (84 per arm)
minimum detectable effect at 80% power: 0.43 block-SD
a 1% effect would need 36 years of half-hour blocks

simulation 2 -- same market, five-minute blocks, 100 repetitions
per-minute t-test rejected 25 (25%)
per-block t-test rejected 7 (7%)
median block-mean lag-1 rho1: 0.71 (gate threshold 0.2 -- flagged)
```

## Notes

- Simulation 1: per-minute analysis rejects 53% of null experiments. The
  effective unit is the block, not the request; the per-block analysis
  restores near-nominal false-positive control (3%).
- The price is power: 84 half-hour blocks per arm can only detect a 0.43
  block-SD effect at 80% power; a 1% effect needs roughly 36 years of
  half-hour blocks. Bojinov, Simchi-Levi and Zhao (2023), "Design and
  Analysis of Switchback Experiments", Management Science 69(7), formalize
  the design and its variance inflation.
- Simulation 2: short blocks make block means autocorrelate (median rho1
  0.71, which the gate's serial-dependence check flags at 0.2). Fair-coin
  per-block analysis stays approximately valid here because random
  assignment makes the t-test a randomization test; the autocorrelation is
  exactly what makes per-request analysis catastrophic at any block length.
- Synthetic and deterministic; the numbers demonstrate the mechanism and
  its cost, not a real marketplace result.
