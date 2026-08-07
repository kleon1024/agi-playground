# Run — when the policy is biased, executed on the position-adjustment read

**Date:** 2026-08-07
**Command:** `uv run python core/policy_biased.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 53's detour: CTR logged at the top of the page is inflated by
position. This run compares exposure by raw and position-adjusted CTR.

## Output

```
policy is biased, read (exposure by item, raw vs adjusted ctr):
  P1001: raw ctr 0.048 exposure 53% -> adjusted ctr 0.036 exposure 35%
  P1002: raw ctr 0.041 exposure 33% -> adjusted ctr 0.034 exposure 29%
  P1003: raw ctr 0.026 exposure 8% -> adjusted ctr 0.030 exposure 20%
  P1004: raw ctr 0.022 exposure 5% -> adjusted ctr 0.028 exposure 16%

reading: the raw numbers hand most exposure to the items
that sat at the top of the page; the position-adjusted
numbers move the tail from 14% to 36% of
exposure. The bias is in the collection policy, and
correcting it is not fairness - it is measurement.
```

## Notes

- Position adjustment moves the tail from 14% to 36% of exposure; P1001's share falls from 53% to 35%.
- The bias is in the collection policy, and correcting it is not fairness — it is measurement.
