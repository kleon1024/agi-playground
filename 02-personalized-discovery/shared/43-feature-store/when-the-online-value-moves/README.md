---
status: verified
level: applied
base: scratch
label: When the online value moves
verified: 2026-08-07
---

# The store freezes a value; the refresh decides how stale it gets

**Question:** [stage 43's store](../) guarantees identical reads. This
chapter asks a second question the store does not answer — how stale is
the frozen value allowed to become — and measures the answer: a promo
price that changes mid-hour is served at the old price until the next
refresh, and the refresh interval, not the model, decides how many hours
the rank is wrong.

**Before this:** [stage 43 — feature store](../) for the frozen read this
chapter ages, and [stage 46 — retraining and staleness](../../46-retraining-and-staleness/)
for the sibling decision of how old a model snapshot is allowed to get.

## The refresh trade, executed

The run ([record](runs/2026-08-07-online-value-moves.md)) drops P1002's
price from \$89 to \$59 mid-hour-2 and counts, for each refresh policy,
how many of the next 24 hours the served rank disagrees with the live
truth:

| refresh | stale hours | wrong pairs | pair-hours |
|---|---:|---:|---:|
| 1h batch | 1 | 1 | 1 |
| 4h batch | 2 | 1 | 2 |
| 8h batch | 6 | 1 | 6 |
| 24h batch | 22 | 1 | 22 |
| streaming | 0 | 0 | 0 |

## The reading

The store's guarantee is identical reads, not current reads. With a
daily refresh the promo price is served stale for 22 of 24 hours, and
P1002 ranks below P1003 the whole time even though the live price puts
it above. Streaming serves the change the hour it lands, at the cost of
per-event writes; an hourly batch costs one stale hour, a daily batch
twenty-two. The latency class is a per-feature decision, not a property
of the store: Airbnb's Zipline serves from a 1-second realtime lane down
to a daily batch lane, with sub-10ms online lookups, and the feature
owner declares which lane a value needs (Simha and Hoh, "Building the
Airbnb User Price Recommendation Engine", Strata Data Conference New
York, 2018).

## Evidence boundary

The executed sweep over one declared promo (illustrative, deterministic).
It demonstrates the freshness mechanics; real stores must decide the
latency class per feature, measure the staleness each class actually
serves, and set the refresh against how fast the value moves — the same
decision stage 46 makes for model snapshots, one level down.

## Check your mental model

**1. Why is the 1h batch stale for only one hour and the 24h batch for
twenty-two?**

<details>
<summary>Answer</summary>

Because the change lands mid-hour-2 and each policy serves the frozen
value until its next re-ingestion: the hourly refresh re-ingests at hour
3, the daily one at hour 24. The wrong-pair count is constant — one pair,
P1002 versus P1003 — because the stale \$89 price scores P1002 below
P1003 while the live \$59 price ranks it above. The interval decides the
duration, the score decides the cost.

</details>

**2. Why is freshness not a store property?**

<details>
<summary>Answer</summary>

Because features move at different speeds. A user's age is frozen
forever; an inventory level is stale after minutes. Serving every value
through the streaming lane costs per-event writes for features that
never change, and serving every value through the daily lane ages the
hot ones. The store keeps the two reads identical; the feature owner
declares how fresh each value must be, and the store enforces that
latency class.

</details>

## Next

Back to [stage 43](../). The [feature-divergence detour](../when-the-feature-diverges/)
shows the same frozen value reaching the ranker through two read paths;
this detour is the other half of the trade — the frozen value itself
aging between refreshes.
