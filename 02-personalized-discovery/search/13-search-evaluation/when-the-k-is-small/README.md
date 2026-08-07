---
status: verified
level: applied
base: scratch
label: When the k is small
verified: 2026-08-06
---

# NDCG@1 is a different claim than NDCG@5

**Question:** [stage 13's evaluation](../) reports NDCG@k. This chapter
reads the executed k-sweep and asks what k changes about the verdict.

**Before this:** [stage 13 — search evaluation](../) and its executed
metrics.

## The sweep, executed

The run ([record](runs/2026-08-06-k-read.md)) computes NDCG@1, @3, @5 on
the same ranking [0, 3, 2, 0, 1]:

| k | NDCG@k |
|---:|---:|
| 1 | 0.000 |
| 3 | 0.500 |
| 5 | 0.546 |

## Two readings

**The verdict flips with k.** At k=1 the top item is irrelevant (grade 0),
so NDCG is 0 — the ranking looks like a total failure. At k=3 the strong
hits at positions 2-3 lift it to 0.500, and at k=5 it reaches 0.546. The
same ranking is "bad at @1" and "decent at @5".

**k must be declared with the metric.** "NDCG@5" is a different claim than
"NDCG@3" — one rewards deep-list quality, the other top-slot precision.
A system optimized for @1 will bury strong results below the top;
optimized for @5 it tolerates a weak first slot. The k is part of the
evaluation contract, exactly as the mission's own nDCG@10 declares its
cutoff.

## Evidence boundary

The executed k-sweep over one hand-built ranking (illustrative,
deterministic). It demonstrates the k-dependence; real evaluation must
declare k to match the product surface being measured.

## Check your mental model

Answer each before opening it.

**1. Why is NDCG@1 zero when the list has relevant items?**

<details>
<summary>Answer</summary>

Because NDCG@1 only looks at the first position, and the first item is
irrelevant (grade 0). The strong grades at positions 2-3 are outside the
window. The metric is not wrong — it is measuring top-slot precision,
which this ranking fails. The relevant items exist; they are just not at
the top, which is exactly what a small k punishes.

</details>

**2. What would a system optimized for @1 do differently?**

<details>
<summary>Answer</summary>

Sacrifice deep-list quality for a guaranteed relevant first slot — place
one good hit at position 1 even if the rest of the list degrades. That is
the metric's incentive, and it is why the k must be chosen to match the
product: a search box showing one result needs @1; a ten-result page
needs @10. The declared k is what makes the incentive visible and
intentional.

</details>

## Next

Back to [stage 13](../), or to
[the metric chooses the winner](../when-mrr-and-ndcg-disagree/) for the
metric-blind-spot side.
