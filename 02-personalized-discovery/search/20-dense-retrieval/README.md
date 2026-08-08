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

## How you find it: the stale-embedding audit, executed

The embedding is the index, but the index has a freshness problem: the
doc vectors are re-trained on a schedule, and between runs the served
snapshot is stale. The failure mode the aggregate hides is the query
whose recall silently degrades against a stale index — and the mean
gap cannot see it. The run ([record](runs/2026-08-07-dense-audit.md))
emits a 20-query log, scores each query against fresh and stale doc
embeddings, and stratifies the gap:

| stratum | queries | fresh recall@5 | stale recall@5 | gap |
|---|---:|---:|---:|---:|
| head | 10 | 1.000 | 0.940 | -0.060 |
| tail | 10 | 1.000 | 0.400 | -0.600 |

The verdict is STALE EMBEDDING DIVERGES IN THE TAIL: the aggregate gap
is -0.330 and the snapshot looks usable, but every unit of the loss is
tail recall. Head queries survive a stale index; tail queries — rare
terms with few training examples — lose most of their retrieval. Huang
et al. ("Embedding-based Retrieval in Facebook Search", KDD 2020, pages
2553-2561) is the industrial reference for two-tower retrieval in
production search, including the training-data choices (hard negative
sampling between ranks 101-500) that determine how well the tail is
represented in the first place. The decision that follows: embedding
freshness is a tail decision — refresh for the tail, or fall back to
the hybrid path in [stage 21](../21-hybrid-fusion/) for the queries the
stale vectors cannot serve.

## The fix and its trade

The fix is to treat embedding freshness as a tail decision — refresh for
the tail, or fall back to the hybrid path for the queries a stale vector
set cannot serve — and to audit the fresh-versus-stale gap by stratum.
The executed audit prices the failure the fix removes: head queries
survive a stale index (fresh recall@5 1.000 to stale 0.940, gap -0.060)
while tail queries lose most of their retrieval (1.000 to 0.400, gap
-0.600) — the aggregate gap of -0.330 makes the snapshot look usable
while every unit of the loss is tail recall. Huang et al. (KDD 2020)
document the industrial two-tower design at Facebook search, including
the hard-negative sampling between ranks 101-500 that decides how well
the tail is represented in the first place.

The trade, named: the vector space is the index, and its quality is the
training data — better tail representation costs harder negative
sampling and more training data, and freshness costs embedding-run
compute on every schedule change. The alternative to both, hybrid
fusion (stage 21), keeps coverage by letting the lexical path carry the
queries the stale vectors cannot, at the price of a fusion rule that
must be measured.

## Who owns the loop

The vector space is the retrieval index; someone must own what serves
it, and the handoffs are where dense retrieval fails:

- **The dense-retrieval model team** owns the towers: the training
  data, the negative sampling that decides tail representation, and
  the space's quality — including the anisotropy check that catches a
  space that stopped separating. It owns the model, and the
  when-everything-is-equidistant detour is its failure mode.
- **The serving or indexing team** owns the snapshot that actually
  answers queries: the embedding run schedule, the fresh-versus-stale
  gap, and the decision of which queries are safe on a stale index. It
  owns freshness, and the audit's tail verdict is its signal.
- **The evaluation or relevance team** owns the recall@k measurement
  and its strata: head/tail split, per-query curves, and the
  offline/online consistency check that catches divergence before
  traffic does. It owns the measurement, and the when-the-index-is-ann
  detour is its scale constraint.

When the ownership is implicit, the model team ships towers, the
serving team serves a stale snapshot, and nobody owns the tail — so
the aggregate consistency check approves an index that has silently
lost 60% of its tail recall.

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

And a third: [the embedding space that stopped separating](when-everything-is-equidistant/) — when training pulls every vector into the
same cone, all cosines converge and the dense ranking becomes a
frequency order; the check is the served similarity distribution.
