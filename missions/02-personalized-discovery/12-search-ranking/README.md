---
status: verified
level: applied
base: scratch
label: Search ranking
verified: 2026-08-06
---

# Re-ordering the candidates: pointwise versus pairwise

**Question:** retrieval returns a candidate set, but the set is not the
answer. Search ranking re-orders it. This stage implements the two classic
formulations and asks which objective the metric actually rewards.

**Before this:** [stage 11 — search retrieval](../11-search-retrieval/)
for the candidate set, and [stage 04's fine-rank](../04-fine-rank/) for the
same idea in the recommendation funnel.

## The two formulations, executed

The run ([record](runs/2026-08-06-learning-to-rank.md)) executes both
rankers on the same eight-item labeled set:

| formulation | NDCG | order |
|---|---:|---|
| pointwise | 0.6209 | [0, 7, 1, 2, 3, 4, 6, 5] |
| pairwise | 0.5804 | [0, 7, 1, 4, 3, 2, 6, 5] |

## The mechanism, named

1. **Pointwise** — predict an absolute relevance score per item, rank by
   the score. The loss is squared error against the grade.
2. **Pairwise** — learn which of two items should rank first, by fitting
   a linear preference over item pairs. The loss is about comparison, not
   absolute score.

Both here are linear (least-squares fits) so the difference is purely in
the objective, not the model class. On small data they often agree — both
put items 0 and 7 first — but the NDCG gap (0.6209 vs 0.5804) is where
the formulations diverge.

## Why the metric is the arbiter

The two losses disagree on mid-list order (pointwise puts 2 before 3,
pairwise puts 4 before 3). Which is "right" is not decided by the loss —
it is decided by NDCG, the metric that measures what search actually
rewards: graded relevance, weighted to the top of the list. This is the
same lesson as stage 04's fine-rank applied to search: the objective and
the metric can be different, and the metric is the contract.

## Evidence boundary

The executed rankers over an eight-item synthetic labeled set (two
features, grades 0-3, deterministic). It demonstrates the formulation
contrast; it does not claim one formulation always wins — the NDCG gap is
an instance, not a law.

## Check your mental model

Answer each before opening it.

**1. Why would pairwise ever lose to pointwise?**

<details>
<summary>Answer</summary>

Because pairwise optimizes comparisons, not absolute quality — and on a
small set the pairwise fit can be noisier than the pointwise one. The two
objectives measure different things: pointwise asks "how relevant is
this?" and pairwise asks "is A better than B?". Which better predicts the
metric is empirical, which is why the run reports NDCG for both instead
of asserting a winner.

</details>

**2. Why does NDCG, not the loss, decide the better ranker?**

<details>
<summary>Answer</summary>

Because the loss is a proxy and the metric is the contract. Squared error
or pairwise error can be minimized while the ranking the user sees is
worse, if the loss weights the wrong positions. NDCG is graded and
top-weighted — it matches what search actually rewards — so it is the
arbiter between formulations, exactly as the mission's own evaluation
discipline uses the declared metric over the trained loss.

</details>

## Next

Forward to [stage 13 — search evaluation](../13-search-evaluation/) which
decides what "worked" means.

A detour from here: [the label that carries the position's bias](when-the-label-is-a-click/) — the executed exposure model read: observed click = relevance x exposure, so raw clicks teach position, not meaning.

Another detour: [where the formulation choice actually matters](when-the-list-is-longer/) — the executed sixteen-item run read: the pointwise/pairwise NDCG gap grows with list length, so the objective choice matters more as candidates grow.
