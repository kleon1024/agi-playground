---
status: verified
level: applied
base: scratch
label: When the list is longer
verified: 2026-08-06
---

# Where the formulation choice actually matters

**Question:** [stage 12's learning-to-rank](../) compared pointwise and
pairwise on eight items. This chapter reads the executed sixteen-item run
and asks when the difference grows.

**Before this:** [stage 12 — search ranking](../) and its executed
comparison.

## The longer list, executed

The run ([record](runs/2026-08-06-list-length.md)) extends the labeled set
to sixteen items:

| formulation | NDCG |
|---|---:|
| pointwise | 0.5747 |
| pairwise | 0.5169 |

## Two readings

**More items widen the gap between the formulations.** On eight items the
pointwise/pairwise NDCG difference was 0.04; on sixteen it is 0.058. With
more items, pairwise learns the comparisons that dominate the list while
pointwise's absolute scores have more room to disagree — the objective
choice matters more as the candidate list grows.

**The metric still decides, and the gap is instance-specific.** The longer
list happens to favor pointwise, but that is not a law — a different data
generation would favor pairwise. The lesson is the one the stage
established: report both formulations against the metric, and let NDCG
arbitrate rather than asserting a winner.

## Evidence boundary

The executed rankers over a sixteen-item list derived by perturbing the
stage's eight-item data (deterministic, illustrative). It demonstrates
the growing divergence; it does not claim a universal winner.

## Check your mental model

Answer each before opening it.

**1. Why does the gap grow with list length?**

<details>
<summary>Answer</summary>

Because pairwise optimizes comparisons, and a longer list has more
comparisons to get right. Pointwise optimizes each item's absolute score,
which is a looser constraint — with sixteen items there are more positions
where the two objectives disagree. The divergence is not noise; it is the
two losses pulling the ranking in measurably different directions.

</details>

**2. Why is the winner not transferable?**

<details>
<summary>Answer</summary>

Because the data determines which objective fits better. On this
perturbed list pointwise wins; on the original eight items the gap was
similar in size. A different feature distribution or grade structure
could flip it. The reproducible method — run both, compare by NDCG — is
the transferable part, not the winner.

</details>

## Next

Back to [stage 12](../), or to
[stage 13 — search evaluation](../../13-search-evaluation/) where the
ranker is judged.
