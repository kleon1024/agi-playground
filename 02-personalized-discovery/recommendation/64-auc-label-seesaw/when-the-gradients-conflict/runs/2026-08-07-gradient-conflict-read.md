# Run — when the gradients conflict, executed on the PCGrad comparison

**Date:** 2026-08-07
**Command:** `uv run python core/gradient_conflict.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 5.1s (2 variants x 60 epochs).
**Cost:** \$0 (local lane).

## Purpose

Multi-task conflict is often met with gradient surgery (PCGrad projects one
task's gradient away from the other's when their directions conflict). This
detour asks whether the conflict frequency alone justifies the optimizer —
and measures that it does not on this cohort.

## Output

```
when the gradients conflict, read (click vs buy):
  model           click auc buy auc
  naive sum           0.710   0.720
  pcgrad              0.712   0.712
  conflicting epochs: 43 of 60

reading: the gradients conflict in most epochs, but surgery is
neutral on this cohort -- neither task's AUC moves beyond noise.
the conflict frequency alone does not justify the optimizer;
the test is whether one task's update actively reverses the
other's progress on the validation loss. here the naive sum
already balances the two, and the sparse task's bottleneck is
amplitude, not direction -- weighting (stage 61) moves the buy
task, PCGrad does not. measure before adopting.
```

## Notes

- The gradients conflict in 43 of 60 epochs — by the textbook signal,
  surgery should help. It does not: click AUC 0.710 to 0.712, buy AUC
  0.720 to 0.712, both within noise.
- The diagnostic that matters is not conflict frequency but whether one
  task's update reverses the other's validation progress. Here the naive
  sum already balances the two tasks; the sparse task's bottleneck is
  gradient amplitude, which weighting (stage 61) fixes and PCGrad does not.
- Decision rule for production: before adopting PCGrad (Yu et al.,
  NeurIPS 2020, arXiv:2001.06782) or CAGrad (Liu et al., NeurIPS 2021),
  measure the validation-loss interference on your own cohort. On this
  one, the answer is no.
