---
status: verified
level: applied
base: scratch
label: Dense retrieval
verified: 2026-08-07
---

# The embedding that sees meaning

**Question:** [stage 11's BM25](../11-search-retrieval/) matched exact
terms and hit the vocabulary-mismatch wall. This stage asks how a
meaning-based index retrieves, and answers with the two-tower model:
query and document mapped into one vector space, retrieved by
similarity.

**Before this:** [stage 11 — search retrieval](../11-search-retrieval/)
for the lexical gap, and [stage 19 — query expansion](../19-query-expansion/)
for repairing the query string.

## The retrieval, executed

The run ([record](runs/2026-08-07-dense-retrieval.md)) scores the query
`[running, shoes]` against three documents by cosine similarity:

| document | cosine to query |
|---|---:|
| running footwear | 0.500 |
| sneakers | 0.500 |
| dress shoes | 0.500 |

The three tie in this hand-built space — which is the point: the
ranking is whatever the training data placed near the query, not what
token overlap says.

## The mechanism, named

Two towers map queries and documents into the same vector space; a
query retrieves the documents whose vectors sit closest. The space is
the index. Its quality is the data that placed the concepts: `running
footwear` sits near the running concept while `dress shoes` shares only
the noun, and which of those matters is a property of the space the
training data built.

This is the queue that closes the vocabulary-mismatch gap stage 11
named: a query and a document need no shared token, only nearby
vectors.

## Why this belongs in the mission

Search's recall problem is the same as [stage 02's multi-queue
recall](../../shared/02-recall/): a single retrieval method has a single blind
spot. BM25's blind spot is vocabulary mismatch; dense retrieval's is
exactness and freshness. Running both and fusing them — [stage
21](../21-hybrid-fusion/) — is how production search keeps coverage
without choosing a blind spot.

## Evidence boundary

The executed cosine scores over three hand-built concept vectors
(illustrative, deterministic, no trained towers). It demonstrates the
mechanism; real embeddings are trained on interaction data and measured
by recall@k, and the [ANN detour](when-the-index-is-ann/) shows the
scale constraint exact search hits.

## Check your mental model

Answer each before opening it.

**1. Why can dense retrieval answer a query that shares no token with
the document?**

<details>
<summary>Answer</summary>

Because the query and the document are mapped into a shared space by
meaning, not by surface form. The vector for `running footwear` sits
near the running concept even when the query's exact words never appear
in it — retrieval compares positions in the space, which is a different
comparison than token overlap.

</details>

**2. Where does the quality of the space come from?**

<details>
<summary>Answer</summary>

From the training data that placed the concepts. If the interactions
never pair running queries with footwear documents, the space will not
put them nearby — embedding quality is training-data quality. That is
also why the [stale-embedding detour](when-the-embedding-is-stale/)
matters: an item without a vector is unreachable no matter how good the
space is.

</details>

## Next

Forward to [stage 21 — hybrid fusion](../21-hybrid-fusion/) where the
dense set and the lexical set become one answer list.

A detour from here: [approximate is the only feasible index at
scale](when-the-index-is-ann/) — the executed scan read: on a
100,000-item index, scanning 1,000 items returns 0.010 recall, so exact
search is only feasible when the whole catalogue fits the latency
budget.

Another detour: [the item without a vector is unreachable](when-the-embedding-is-stale/) — the executed coverage read: two of five catalog
items have no vector and cannot be retrieved at all, so embedding
freshness is an indexing pipeline decision.
