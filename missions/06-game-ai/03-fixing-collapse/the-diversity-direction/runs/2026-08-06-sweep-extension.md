# Run — collapse-fix sweep extension: group 16 and entropy 0.05

**Date:** 2026-08-06
**Commands:**

```bash
cd missions/06-game-ai/03-fixing-collapse/core
uv run --group torch python fix_collapse.py --variant small-group --group-size 16 --seed 0 \
  --out ../../03-fixing-collapse/runs/group16-seed0.json
uv run --group torch python fix_collapse.py --variant entropy-bonus --entropy-coef 0.05 --seed 0 \
  --out ../../03-fixing-collapse/runs/entropy005-seed0.json
```

**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only. Same 5x5 grid-world,
vocab, reward, and GRPO mechanism as stage 01 and the recorded sweep.
**Software:** Python 3.11.14 via uv; the stage's own `fix_collapse.py`
unmodified.
**Wall-clock:** 290s (group 16) and 223s (entropy 0.05), 200 steps each.
**Cost:** \$0 (local lane).

## Purpose

The recorded sweep (2026-08-01) tried smaller groups and a weak entropy
bonus, and concluded neither fix worked. It never tried the opposite
directions on the same two knobs: a larger group (more diversity per
prompt) and a stronger entropy bonus. This run fills both cells of the grid.

## Metrics

| Variant | Seed | Degenerate / 200 | Greedy success | Sampled success | Wall-clock |
|---|---:|---:|---:|---:|---:|
| baseline (stage 01, group 8) | 0/1/2 | 0/0/1 | 0.078/0.062/0.078 | 0.182/0.144/0.210 | ~130s |
| small-group (group 4) | 0/1/2 | 18/4/10 | 0.024/0.050/0.036 | 0.032/0.080/0.034 | ~70s |
| entropy-bonus (coef 0.01) | 0 | 0 | 0.078 | 0.176 | 329s |
| **group 16 (new)** | 0 | 0 | **0.156** | 0.198 | 290s |
| **entropy 0.05 (new)** | 0 | 0 | 0.032 | 0.036 | 223s |

## Notes

- Group 16 is the first variant that substantially moves the collapse:
  greedy success doubles from the baseline's 0.078 to 0.156, and the
  greedy-to-sampled gap halves (0.104 to 0.042). Same environment, same
  reward, same loop — only the rollout group is bigger.
- Stronger entropy (0.05) goes the wrong way: greedy success falls to 0.032,
  below the baseline, with the gap collapsing to 0.004 (the policy is
  everywhere-wrong rather than greedily-collapsed).
- The original sweep's verdict ("neither fix worked") is accurate for the
  grid it ran, and the chapter's point is exactly that: a null only covers
  the cells you ran. The untested direction on the same two knobs is where
  the mechanism moved.
- One seed per new cell; the baseline and small-group rows carry their own
  seed spread from the recorded runs.
