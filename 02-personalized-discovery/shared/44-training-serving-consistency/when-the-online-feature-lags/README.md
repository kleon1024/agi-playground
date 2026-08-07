---
status: verified
level: applied
base: scratch
label: When the online feature lags
verified: 2026-08-07
---

# The online feature that lags serves a world that ended

**Question:** [stage 44's skew](../) covers the training snapshot moving
away from live reality. This chapter covers the other direction: the
serving value itself is stale, because the snapshot was taken before the
world updated.

**Before this:** [stage 44 — training-serving consistency](../) and its
executed skew read.

## The lag, executed

The run ([record](runs/2026-08-07-online-feature-lags-read.md)) updates
two prices after the training snapshot; the third is unchanged:

| item | logged price | live price | logged ctr | live ctr |
|---|---:|---:|---:|---:|
| P1001 | \$49 | \$56 | 0.042 | 0.026 |
| P1002 | \$89 | \$89 | 0.023 | 0.026 |
| P1003 | \$19 | \$24 | 0.018 | 0.030 |

## The reading

P1001 and P1003 changed price after the snapshot; their logged CTRs
describe the old prices. The estimate is not wrong — it is stale. The lag
between the snapshot and the live value is the skew, and it is a pipeline
property, not a model one. The same shape as stage 44's main read, seen
from the serving side: the world moved, and whichever side read it last
is the one the model is right about.

## Evidence boundary

The executed comparison over three declared items (illustrative,
deterministic). It demonstrates the mechanism; real deployments must
measure per-feature staleness budgets and decide which features may serve
the last snapshot and which must read live.

## Check your mental model

Answer each before opening it.

**1. Why is P1002 the only item whose logged CTR matches its live one?**

<details>
<summary>Answer</summary>

Because its price did not change (\$89 in both columns). The logged CTR
describes the current world by coincidence, not by design. The other two
items' prices moved, so their logged CTRs describe prices the user no
longer sees — the stale estimate is not an estimation error, it is a
snapshot age problem.

</details>

**2. Where does the lag decision actually live?**

<details>
<summary>Answer</summary>

In the pipeline's staleness budget: which features are allowed to serve
the last snapshot and for how long, set against how fast each one moves.
The model cannot fix it, because the model sees what it is given. This is
why serving-time feature logging (stage 44) and the store's write path
(stage 43) are the levers, not retraining.

</details>

## Next

Back to [stage 44](../). The [late-label
detour](../when-the-label-arrives-late/) is the training-side version of
the same split second: the target, not the feature, arriving after the
cut.
