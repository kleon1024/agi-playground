# Run — the as-of consistency audit over emitted store reads

**Date:** 2026-08-07
**Commands:** `uv run python core/feature_store.py --emit-log /tmp/store-reads.json`;
`uv run python prod/store_consistency.py /tmp/store-reads.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 43's store must serve training and serving the same frozen value.
This run is the case-finding half of the stage: how a team finds a read
path that bypasses the store. The core script emits the store-path and
naive-path reads as JSON; the production audit compares every served
value against the training snapshot, per key, and names the divergent
feature.

## Output

```
as-of consistency audit over the emitted store reads:
  keys checked: 9 rows across 3 items
  feature age_hours: mean served-vs-trained delta +4.00, max +5.00 (3 keys)
  feature category_ctr: mean served-vs-trained delta +0.00, max +0.00 (3 keys)
  feature price: mean served-vs-trained delta +0.00, max +0.00 (3 keys)
  keys whose served value differs from training: 3
    P1001/age_hours
    P1002/age_hours
    P1003/age_hours

verdict: DIVERGENT -- the served read recomputed a feature
the model never trained on. Keys above; the store is bypassed
on this read path.
```

## Notes

- The price and category features match on both paths; the divergence is
  isolated to `age_hours`, where the naive read recomputes 3-5 hours of
  age against the store's frozen 0. The audit names the feature, which is
  what lets the owning team fix the read path instead of the model.
- The check is the point-in-time discipline Airbnb's Zipline encodes in
  its training backfills: every feature value must be exactly the value a
  serving read at that moment would have returned (Simha and Hoh, "Building
  the Airbnb User Price Recommendation Engine", Strata Data Conference New
  York, 2018).
