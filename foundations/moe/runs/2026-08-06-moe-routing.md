# Run — tiny MoE routing statistics, 4 experts, 4 patterns

**Date:** 2026-08-06
**Command:** `uv run --group torch python core/moe_demo.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; torch 2.13.0.
**Wall-clock:** ~65s (six configs x 1,500 steps).
**Cost:** \$0 (local lane).

## Purpose

Measure the four things the MoE line is about on a toy that isolates them:
specialization (4 patterns, one target each), load balance under a 4:1
pattern-frequency skew, the shared expert's effect, and accuracy versus
routing cost. An expert is counted as routed when it appears anywhere in the
top-k set, not only as the argmax winner.

## Output

```
tiny MoE, 4 experts, 4 patterns (pattern 0 four times as frequent)
 top_k  shared  accuracy  routing entropy  load imbalance  counts
     1   False     1.000            1.327            None  [45,0,6,149]
     1    True     1.000            1.362            21.5  [172,8,11,9]
     2   False     1.000            1.352           3.892  [93,144,37,126]
     2    True     1.000            1.349           5.613  [174,56,31,139]
     4   False     1.000            1.240             1.0  [200,200,200,200]
     4    True     1.000            1.270             1.0  [200,200,200,200]
```

## Notes

- Accuracy is 1.000 in every cell: on a separable task, routing does not buy
  accuracy. It buys compute — top-1 routes one of four experts per input,
  top-2 two of four, top-4 all four, at identical accuracy.
- Top-1 under the 4:1 skew produces a dead expert (expert 1, 0/200) and a
  74% dominant expert — the routing analog of codebook collapse, and the
  imbalance (21.5x with a shared expert) that load-balancing losses and
  Quantile Balancing exist to fight.
- Routing entropy stays near its maximum (1.33-1.36 of ln 4 = 1.386) in
  every cell: the softmax router balances in expectation even when the
  realized counts are skewed. Entropy and realized load imbalance are
  different diagnostics.
- The shared expert at top-2 (counts [174,56,31,139], imbalance 5.6) does
  not obviously help on this toy; its benefit (absorbing common structure so
  routed experts specialize on differences) needs a task where common
  structure exists, which the toy's block-disjoint patterns do not provide.
