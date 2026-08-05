# Run — the rule engine's frontier: region x cap, and the empty-set boundary

**Date:** 2026-08-06
**Command:** `uv run python core/rule_frontier.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `rule_engine.py`
unmodified.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 07's demo shows one empty-set case. The empty set is a property of
the rule x context grid; this run sweeps region and the per-creator cap to
map the boundary, and prints one decision's audit record.

## Output

```
region  cap  kept  empty
   US    1     3  False
   US    2     6  False
   US    3     6  False
   US    4     6  False
   EU    1     0   True
   EU    2     0   True
   EU    3     0   True
   EU    4     0   True

audit sample (region=US, cap=1) — one capped decision's record:
  us_1: status=capped, fired=['per_creator_cap']
  explanation: creator cap of 1 reached
```

## Notes

- The empty set is region-determined, not cap-determined: EU empties at
  every cap, US never does. The rules intersect to nothing for EU by
  construction, and the sweep shows the boundary is a vertical line in the
  grid, not a cap threshold.
- The audit record shows why: us_1 is capped with the fired rule and a
  human-readable explanation — the "why was this shown" answer the mission
  requires, attached to the decision.
