---
status: verified
level: applied
base: scratch
label: Hybrid fusion
verified: 2026-08-07
---

# Two retrieval sets, one answer list

**Question:** [stage 11's BM25](../11-search-retrieval/) and [stage
20's dense retrieval](../20-dense-retrieval/) each have a blind spot.
This stage asks how two candidate sets become one answer list, and
answers with reciprocal rank fusion: keep the union, reward the
documents both matchers agree on.

**Before this:** [stage 11 — search retrieval](../11-search-retrieval/)
and [stage 20 — dense retrieval](../20-dense-retrieval/) for the two
matchers being fused.

## The fusion, executed

The run ([record](runs/2026-08-07-hybrid-fusion.md)) fuses a lexical
list `[d1, d2, d3, d4]` and a dense list `[d4, d5, d1, d6]`:

| document | fusion score | ranked by |
|---|---:|---|
| d1 | 0.0323 | lexical#1, dense#3 |
| d4 | 0.0320 | lexical#4, dense#1 |
| d2 | 0.0161 | lexical#2 |
| d5 | 0.0161 | dense#2 |
| d3 | 0.0159 | lexical#3 |
| d6 | 0.0156 | dense#4 |

## The mechanism, named

Reciprocal rank fusion gives each matcher's rank a score of
1/(k + rank) and sums across matchers. Two consequences fall out of the
run:

1. **Agreement is rewarded.** d1 and d4 appear in both sets and score
   roughly double the survivors.
2. **The union is preserved.** d2/d3 survive only from lexical and
   d5/d6 only from dense — nothing a matcher retrieved is dropped.

That is the point of hybrid search: coverage without choosing a blind
spot, with shared confidence ranked first.

## Why this belongs in the mission

[Stage 02's rule](../../shared/02-recall/) — a perfect ranker cannot rank an item
that was never retrieved — applies to search verbatim. Hybrid fusion is
how production search keeps both matchers' coverage: the first stage of
the funnel retrieves with every method it has, and downstream ranking
works on the union.

## Evidence boundary

The executed fusion over two hand-built lists (illustrative,
deterministic, equal-weight matchers). It demonstrates the mechanism;
real fusion also needs score calibration between matchers and a health
check per set — the [empty-set detour](when-one-set-is-empty/) shows
what happens without it.

## Check your mental model

Answer each before opening it.

**1. Why do d1 and d4 score roughly double the survivors?**

<details>
<summary>Answer</summary>

Because reciprocal rank fusion sums each matcher's contribution. A
document ranked by both matchers collects two terms; a document in one
set collects one. The fusion is designed so that agreement — both
matchers confident in the same document — is worth more than either
alone.

</details>

**2. Why not just concatenate the two lists?**

<details>
<summary>Answer</summary>

Concatenation keeps coverage but throws away rank information and
duplicates. Fusion keeps the union while making shared documents rise,
so the merged list reflects both matchers' confidence instead of
whichever list happened to be appended second.

</details>

## Next

Forward to [stage 22 — reranking](../22-reranking/) where the fused
list meets a second, more expensive ranker.

A detour from here: [the fusion weight is a trust decision](when-the-fusion-weight-moves/) — the executed weight sweep read: at w=0 the
dense-only winner (d2) takes the top slot, at w=1 the lexical-only
winner (d1) does, so the weight is the product decision about how much
the platform trusts meaning versus exact terms.

Another detour: [the hybrid degrades into whoever is alive](when-one-set-is-empty/) — the executed degradation read: with the dense set
empty the fusion is exactly the lexical ranking, so fusion needs a
health check per matcher.
