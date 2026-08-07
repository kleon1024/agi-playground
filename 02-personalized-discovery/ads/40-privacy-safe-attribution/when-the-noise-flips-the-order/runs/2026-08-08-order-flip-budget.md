# Run — order flips, audited: granularity multiplies the flip exposure

**Date:** 2026-08-08
**Command:** `uv run python core/order_flip_budget.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

The stage-40 audit measured how often one adjacent pair (display vs
email) flips at each epsilon. This detour asks the decision-side
question that rate skips: a real attribution report ranks more than two
channels, and every close pair is another chance for the noise to flip
the budget. It compares a three-channel report with a six-channel
report at the same epsilon, under the stage's own noise model (uniform
of range 100 / epsilon per count), and reads the rank-flip rate and the
expected share of the weekly budget misallocated by a rank-weighted
50/30/20-style split.

## Output

```
order flips, audited: granularity multiplies the flip exposure
  noise model: stage 40's uniform of range 100/epsilon per count
  1000 fixed-seed draws; rank-weighted budget per report size

report        | epsilon | any rank flip  | expected misallocated
  3 channels   |   5.0 |   0.0%        |  0.0% of the weekly budget
  3 channels   |   2.0 |  12.3%        |  2.5% of the weekly budget
  6 channels   |   5.0 |  61.8%        |  3.3% of the weekly budget
  6 channels   |   2.0 |  87.6%        | 12.0% of the weekly budget

reading: the three-channel report at epsilon 2.0 flips its
rank on 12.3 percent of reports; the six-channel report with
the same budget and the same epsilon flips on 87.6 percent.
The decision granularity is a privacy cost the epsilon number
alone does not show: every extra close pair is another chance
for the noise to move budget. The fix is to coarsen the
decision — merge channels that are not separable at the noise
floor, or report only the top split — which trades attribution
detail for a rank the budget can trust (Dwork 2006; Apple
AdAttributionKit, WWDC24, crowd-anonymity buckets;
arXiv:2406.02463).
```

## Notes

- 1,000 fixed-seed draws (seed 23) per (report, epsilon) cell, 4 cells.
- Three-channel true counts: search 480, display 310, email 260 —
  the stage's own numbers. Six-channel adds video 240, social 230,
  affiliate 220, so the tail of the report is a chain of 10-count
  gaps.
- The six-channel report at epsilon 5.0 already flips on 61.8 percent
  of draws even though the top channel is far ahead: the bottom three
  channels sit below the noise floor, so their relative order is
  random at any reasonable epsilon.
- Rank-weighted budget split: 50/30/20 for three channels, 35/25/15/
  10/08/07 for six; misallocation is the average L1 distance between
  the true and noisy budget vectors.
