---
status: verified
level: applied
base: scratch
label: When the embedding expires
verified: 2026-08-07
---

# The embedding expires and recall dies with it

**Question:** [stage 46's staleness](../) measures the model's snapshot
age. This chapter asks where the staleness hides when the model is
retrained, and answers: the embedding computed at ingestion is a dated
snapshot too, and retrain must reach the index, not just the weights.

**Before this:** [stage 46 — retraining and staleness](../) and its
executed aging-snapshot read, plus [stage 02 — recall](../../02-recall/)
for the retrieval this index serves.

## The stale index, executed

The run ([record](runs/2026-08-07-embedding-expires-read.md)) compares
similarity to the current query under stale and refreshed embeddings:

| item | stale sim | refreshed sim |
|---|---:|---:|
| P1001 | 0.81 | 0.30 |
| P1002 | 0.55 | 0.85 |
| P1003 | 0.42 | 0.78 |
| P1004 | 0.38 | 0.22 |
| P1005 | 0.25 | 0.60 |

Recall@3: 2/3 with stale embeddings, 3/3 with refreshed.

## The reading

The stale vectors were computed for the taste of the day they were
ingested; the refreshed ones match the current query. Recall recovers
from 2/3 to 3/3 — the embedding is a dated snapshot, and "retrain" must
reach the index, not just the model weights. The retrieval stage (02)
assumed the vectors describe the item; the expiry is the same staleness
as stage 46's main read, living in a different artifact, invisible to a
retrain that only touches the ranker.

## The fix and its trade

The fix is to make "retrain" reach the index, not just the model weights —
and to measure embedding freshness against current queries on the same
measured-gap principle as model retraining. The executed comparison prices
the failure: with stale vectors, recall@3 is 2/3; with refreshed vectors,
3/3. The mechanism is visible per item — P1001's stale similarity reads
0.81 where the refreshed embedding says 0.30, and P1002/P1003/P1005
recover the other way — the vectors describe the taste of the day they
were ingested, not the current query.

The trade, named: index rebuilds cost compute, pipeline load, and cache
invalidation, and they must be scheduled against a freshness read — the
alternative is a retrain that touches only the ranker while a dated
snapshot keeps serving retrieval, which is the same staleness as the
stage's main read living in a different artifact. The panel that names
when a cohort is due (the stage's VOLATILE FIRST read) is the same
measurement applied to embeddings: the expiry is per-artifact, and each
artifact needs its own trigger.

## Who owns the loop

- **The retrieval team** owns the index rebuild and its freshness schedule
  — the recall drop is their artifact's staleness.
- **The feature platform team** owns the embedding pipeline that refreshes
  the vectors on demand.
- **The monitoring team** owns the freshness read against current queries,
  so an expiring index is caught before recall visibly drops.

## Evidence boundary

The executed comparison over five declared items (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
embedding freshness against current queries and schedule index rebuilds
on the same measured-gap principle as model retraining.

## Check your mental model

Answer each before opening it.

**1. Why does recall@3 drop even though the model weights are fresh?**

<details>
<summary>Answer</summary>

Because retrieval reads the index, and the index holds embeddings from
ingestion time. The vectors were computed for the taste of their day;
when the query moves on, the nearest neighbours move with it and the top-3
stops matching. Retraining the ranker does not touch the index, so the
recall failure survives any weight update.

</details>

**2. How is this the same failure as the main staleness read?**

<details>
<summary>Answer</summary>

Both are snapshots aging against a moving world — the ranker's weights
against drifting CTRs, the index's vectors against drifting taste. The
only difference is the artifact. That is why the fix has the same shape:
measure the gap between the snapshot and the current truth, and rebuild
when the gap grows, not on a calendar.

</details>

## Next

Back to [stage 46](../). The [retrain-flips-the-metric
detour](../when-retraining-flips-the-metric/) is the other place a
retrain can mislead: the offline metric itself inheriting the old
policy's log.
