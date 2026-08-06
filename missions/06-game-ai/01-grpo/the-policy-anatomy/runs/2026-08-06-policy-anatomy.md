# Run — the policy anatomy, computed from the stage-01 config and seeds

**Date:** 2026-08-06
**Command:** `uv run python core/policy_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the three recorded seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-07-31
runs).

## Purpose

Mission 06's "model" is mission 01's decoder with a different reward. This
run lays out the structure and reads the collapse from the recorded seeds.

## Output

```
policy anatomy (stage-01 config), computed:
  structure: mission 01's Transformer, 692,864 params,
             instantiated for a 28-character grid vocabulary
  reward:    format credit (0.2/0.5/1.0 for legal moves)
             + terminal goal-reached bit
  outcome:   each seed collapses to a constant direction string
             seed 0: greedy success 0.078
             seed 1: greedy success 0.062
             seed 2: greedy success 0.078
```

## Notes

- The architecture is not the failure: the same Transformer that learns
  next-token prediction collapses here because the reward's format credit
  can be earned without reaching the goal.
- Greedy success (0.062-0.078) sits below the random floor (0.222) — the
  cold-start trap the mission's null result records.
