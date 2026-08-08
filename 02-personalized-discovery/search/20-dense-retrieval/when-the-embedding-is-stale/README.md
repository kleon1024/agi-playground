---
status: verified
level: applied
base: scratch
label: When the embedding is stale
verified: 2026-08-07
---

# The item without a vector is unreachable

**Question:** [stage 20's dense retrieval](../) ranks by embedding
similarity. This chapter reads the executed coverage check and asks
what happens to items between embedding runs.

**Before this:** [stage 20 — dense retrieval](../) and its executed
cosine model.

## The coverage, executed

The run ([record](runs/2026-08-07-stale-embedding-read.md)) checks the
catalog against the vector store:

| item | embedded | reachable |
|---|---|---|
| item_a | True | yes |
| item_b | True | yes |
| item_c | True | yes |
| item_d | False | no |
| item_e | False | no |

Catalog: 5 items, 3 with vectors.

## The reading

Retrieval can only return what has a vector. item_d and item_e are
unreachable by dense retrieval whatever their relevance, because they
wait for the next embedding run — and their wait is a recall loss for
every query they would have answered. Embedding freshness is an
indexing pipeline decision, not a model detail: the gap between
embedding runs, and the queue of new items waiting in it, is where
dense retrieval quietly loses coverage.

## The fix and its trade

The fix is to measure time-to-vector for new items and its recall cost
per query class — embedding freshness is an indexing pipeline decision,
not a model detail. The executed coverage check prices the failure:
the five-item catalog has only 3 vectors, and item_d and item_e are
unreachable by dense retrieval whatever their relevance, because they
wait for the next embedding run. Their wait is a recall loss for every
query they would have answered.

The trade, named: more frequent embedding runs cost compute and pipeline
load, and the gap between runs — plus the queue of new items waiting in
it — is exactly where dense retrieval quietly loses coverage. The same
staleness discipline as the retraining stage applies: the freshness
schedule should be derived from the measured recall cost per query
class, not from a fixed calendar, and the index rebuild must be
monitored against the catalog's arrival rate.

## Who owns the loop

- **The serving and indexing team** owns the embedding run schedule and
  the time-to-vector for new catalog items.
- **The dense-retrieval model team** owns the vector freshness contract
  and re-embeds when the recall cost is measured to be too high.
- **The evaluation team** owns the per-query-class recall read that
  converts a coverage gap into a recall number.

## Evidence boundary

The executed coverage check over a five-item hand-built catalog
(illustrative, deterministic). It demonstrates the mechanism; real
systems measure time-to-vector for new items and its recall cost per
query class.

## Check your mental model

Answer each before opening it.

**1. Why is a missing vector a recall loss, not a quality issue?**

<details>
<summary>Answer</summary>

Because retrieval never sees the item at all. A vector that is slightly
wrong still lets the item compete for ranking; no vector removes it
from the candidate set entirely. The item is unreachable no matter how
relevant it is — the failure is at recall, which downstream stages
cannot repair.

</details>

**2. Who owns embedding freshness?**

<details>
<summary>Answer</summary>

The indexing pipeline. The embedding model sets the space, but the
scheduler decides when new items get vectors — hourly, daily, on
publication. That scheduling decision sets the average wait, and the
wait is the recall loss. It is a pipeline decision with a measurable
coverage cost, not a model detail.

</details>

## Next

Back to [stage 20](../), which retrieves by embedding. The [ANN
detour](../when-the-index-is-ann/) shows the scale constraint on the
other side: how the index structure decides feasibility.
