---
status: verified
level: applied
base: scratch
label: Feature store
verified: 2026-08-07
---

# The feature store makes training and serving read the same number

**Question:** every stage so far assumed the ranker scores what the model
learned. This stage introduces the feature store and answers: a feature
computed once at ingestion and served unchanged to both training and
serving keeps the two sides looking at the same world, while recomputing
on read lets them drift apart.

**Before this:** [stage 08 — serving](../08-serving/) for the two-stage
serving path this store feeds, and [stage 04 — fine-rank](../04-fine-rank/)
for the features the model trains on.

## The store versus the naive read, executed

The run ([record](runs/2026-08-07-feature-store.md)) reads the same three
items at serve time, hour 5, twice:

| item | price | store age | store score | naive age | naive score |
|---|---|---:|---:|---:|---:|
| P1001 | \$49 | 0h | 17.5 | 5h | 12.5 |
| P1002 | \$89 | 0h | -2.5 | 3h | -5.5 |
| P1003 | \$19 | 0h | 11.5 | 4h | 7.5 |

The prices are identical on both paths. What differs is the age feature:
the store serves the ingestion-time value (0 hours for every item), the
naive path serves the current age (3-5 hours). The score function rewards
freshness, so the naive path reorders P1002 and P1001 on a feature the
model never trained on.

## The mechanism, named

A feature is a fact about the world, and the world moves. The store
freezes the fact at ingestion and serves that frozen value to both
training and serving, so the model and the ranker agree by construction.
The naive alternative computes the feature on every read, which means
training sees one value and serving sees another whenever anything
changed in between. The divergence is not a model bug — it is the two
reads disagreeing about the world, and the store is the boundary that
stops the disagreement before it reaches the ranker.

## Why this belongs in the mission

The mission's cascade is a chain of scores, and a score is only as good
as the feature behind it. Stage 04 trained a fine-ranker on features;
stage 08 served it. This stage closes the gap between those two moments:
the store is what makes "the model trained on X" and "the ranker scores
with X" the same sentence. Without it, every later stage — calibration,
experiments, monitoring — argues with data the model never saw.

## Evidence boundary

The executed read over three declared items (illustrative, deterministic).
It demonstrates the mechanism; real feature stores must decide how
staleness is tolerated per feature, which values are recomputed online,
and how the store's write path stays consistent with the training
snapshot — all measured on the live pipeline.

## Check your mental model

Answer each before opening it.

**1. Why does the naive path reorder the slate even though the prices
are unchanged?**

<details>
<summary>Answer</summary>

Because the age feature moved. P1001 is 5 hours old on the naive path
and 0 on the store path, which drops its score from 17.5 to 12.5 and
lets P1002 pass it. The items did not change; the feature's read did.
That is the divergence the store exists to prevent.

</details>

**2. Where does the store's guarantee end?**

<details>
<summary>Answer</summary>

It guarantees the two reads agree with each other, not that either read
is current. If the world moved after ingestion, both sides share the
stale value — consistently wrong. Freshness is a separate decision
(stages 44 and 46), and the store is the layer that keeps the two
decisions from colliding.

</details>

## Next

The store guarantees identical reads; stage 44 asks what happens when the
logged world and the live world disagree anyway. A detour from here: [the
feature diverges and the ranker reorders on a value the model never
saw](when-the-feature-diverges/) — the executed read shows training order
and serve order disagreeing on the same items.

Another detour: [a missing feature default is a silent ranking
decision](when-the-feature-is-missing/) — the executed read: a default
price of zero promotes the item as if it were free, to the top.
