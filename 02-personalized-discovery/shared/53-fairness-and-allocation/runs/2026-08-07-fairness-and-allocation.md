# Run — fairness and allocation, executed on the exposure-budget read

**Date:** 2026-08-07
**Commands:** `uv run python core/allocation.py --emit-log /tmp/allocation-envelope.json`;
`uv run python prod/allocation_audit.py /tmp/allocation-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 53 introduces allocation. This run measures exposure by category
with and without a 10% per-category floor, then sweeps the floor level
and emits the protected-group exposure rows the production audit reads.

## Output

```
fairness and allocation, read (exposure by category):
  unconstrained:
    audio        ctr 0.040 exposure 59%
    video        ctr 0.032 exposure 30%
    cable        ctr 0.022 exposure 10%
    accessories  ctr 0.010 exposure 1%
    aggregate ctr: 0.0355
  with a 10% per-category floor:
    audio        ctr 0.040 exposure 54%
    video        ctr 0.032 exposure 28%
    cable        ctr 0.022 exposure 9%
    accessories  ctr 0.010 exposure 9%
    aggregate ctr: 0.0334

reading: the floor moves accessories from near-invisible to
a real share and costs a little aggregate ctr. Allocation is
a constraint on the ranking objective, and the price of the
constraint is measured, not assumed.

floor sweep (protected-group exposure per floor level):
   floor  accessories  aggregate ctr
      0%         0.9%         0.0355
      5%         4.8%         0.0345
     10%         9.2%         0.0334
     15%        12.6%         0.0319
     20%        15.5%         0.0307

  reading: the declared floor never quite lands on the
  protected group - at a 10% floor, accessories receive 9.2%
  of exposure because renormalising after the floor re-
  dilutes it. Measure per-group exposure, not the declared
  floor, before declaring the allocation fair.
```

## Notes

- The 10% floor moves accessories from 1% to 9% of exposure at a cost of 0.0021 aggregate CTR (0.0355 to 0.0334).
- Allocation is a constraint on the ranking objective, and the price of the constraint is measured, not assumed.
- The floor sweep is the case-finding half of the stage: the declared
  floor never quite lands on the protected group — at a 10% floor,
  accessories receive 9.2% of exposure because renormalising after the
  floor re-dilutes it. The audit reads the emitted envelope and returns
  the GROUP GAP verdict; see the audit record.
