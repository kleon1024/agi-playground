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
