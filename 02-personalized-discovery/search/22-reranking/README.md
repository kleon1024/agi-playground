---
status: verified
level: applied
base: scratch
label: Reranking
verified: 2026-08-07
---

# The second ranker that fixes the first

**Question:** [stage 12's ranking](../12-search-ranking/) ordered the
candidates, but with cheap features only. This stage asks what a second,
more expensive ranker buys, and answers: a better order for the few
documents the budget can afford to re-score.

**Before this:** [stage 12 — search ranking](../12-search-ranking/) for
the first-stage ranker, and [stage 20 — dense retrieval](../20-dense-retrieval/)
for the candidate set it ranks.

## The reorder, executed

The run ([record](runs/2026-08-07-reranking.md)) reorders a five-
document list with a reranker that uses richer features:

| order | list |
|---|---|
| first stage | d1, d2, d3, d4, d5 |
| reranker | d4, d2, d5, d1, d3 |
| positions changed | 4/5 |

d4 jumps from 4th to 1st; d5 from 5th to 3rd.

## The mechanism, named

The first stage ranks every candidate with features cheap enough to
score at scale; the reranker re-orders the top-k with features the first
stage cannot afford. The run shows the division in one number: four of
five positions change. The first stage recalls, the reranker refines —
the split is a latency budget decision, not a preference for one model
over the other.

## Why this belongs in the mission

This is search's version of [the mission's pre-rank/fine-rank
split](../../shared/03-pre-rank/): a cascade where each stage buys the next a
smaller problem. Stage 12 ranked the candidates once; this stage adds
the second pass whose pool size — the rerank budget — is the tuning
decision that decides how much of the first stage's verdict survives.

## Evidence boundary

The executed reorder over five hand-built documents with declared
first-stage and reranker scores (illustrative, deterministic). It
demonstrates the mechanism; real reranking cost is measured as p95
latency, and the pool size is the budget decision the
[tight-budget detour](when-the-rerank-budget-is-tight/) prices.

## Check your mental model

Answer each before opening it.

**1. Why does d4 jump from 4th to 1st?**

<details>
<summary>Answer</summary>

Because the reranker uses features the first stage cannot afford. The
first stage's order is a cheap approximation of quality; the reranker's
is the better estimate that the budget buys for a small pool. The jump
is the entire reason the second ranker exists.

</details>

**2. What decides how many documents the reranker sees?**

<details>
<summary>Answer</summary>

The latency budget. Reranking is expensive, so the pool is a top-k —
the [tight-budget detour](when-the-rerank-budget-is-tight/) shows a
document with a 0.99 reranker score that is unreachable at k=3 or k=4.
The cutoff is a filter on what the reranker can fix.

</details>

## Next

Forward to [stage 23 — personalized search](../23-personalized-search/)
where the ranking gains a user.

A detour from here: [the cutoff decides what the reranker can
fix](when-the-rerank-budget-is-tight/) — the executed cutoff read: a
document with a 0.99 reranker score is unreachable at k=3 and k=4 and
only seen at k=5, so a tight rerank budget hides recall.

Another detour: [disagreement is the reranker's job and its
risk](when-the-reranker-disagrees/) — the executed comparison read: the
first stage and the reranker disagree on the top-3, which is the
reranker's reason to exist and the risk that anything outside the
reranked pool keeps the cheaper verdict.
