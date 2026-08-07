---
status: verified
level: applied
base: scratch
label: When retraining flips the metric
verified: 2026-08-07
---

# The retrain that flips the metric offline can lose online

**Question:** [stage 46's staleness](../) says retraining buys back rank
error. This chapter asks which metric the retrain should be judged by,
and answers: the offline win is not the online outcome when the labels
were logged under the old policy.

**Before this:** [stage 46 — retraining and staleness](../) and its
executed aging-snapshot read.

## The two metrics, executed

The run ([record](runs/2026-08-07-retraining-flips-the-metric-read.md))
compares the old model and the retrained one on offline NDCG and on
exposure-weighted CTR:

| metric | old model | retrained |
|---|---:|---:|
| offline ndcg@5 | 0.917 | 1.000 |
| exposure-weighted ctr | 0.0289 | 0.0282 |

## The reading

The retrained model scores higher on the offline list, but the slate it
serves clicks less where it matters. The offline labels were logged under
the old policy, where the top position inflated its own clicks; NDCG
believes that log, and the online page does not. The retrain decision
needs the metric that matches the goal — and an A/B, because the exposure
shift is only visible online. A model that wins the offline metric and
loses the page is not a better model; it is a different policy that the
offline eval cannot see.

## Evidence boundary

The executed comparison over one declared slate (illustrative,
deterministic). It demonstrates the mechanism; real retrain decisions need
an A/B on the live page, because the exposure shift that flips the metric
is invisible to any offline replay of the old policy's log.

## Check your mental model

Answer each before opening it.

**1. How can NDCG rise while CTR falls?**

<details>
<summary>Answer</summary>

Because NDCG is computed on the old policy's log, where the top position
got inflated clicks. The retrained model reorders the slate, and the new
top items have lower true CTR than the old log believed. NDCG says the
new order matches the logged preferences; the live page says the users
click it less. The metric inherited the old policy's bias.

</details>

**2. Why does the exposure shift need an online experiment?**

<details>
<summary>Answer</summary>

Because the shift is only visible where the new policy actually serves:
which items move up, which down, and what the real click rate is at each
new position. No offline replay can simulate that, since the log contains
no data from the new policy. The A/B is not a formality — it is the only
place the retrain's claim can be tested.

</details>

## Next

Back to [stage 46](../). The [embedding-expiry
detour](../when-the-embedding-expires/) is the other way a retrain can
miss: refreshing the weights while the index still holds yesterday's
vectors.
