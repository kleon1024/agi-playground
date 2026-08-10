# Run — when the policy borrows luck, executed on the exposure read

**Date:** 2026-08-07
**Command:** `uv run python core/policy_luck.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 45's detour: the log measures quality under the policy, not
quality. This run reads the naive, true-propensity, and stale-propensity
estimates for two items with identical true CTR and different position
multipliers.

## Output

```
policy borrows luck, read (200 impressions each, true ctr 0.030):
  item  multiplier  clicks  naive ctr  IPS (true)  IPS (stale)
  A       2.0       12    0.060      0.030       0.060
  B       0.5        3    0.015      0.030       0.015

reading: the naive log says A converts at 0.060 and B at 0.015
- A borrowed the featured slot's luck. IPS with the propensities
that produced the log returns 0.030 for both. When the policy
changes and the stored propensities go stale, the correction
reproduces the bias - the loop's luck is only payable with the
propensity log, which is why exploration must be logged, not
assumed.
```

## Notes

- The naive estimate conflates quality with position luck; IPS with the
  propensities that produced the log recovers the true rate for both
  items.
- The stale-propensity column is the feedback-loop twist: when the
  serving policy changes, the stored propensities describe a policy that
  no longer exists, and the correction reproduces the bias. The
  propensity log must be kept with the policy version that produced it.
- Cross-references stage 59's exposure-bias detour on noisy propensities
  (`recommendation/59-exposure-bias/when-the-propensity-is-noisy/`).
