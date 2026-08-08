---
status: verified
level: applied
base: scratch
label: When the rerank budget is tight
verified: 2026-08-07
---

# The cutoff decides what the reranker can fix

**Question:** [stage 22's reranking](../) reorders the first stage's
top-k. This chapter reads the executed cutoff sweep and asks what a
tight rerank budget hides.

**Before this:** [stage 22 — reranking](../) and its executed reorder
model.

## The cutoff, executed

The run ([record](runs/2026-08-07-tight-rerank-read.md)) varies the
pool size k for a document with a 0.99 reranker score:

| k | reranker sees d5 | reachable |
|---:|---|---|
| 3 | top 3 | False |
| 4 | top 4 | False |
| 5 | top 5 | True |

## The reading

With k=3 or k=4, d5 never reaches the reranker and its 0.99 score is
never seen; only k=5 lets it through. The first stage's cutoff is a
filter on what the reranker can fix — a tight budget hides recall. The
expensive model's value is capped by the pool the budget allows, so the
pool size is a quality decision, not an operational detail.

## The fix and its trade

The fix is to measure the recall lost at the pool boundary against the
latency saved, per query class — the pool size is a quality decision, not
an operational detail. The executed cutoff prices the failure: a
document with a 0.99 reranker score sits at position 5 of the first
stage, and with k=3 or k=4 the reranker never sees it — the score is
real but unreachable, and only k=5 lets it through. The first stage's
cutoff is a filter on what the reranker can fix: a tight budget hides
recall.

The trade, named: a tighter pool saves cross-encoder latency on every
request and loses the reranker's verdict on everything below the line —
the expensive model's value is capped by the pool the budget allows.
The operating point comes from the per-query-class measurement: queries
whose rerank gains sit deep in the first-stage order pay more for a
bigger pool than queries whose gains sit at the top.

## Who owns the loop

- **The serving and infrastructure team** owns the budget and the top-k
  cutoff it permits.
- **The ranking team** owns the recall-lost read at the pool boundary —
  a hidden 0.99 score is their artifact failing.
- **The evaluation team** owns the per-query-class latency-versus-recall
  measurement that sets the operating point.

## Evidence boundary

The executed sweep over one hand-built score list (illustrative,
deterministic). It demonstrates the mechanism; real systems measure the
recall lost at the pool boundary against the latency saved per query
class.

## Check your mental model

Answer each before opening it.

**1. Why can a 0.99 reranker score be invisible?**

<details>
<summary>Answer</summary>

Because the reranker only sees the first stage's top-k. If d5 ranks
fifth or lower in the first stage and k is 4, the reranker never scores
it — the 0.99 is real but unreachable. The first stage's verdict is the
filter the reranker cannot overturn for documents outside the pool.

</details>

**2. What is the trade the pool size represents?**

<details>
<summary>Answer</summary>

Latency against recall. Every extra document the reranker scores costs
its per-document latency, and every document excluded keeps the first
stage's cheaper verdict. The budget buys a pool, and the pool boundary
decides how much reranker-quality the system can afford per request.

</details>

## Next

Back to [stage 22](../), where the reranker refines the top-k. The
[disagreement detour](../when-the-reranker-disagrees/) shows the other
side: when the two rankers disagree, the pool boundary decides whose
verdict survives.
