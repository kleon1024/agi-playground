---
status: verified
level: applied
base: scratch
label: When the gradients conflict
verified: 2026-08-07
---

# Conflict frequency alone does not justify gradient surgery

**Question:** the multi-task trunk's gradients conflict, and the textbook
answer is surgery — PCGrad projects one task's gradient away from the
other's. This chapter asks whether the conflict frequency alone justifies
the optimizer, and measures that it does not on this cohort.

**Before this:** [stage 64](../) and [stage 61 — multi-task
conflict](../../61-multi-task-conflict/), where the shared trunk's task
balance is the mechanism. This detour tests the optimizer-level fix for
the same conflict.

## The comparison, executed

The run ([record](runs/2026-08-07-gradient-conflict-read.md)) trains the
naive sum and a PCGrad variant on the same click-versus-buy cohort:

| model | click AUC | buy AUC |
|---|---:|---:|
| naive sum | 0.710 | 0.720 |
| PCGrad | 0.712 | 0.712 |

Conflicting epochs: 43 of 60.

## The reading

The gradients conflict in most epochs — by the textbook signal, surgery
should help. It does not: neither task's AUC moves beyond noise. The
diagnostic that matters is not conflict frequency but whether one task's
update actively reverses the other's validation progress; here the naive
sum already balances the two, and the sparse task's bottleneck is
amplitude, not direction. Weighting ([stage 61's balance](../../61-multi-task-conflict/))
moves the buy task; PCGrad does not. The production decision rule is to
measure validation-loss interference on your own cohort before adopting
PCGrad (Yu et al., NeurIPS 2020, arXiv:2001.06782) or CAGrad (Liu et al.,
NeurIPS 2021, arXiv:2106.16142) — the paper mechanism and the working
mechanism are different claims.

## The fix and its trade

The failure is adopting the optimizer on the textbook signal. The run
measures why conflict frequency alone does not justify surgery: the
gradients conflict in 43 of 60 epochs, and PCGrad still does not win —
naive sum click 0.710 / buy 0.720, PCGrad 0.712 / 0.712, both within
noise. The fix is to test the mechanism the optimizer actually repairs —
one task's update actively reversing the other's validation progress —
on your own cohort before paying the optimizer's cost (Yu et al.,
NeurIPS 2020, arXiv:2001.06782; CAGrad: Liu et al., NeurIPS 2021,
arXiv:2106.16142). The trade is measured by the same comparison: surgery
adds per-step projection cost and hyperparameters, and it cannot move a
task whose bottleneck is gradient amplitude, not direction — which is
why the stage-64 weighting fix, the amplitude fix, is the one that moved
the number.

## Who owns the loop

- **The model team** owns the adoption test: the validation-loss
  interference read during joint training decides whether the optimizer
  class is even on the table, and it comes before the optimizer choice,
  not after.
- **The evaluation team** owns the interference measurement itself: the
  per-task validation progress under joint training, not conflict
  frequency, is the number that decides.
- **The research and algorithm team** owns the surgery family choice
  (PCGrad versus CAGrad and successors) once interference is proven, and
  the regression risk a projection rule carries on the primary metric.

When ownership is implicit, the team adopts PCGrad because the gradients
"look conflicting" and pays the optimizer's cost for a balance the naive
sum already had.

## Evidence boundary

The executed synthetic comparison over one cohort (illustrative,
deterministic, single seed). It demonstrates that conflict frequency and
interference are different diagnostics; real systems must run the same
validation-loss interference test on production tasks before paying the
optimizer's cost.

## Check your mental model

Answer each before opening it.

**1. Why do 43 conflicting epochs not produce a PCGrad win?**

<details>
<summary>Answer</summary>

Because conflict frequency measures direction disagreement, not harm. If
each task's update still advances the other's validation loss on balance,
the conflict is noise, not interference. The executed run shows the naive
sum already balancing the two tasks, so there is no reversal for surgery
to remove.

</details>

**2. When would PCGrad actually pay?**

<details>
<summary>Answer</summary>

When one task's update measurably reverses the other's validation
progress — real interference, not direction disagreement. The test is a
validation-loss read during joint training, and it comes before the
optimizer choice, not after it.

</details>

## Next

Back to [stage 64](../), where the amplitude fix — slice weighting —
is the one that moved the number.
