# Run — the NOT MET verdict's margins, recomputed from the recorded JSONs

**Date:** 2026-08-06
**Command:** `uv run python core/not_met_report.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed baselines and seed JSONs).
**Cost:** \$0 (local lane; the underlying runs were the mission's recorded
ones).

## Purpose

Mission 06's outcome report judged GRPO against both baselines. This run
recomputes the margins from the committed JSONs against the policy's own
seed spread — the move that makes the verdict honest.

## Output

```
baselines: random 0.2220, greedy 0.8240
GRPO greedy decode 0.0727+-0.0160 | sampled 0.1787+-0.0660

  greedy decode vs random: -0.1493 vs spread 0.0160 -> decisively loses
  sampled decode vs random: -0.0433 vs spread 0.0660 -> within noise
  greedy decode vs greedy: -0.7513 vs spread 0.0160 -> decisively loses
  sampled decode vs greedy: -0.6453 vs spread 0.0660 -> decisively loses
```

## Notes

- The recomputed verdicts reproduce the recorded report exactly (spread is
  the full per-seed range, per the mission's rule). The margins lose except
  the sampled-vs-random row, which is inside the policy's own noise band.
- The verdict is NOT MET not because of a single number but because the
  margins lose and the failure catalogue (board-independent collapse 3/3,
  non-stabilizing success 3/3) explains why: the policy's greedy decode
  emits one fixed action string on every board, which no margin can
  survive.
