---
status: verified
level: applied
base: scratch
label: When the dense path exists
verified: 2026-08-06
---

# The embedding that sees the synonym

**Question:** [stage 11's BM25 index](../) fails on synonyms. This chapter
reads the executed embedding contrast and makes the dense fix concrete.

**Before this:** [stage 11 — search retrieval](../) and
[the synonym that lexical retrieval cannot see](../when-the-synonym-is-invisible/).

## The contrast, executed

The run ([record](runs/2026-08-06-dense-contrast.md)) computes cosine
similarity between the query and three documents:

| document | cosine with "running shoes" |
|---|---:|
| doc_running_shoes | 0.816 |
| doc_running_footwear | 0.408 |
| doc_headphones | 0.000 |

## Two readings

**The embedding scores meaning, not spelling.** doc_running_footwear
shares the concept 'running' and its 'footwear'/'athletic' terms embed
near 'shoes', so dense similarity is meaningful where BM25 scored low.
The vector places the synonym beside the word it means.

**Hybrid search is the production answer, not a choice between the two.**
BM25 catches exact terms and entities; dense catches meaning. The two
fail differently — the synonym case here, the exact-entity case in
reverse — so production search runs both and fuses the candidate sets.
The contrast is the mechanism that makes hybrid a design rather than an
afterthought.

## The fix and its trade

The fix is hybrid search: run BM25 and the dense path, and fuse the two
candidate sets with an explicit rule. The executed contrast prices why
neither path alone suffices: the embedding scores meaning, not spelling —
cosine similarity is 0.816 for doc_running_shoes, 0.408 for
doc_running_footwear (the synonym doc BM25 under-ranked), and 0.000 for
doc_headphones. The vector places the synonym beside the word it means,
where the lexical index left it half-scored.

The trade, named: hybrid costs a trained embedding model, a dense index,
and the fusion rule — and the two paths fail differently, which is the
reason both must run. Dense blurs exact entities (a product code or model
number embeds near unrelated terms), where BM25 is exact; BM25 misses
meaning, where dense is exact. The fusion rule is the decision point:
how a query is split between the two candidate sets determines which
failure the user sees, and it must be measured on a real corpus rather
than assumed.

## Who owns the loop

- **The retrieval team** owns the fusion rule and the per-query split
  between the lexical and dense paths.
- **The embedding and model team** owns the trained vectors, their index,
  and their refresh schedule.
- **The relevance team** owns the graded labels that measure whether the
  fused candidate set serves meaning and exact entities in the right
  proportions.

## Evidence boundary

The executed hand-built concept-vector contrast (illustrative,
deterministic — a bag-of-concepts stand-in for real embeddings). It
demonstrates the mechanism; real dense retrieval trains embeddings on
large corpora.

## Check your mental model

Answer each before opening it.

**1. Why is the footwear doc's similarity 0.408, not higher?**

<details>
<summary>Answer</summary>

Because it shares only part of the query's meaning. The query vector
carries 'shoes' and 'running'; the footwear doc carries 'running',
'footwear', and 'athletic' — one shared concept out of two in the query,
scaled by the doc's extra terms. Cosine is a proportion, so partial
overlap yields partial similarity, which is exactly the graded behavior a
retrieval stage wants.

</details>

**2. What does the headphones zero mean for hybrid?**

<details>
<summary>Answer</summary>

That dense retrieval also has a zero — the query 'running shoes' shares no
concept with 'headphones'. The failure is different from BM25's (no
synonym to miss, just no relation), but it confirms neither matcher alone
is complete. Hybrid fuses the two candidate sets so each covers what the
other cannot see.

</details>

## Next

Back to [stage 11](../), or to
[stage 12 — search ranking](../../12-search-ranking/) where the fused
candidate set is re-ordered.
