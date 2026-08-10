# Run — the dead expert, read from the recorded MoE routing run

**Date:** 2026-08-06
**Command:** `uv run python core/dead_expert_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the routing was the chapter's recorded
2026-08-06 run).

## Purpose

The MoE chapter's run measured six top-k/shared configurations under a 4:1
pattern skew. This run reads the record and lays out the collapse — the
dead expert and the imbalance the load-balancing machinery exists to fight.

## Output

```
  top-k shared  accuracy  entropy  imbalance  counts
  1     False  1.000   1.327    None   [45,0,6,149]
  1     True   1.000   1.362    21.5   [172,8,11,9]
  2     False  1.000   1.352    3.892  [93,144,37,126]
  2     True   1.000   1.349    5.613  [174,56,31,139]
  4     False  1.000   1.240    1.0    [200,200,200,200]
  4     True   1.000   1.270    1.0    [200,200,200,200]
```

## Notes

- Top-1 without a shared expert under the 4:1 skew produces a dead expert
  (expert 1, 0/200) and a 74% dominant expert — the routing analog of
  codebook collapse.
- Accuracy is 1.000 in every cell: on a separable task, routing buys
  compute, not accuracy, and the imbalance numbers are the cost it hides.
