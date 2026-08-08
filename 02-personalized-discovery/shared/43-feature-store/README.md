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

## How you find it: the as-of audit, executed

The failure is silent: nothing crashes when a read bypasses the store,
and a rank that moved is hard to trace back to a feature. The check that
finds it is an as-of audit — compare, per key, the value the model was
trained on against the value the serving read returned. The run
([record](runs/2026-08-07-store-consistency.md)) emits both reads as JSON
and audits them the way a serving team audits a live store:

| feature | keys | mean served-vs-trained delta | max delta |
|---|---|---:|---:|
| age_hours | 3 | +4.00 | +5.00 |
| category_ctr | 3 | +0.00 | +0.00 |
| price | 3 | +0.00 | +0.00 |

The verdict is DIVERGENT: three keys — P1001, P1002, P1003 on
`age_hours` — were served a value the model never trained on, and the
audit names the feature, not just the symptom. The point-in-time
discipline is the one Airbnb's Zipline encodes in its training
backfills: every training value must be exactly the value a serving read
at that moment would have returned (Simha and Hoh, "Zipline: Airbnb's
Machine Learning Data Management Platform", Strata Data Conference New
York, 2018). The audit is a standing check, run on every
training-snapshot-to-serving comparison, because the alternative is
discovering the divergence in a production rank change you cannot
explain.

## The fix and its trade

The fix is the store itself: freeze each feature at ingestion and serve
that frozen value to both training and serving, with the as-of audit as
the standing regression check. The executed read prices the repair — the
store path serves the 0-hour age the model trained on, while the naive
path serves 3-5 hours and reorders P1002 past P1001 on a feature the
model never saw — and the audit names the divergence per feature
(`age_hours` mean served-vs-trained delta +4.00, max +5.00, DIVERGENT)
before it becomes an unexplained production rank change.

The trade is that the store guarantees consistency, not freshness: if
the world moves after ingestion, both sides share the stale value —
consistently wrong, which is a different failure from the divergence
this stage fixes. Freshness is a separate decision owned by stages 44
and 46, and the refresh cadence prices it — a promo that lands mid-hour
is served stale for 22 of 24 hours on a daily refresh and zero hours on
streaming. The store also costs a per-feature contract: the feature
owner must declare the default and the latency class, because a value
that tolerates the batch lane buys cheap reads and a value that needs
realtime buys the request path, and choosing wrong is a silent ranking
decision.

## Who owns the loop

The store sits between three owners, and the failure mode is born when
their handoffs are implicit:

- **The feature owner** (the team that knows what the value means) owns
  the frozen value, its default, and its latency class — whether the
  value must be served from the realtime lane or tolerates the daily
  batch. Zipline's published serving requirements state the range
  explicitly: point lookups under 10 milliseconds, freshness from one
  second for realtime features down to midnight for snapshot-accurate
  ones.
- **The serving team** owns the read path: every live read must go
  through the store, never through a recompute. The audit above is its
  regression test.
- **The training platform** owns the snapshot and the backfill: the
  training value is read from the same store, at the same timestamp, so
  the comparison the audit makes is meaningful.

When the ownership is implicit, each side assumes the other keeps the
two reads consistent, and the divergence survives. The failure is a
handoff problem as much as a data problem — which is why the as-of audit
is a platform job, not a model team's afterthought.

## Why this belongs in the mission

The mission's cascade is a chain of scores, and a score is only as good
as the feature behind it. Stage 04 trained a fine-ranker on features;
stage 08 served it. This stage closes the gap between those two moments:
the store is what makes "the model trained on X" and "the ranker scores
with X" the same sentence. Without it, every later stage — calibration,
experiments, monitoring — argues with data the model never saw.

## Evidence boundary

The executed reads over three declared items (illustrative,
deterministic). They demonstrate the mechanism and the audit; real
feature stores must decide how staleness is tolerated per feature (the
online-value-moves detour), which values are recomputed online, and how
the store's write path stays consistent with the training snapshot — all
measured on the live pipeline. Sculley et al. (2015), "Hidden Technical
Debt in Machine Learning Systems" (NeurIPS), name the general pattern:
the training-serving skew is one of the debts that looks like glue code
until it silently moves a production decision.

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
(stages 44 and 46, and the online-value-moves detour), and the store is
the layer that keeps the two decisions from colliding.

</details>

**3. Whose job is the as-of audit?**

<details>
<summary>Answer</summary>

The training platform's, as a standing check on every backfill: compare
each training value against what a serving read at that moment would
return, and name the feature when they differ. The serving team keeps
every live read on the store path; the feature owner declares the
default and the latency class. When the audit is nobody's job, the
divergence is discovered in a production rank change nobody can explain.

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

A third detour: [the store freezes a value; the refresh decides how stale
it gets](when-the-online-value-moves/) — the executed read: a promo that
lands mid-hour is served stale for 22 of 24 hours on a daily refresh and
zero hours on streaming.
