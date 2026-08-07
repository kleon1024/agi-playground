# Run — the floor-level allocation audit over the emitted floor rows

**Commands:** `uv run python core/allocation.py --emit-log /tmp/allocation-envelope.json`;
`uv run python prod/allocation_audit.py /tmp/allocation-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 53's read shows the floor moving the tail from 1% to a real share.
This run is the case-finding half of the stage: a declared fairness
floor is not the same as the exposure the protected group actually
receives, because renormalising after flooring the other categories
re-dilutes the group the floor was meant to protect. The core script
emits per-floor-level rows; the production audit compares each floor's
declared level against the protected group's measured exposure, the way
a marketplace or fairness team reads allocation telemetry.

## Output

```
allocation audit (protected-group exposure per floor level):
   floor  group exposure      gap  aggregate ctr
      0%            0.9%    -0.9%         0.0355
      5%            4.8%    +0.2%         0.0345
     10%            9.2%    +0.8%         0.0334
     15%           12.6%    +2.4%         0.0319
     20%           15.5%    +4.5%         0.0307

verdict: GROUP GAP -- at a 20% declared floor,
the protected group receives 15.5% of
exposure, a 4.5% shortfall. Renormalising after
flooring the other categories re-dilutes the group the floor
was meant to protect, so the configured constraint is not the
served allocation. Measure per-group exposure, not the declared
floor, and fix the allocation by solving the constrained
problem with the floor as a binding constraint, not by
max-then-renormalise.
```

## Notes

- The gap between the declared floor and the protected group's exposure
  grows with the floor level: 0.2 points at 5%, 0.8 at 10%, 4.5 at 20% —
  the renormalisation after flooring re-dilutes the group harder as more
  categories get floored.
- The audit's message is the stage's: the configured constraint is not
  the served allocation. Measure per-group exposure, not the declared
  floor, and fix the allocation by solving the constrained problem with
  the floor binding, not by max-then-renormalise. Multi-sided exposure
  bias work (Abdollahpouri et al., KDD Workshop 2020) frames exactly
  this gap between the intended and the served allocation.
