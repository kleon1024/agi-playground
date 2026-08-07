---
status: verified
level: applied
base: scratch
label: When the reranker disagrees
verified: 2026-08-07
---

# Disagreement is the reranker's job and its risk

**Question:** [stage 22's reranking](../) adds a second ranker after
the first stage. This chapter reads the executed comparison of the two
orders and asks what their disagreement means.

**Before this:** [stage 22 — reranking](../) and its executed reorder
model.

## The comparison, executed

The run ([record](runs/2026-08-07-reranker-disagrees-read.md)) ranks the
same documents with both models:

| order | list |
|---|---|
| first stage | d1, d2, d4, d3, d5 |
| reranker | d3, d2, d5, d4, d1 |
| same top-3 | False |

## The reading

The first stage ranks by cheap signals, the reranker by rich ones, and
they disagree on the top-3. The disagreement is the point — if they
always agreed, the reranker would be dead weight. It is also the risk:
the budget only reranks a pool, and anything outside it keeps the first
stage's verdict. The disagreement is what makes the reranker worth its
latency, and the pool boundary decides how much of that better verdict
the system actually applies.

## Evidence boundary

The executed comparison over five hand-built documents with declared
scores (illustrative, deterministic). It demonstrates the disagreement;
real systems measure agreement per query class and tune the pool to the
queries where disagreement is valuable.

## Check your mental model

Answer each before opening it.

**1. Why is disagreement good news here?**

<details>
<summary>Answer</summary>

Because the reranker exists to improve on the first stage, and
improvement requires difference. If the two orders were identical, the
reranker would be replicating the cheaper model at extra latency. The
disagreement on d2/d3 is evidence the richer features are actually
changing the ranking.

</details>

**2. What makes the same disagreement a risk?**

<details>
<summary>Answer</summary>

The pool boundary. The reranker only reorders what it sees, so a
document outside the pool keeps the first stage's cheaper verdict even
when the reranker would have ranked it higher. Disagreement makes the
boundary matter: with perfect agreement, the pool size would be
irrelevant; with disagreement, it decides whose judgment wins.

</details>

## Next

Back to [stage 22](../), where the reranker refines the top-k. The
[tight-budget detour](../when-the-rerank-budget-is-tight/) prices the
boundary directly.
