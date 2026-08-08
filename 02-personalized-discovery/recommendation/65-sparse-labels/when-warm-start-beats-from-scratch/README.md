---
status: verified
level: applied
base: scratch
label: When warm start beats from scratch
verified: 2026-08-07
---

# Warm start is not automatic: the source task has to share the signal

**Question:** the cold-item slice has five train positives, so a ranker
trained there from scratch fits noise. The natural fix is transfer:
pre-train the trunk on a dense task and fine-tune on the cold rows. This
chapter tests two source tasks and reads which one actually transfers.

**Before this:** [stage 65 — sparse labels](../) and [stage 61 — multi-task
conflict](../../61-multi-task-conflict/), where the shared trunk's balance
is the mechanism. This detour is the transfer axis of the sparse-label
fixes.

## The transfer test, executed

The run ([record](runs/2026-08-07-warm-start-read.md)) trains from
scratch, from a click-task trunk, and from a head-slice-buy trunk on the
same cold rows (3,706 train, 936 test, 87 train positives):

| model | cold-slice buy AUC |
|---|---:|
| from scratch | 0.740 |
| from click task | 0.659 |
| from head-slice buy | 0.786 |

## The reading

Warm start is not automatic. Pre-training on clicks and fine-tuning on the
cold rows loses to scratch (0.659 versus 0.740), because the click task's
trunk is activity-dominated — the signal that drives clicks, not purchases.
The same objective on the dense head slice is the aligned source: it
shares buy's drivers, so the fine-tune beats scratch (0.786). The transfer
test is source-task alignment, measured per slice — never assumed from
the task names. This is the warm-start prior literature in miniature
(Yi et al., RecSys 2019, on sampling bias in YouTube recommendation
labels): what transfers is the signal distribution, not the task label.

## The fix and its trade

The failure is assuming transfer from the task names: the click-task
trunk is activity-dominated, so fine-tuning it on the cold rows loses to
scratch (0.659 versus 0.740), while the aligned source — the same buy
objective on the dense head slice — wins (0.786). The fix is the
transfer test: train the candidate source tasks on their dense slices,
fine-tune each on the cold rows, and compare cold-slice AUC against a
from-scratch baseline — source-task alignment measured per slice, never
inferred (the warm-start prior in miniature: Yi et al., RecSys 2019, on
sampling bias in YouTube recommendation labels). The trade is the
commitment the test costs: each candidate source is a real training run,
and a misaligned transfer path is worse than no transfer at all, because
the fine-tune starts from a representation biased away from the target's
signal.

## Who owns the loop

- **The model team** owns the transfer path: the candidate sources, the
  fine-tune, and the from-scratch baseline it must beat.
- **The evaluation team** owns the per-slice comparison: cold-slice AUC
  with intervals, not the task names, is the verdict.
- **The data team** owns the source-task density the test depends on:
  an aligned source exists only where the dense slice actually shares
  the target's signal distribution.

When ownership is implicit, the team pre-trains on whatever dense task
is available, and the 0.659 result ships as "transfer tried" instead of
"transfer misaligned."

## Evidence boundary

The executed synthetic read over one cohort with declared click and buy
drivers (illustrative, deterministic, single seed). It demonstrates the
alignment test; real systems must run the same source-comparison per cold
slice before committing a transfer path.

## Check your mental model

Answer each before opening it.

**1. Why does the click trunk hurt the cold-slice buy model?**

<details>
<summary>Answer</summary>

Because the click task's representation is shaped by activity — who
clicks a lot — not by what leads to purchase. Fine-tuning on the cold rows
starts from a representation biased away from the buy signal, and the
executed read shows it losing to a from-scratch fit (0.659 versus 0.740).

</details>

**2. What is the transfer test, concretely?**

<details>
<summary>Answer</summary>

Train the candidate source tasks on their dense slices, fine-tune each on
the cold rows, and compare cold-slice AUC against a from-scratch baseline.
The source that wins is the one sharing the target's signal distribution —
measured per slice, never inferred from the task names.

</details>

## Next

Back to [stage 65](../), where warm start is one of the three fix layers
— now with the alignment test that decides whether it pays.
