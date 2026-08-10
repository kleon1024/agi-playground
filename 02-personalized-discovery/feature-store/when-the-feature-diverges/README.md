---
status: verified
level: applied
base: scratch
label: When the feature diverges
verified: 2026-08-07
---

# The feature diverges and the ranker reorders on a value the model never saw

**Question:** [stage 43's feature store](../) guarantees identical reads.
This chapter reads the divergence the store prevents, directly: the same
items, scored with the training-time feature and the serve-time feature.

**Before this:** [stage 43 — feature store](../) and its executed
read-at-serve-time model.

## The two orders, executed

The run ([record](runs/2026-08-07-feature-diverges-read.md)) scores each
item at its training-time age (hour 0) and its serve-time age (hour 5):

| item | train score | serve score |
|---|---:|---:|
| P1001 | 17.5 | 12.5 |
| P1002 | 17.5 | 17.5 |
| P1003 | 11.5 | 7.5 |

Train order: P1001, P1002, P1003. Serve order: P1002, P1001, P1003.

## The reading

The items are the same; only the feature differs. The training-time
ranker sees every item as new and puts P1001 first; at serve time P1002
is the fresh one and wins on an age feature the model never trained on.
The divergence is not a model bug — it is the two reads disagreeing about
the world, which is what the store prevents. A ranker that trains on one
world and serves another is not wrong about either; it is unmoored, and
the disagreement is invisible until the slate changes under it.

## The fix and its trade

The fix is the as-of read itself: score serving with the same frozen
feature values training used, so the ranker always reorders on a world it
has seen. The executed read prices the failure — train order P1001,
P1002, P1003 against serve order P1002, P1001, P1003, with P1001 falling
17.5 to 12.5 while P1002 holds 17.5 on an age feature the model never
trained on. With the store in place, the divergence disappears by
construction rather than by inspection.

The trade is that identical reads are not the whole repair: the serve
world still moves, and the frozen value ages until refresh. The store
cannot tell a legitimate fast-mover (an item that genuinely gets old)
from a read bug, so the feature owner must declare which divergences are
expected, and the prediction-observation gap of stage 47 is the standing
check that the frozen read still matches the world it serves. The store
trades away the ability to lie silently; it does not trade away the
feature owner's obligation to say how fast the value moves.

## Who owns the loop

- **The feature-owner team** declares what each feature means and how
  fast it legitimately moves, so a serve-time reorder is classified as
  expected drift or a read bug.
- **The serving and ranking team** owns the serve-time feature
  computation and the slate that reorders under it.
- **The monitoring team** owns the prediction-observation gap of stage
  47 that catches the divergence the store cannot see.

## Evidence boundary

The executed read over three declared items (illustrative, deterministic).
It demonstrates the divergence shape; real deployments must measure the
serve-time distribution of each feature against the training snapshot to
decide which divergences matter.

## Check your mental model

Answer each before opening it.

**1. Why does P1002 win at serve time when it loses at training time?**

<details>
<summary>Answer</summary>

Because its age feature changed least: at hour 5, P1002 (added at hour 2)
is 3 hours old while P1001 (added at hour 0) is 5. The score rewards
freshness, so P1002's serve score holds at 17.5 while P1001 drops to
12.5. Neither score is wrong — they answer different questions, and the
ranker was trained on one of them.

</details>

**2. Why is the disagreement invisible to the offline eval?**

<details>
<summary>Answer</summary>

Because the eval reuses the training-time features, so it scores the same
world the model trained on. The divergence only appears at serve time,
where the live feature is computed on the current world. This is why
monitoring (stage 47) must track the prediction-observation gap online —
the offline number cannot see the drift.

</details>

## Next

Back to [stage 43](../). The [missing-feature
detour](../when-the-feature-is-missing/) is the other way the store can
lie: not by diverging, but by serving a default nobody chose.
