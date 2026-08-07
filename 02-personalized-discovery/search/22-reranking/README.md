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

## How you find it: the served-k audit, executed

The reranker is evaluated offline at one k and serves another, and the
failure mode the aggregate hides is the k that disagrees with the page.
The run ([record](runs/2026-08-07-rerank-audit.md)) emits a 20-query
log with first-stage and reranked NDCG@10 and NDCG@3, and compares the
two surfaces:

| stratum | queries | delta@10 | delta@3 | agree? |
|---|---:|---:|---:|---|
| head | 10 | +0.080 | +0.050 | yes |
| tail | 10 | +0.080 | -0.080 | NO |

The verdict is SERVING-K DIVERGENCE: the @10 experiment approves the
reranker (aggregate +0.080) while the served @3 report says the page
got worse (-0.015), and the entire loss is tail — the reranker's fixes
land in the middle of the list, below the three served slots. Nogueira
and Cho ("Passage Re-ranking with BERT", arXiv:1901.04085, 2019) is the
cross-encoder reranker production systems deploy; its cost is why the
shortlist is short and the served page shorter. The decision that
follows: report at the served k, audit per position, and slice the
rerank experiment by head and tail before shipping.

## Who owns the loop

The reranker changes the order the user sees; someone must own the k
that decides what reaches the page, and the handoffs are where
reranking fails:

- **The ranking team** owns the reranker: the features it trusts, the
  pool size, and the served-k evaluation that decides whether a change
  ships. It owns the model, and the when-the-reranker-disagrees detour
  is its failure mode.
- **The serving or infrastructure team** owns the budget: the top-k
  cutoff and the p95 latency that constrain how many documents the
  reranker can re-score. It owns the pool, and the
  when-the-rerank-budget-is-tight detour is its constraint.
- **The evaluation or product team** owns the surface contract: what k
  the page actually serves, and the @10-versus-@3 audit that catches a
  reranker whose gains never reach a user. It owns the metric, and the
  when-the-gain-is-below-the-fold detour is its failure mode.

When the ownership is implicit, the ranking team reports @10, the
serving team ships the pool, and nobody owns the served k — so a
reranker that fixes the middle of the list ships as an improvement
while the tail's top-3 silently gets worse.

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

And a third: [the improvement the page never shows](when-the-gain-is-below-the-fold/) — a reranker that fixes positions 4-10 improves
NDCG@10 from 0.9592 to 0.9758 while the three-slot page worsens from
1.0000 to 0.9677; the eval k and the served k disagree.
