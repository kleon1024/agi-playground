---
status: verified
level: applied
base: scratch
label: When the intent misroutes
verified: 2026-08-07
---

# The path decision costs relevance before ranking runs

**Question:** [stage 10's classifier](../) assigns one intent per query,
and that intent decides which retrieval path runs. This chapter measures
what a wrong assignment costs: when the candidate set is the wrong type,
no ranker downstream can recover.

**Before this:** [stage 10 — query understanding](../) for the classifier
and its rule order, and the stage's intent-mix [audit
run](../runs/2026-08-07-query-understanding-audit.md) for the
case-finding that names the failure first.

## The misroute, executed

The run ([record](runs/2026-08-07-misroute-read.md)) routes seven
queries by the classifier and measures NDCG@3 of the routed candidate
set against a fixed ideal (the oracle path's top three at the primary
grade):

| query | classifier intent | NDCG@3 | route |
|---|---|---:|---|
| buy nike running shoes | transactional | 1.0000 | correct |
| how to fix sleep schedule | informational | 1.0000 | correct |
| best wireless headphones 2026 | navigational | 1.0000 | correct |
| cheap how to fix iphone screen | transactional | 0.3333 | MISROUTED |
| how to buy iphone | transactional | 0.3333 | MISROUTED |
| redmi note 13 price vs poco x6 | transactional | 0.3333 | MISROUTED |
| nike or adidas | navigational | 0.3333 | MISROUTED |

## Two findings

**Every misroute is a query the keyword classifier cannot commit on.**
"cheap how to fix iphone screen" fires both transactional (cheap) and
informational (how, fix) keywords; the rule order checks transactional
first and silently routes to price-bearing results. "nike or adidas"
fires no keyword at all and falls back to navigational entity pages.
Either way the retrieval path changed and the candidate set is the
wrong type before ranking begins — the stage's own claim, now measured:
NDCG@3 drops from 1.0000 to 0.3333.

**The collision and the fallback are the same failure with two
signatures.** The audit counts both: all three collisions are tail
queries (15% of tail vs 0% of head), and five of six no-keyword tail
queries want comparison or guide content the navigational fallback
cannot route. The fix is either a confidence-aware intent model with an
explicit ambiguous bucket, or dual-path retrieval that carries both
candidate types and lets the ranker decide. The trade is structural:
dual-path retrieval guarantees the right type is present but raises
candidate count per query, pushing the disambiguation downstream where
[stage 12's ranker](../../12-search-ranking/) can use features, not
keyword order.

## The fix and its trade

The fix is either a confidence-aware intent model with an explicit
ambiguous bucket, or dual-path retrieval that carries both candidate
types and lets the ranker decide. The executed routing prices the
failure: four of seven queries misroute and NDCG@3 drops from 1.0000 to
0.3333 — every misroute is a query the keyword classifier cannot commit
on ("cheap how to fix iphone screen" fires transactional and
informational, and the rule order checks transactional first; "nike or
adidas" fires no keyword and falls back to navigational entity pages).
The candidate set is the wrong type before ranking begins.

The trade, named: dual-path retrieval guarantees the right type is
present but raises candidate count per query, pushing disambiguation
downstream where stage 12's ranker can use features instead of keyword
order — the structural price is more expensive-stage traffic. The
ambiguous-bucket alternative costs a defined fallback and a confidence
floor, and trades a confident wrong route for a hedge that the retrieval
path must honor.

## Who owns the loop

- **The query-understanding team** owns the confidence floor and the
  ambiguous bucket — the misroute rate is their acceptance number.
- **The retrieval team** owns the dual-path contract and the fallback
  behavior when a query is declared ambiguous.
- **The ranking team (stage 12)** owns the disambiguation features that
  decide between the carried candidate types.

## Evidence boundary

The corpus is a hand-built synthetic set of thirteen type-tagged docs
and seven queries with declared oracle intents (illustrative,
deterministic). It measures the mechanism — path routing decides the
candidate set — not a real query log's misroute rate, which the
stage-10 audit would need labeled production traffic to estimate.

## Check your mental model

Answer each before opening it.

**1. Why does a correct path always score 1.0000 in this read?**

<details>
<summary>Answer</summary>

Because NDCG@3 is normalized against the oracle path's ideal, and a
correct route returns the primary-type docs at grade 3 for all three
top slots. A misroute scores 0.3333 not because the wrong path is
"somewhat relevant" but because its docs earn only the adjacent grade
(1) against the same ideal — the wrong type cannot normalize itself to
perfect by being uniformly weak.

</details>

**2. What does dual-path retrieval buy, and what does it cost?**

<details>
<summary>Answer</summary>

It buys presence: the correct candidate type is guaranteed to be in the
set even when intent is ambiguous, so ranking — not keyword rule order
— decides. It costs candidate count: every query now fetches more than
one type, and the ranker carries the disambiguation load, which is
exactly the latency-and-quality trade the advanced track's
[hybrid fusion](../../21-hybrid-fusion/) stage measures.

</details>

## Next

Back to [stage 10](../), or forward to
[stage 11 — search retrieval](../../11-search-retrieval/) where the
routed query hits the BM25 index.
