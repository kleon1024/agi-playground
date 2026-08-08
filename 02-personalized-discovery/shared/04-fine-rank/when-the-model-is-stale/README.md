---
status: verified
level: applied
base: scratch
label: When the model is stale
verified: 2026-08-07
---

# The model that learned yesterday

**Question:** [stage 04's fine-rank model](../) is trained on logged
interactions. This chapter reads the executed freshness run and asks what
an unrefreshed model costs.

**Before this:** [stage 04 — fine rank](../) and its executed model.

## The decay, executed

The run ([record](runs/2026-08-07-stale-read.md)) freezes the model's
score order at day 0 and moves the true grades:

| days since training | NDCG |
|---:|---:|
| 0 | 1.000 |
| 1 | 0.628 |
| 2 | 0.505 |
| 3 | 0.437 |
| 4 | 0.371 |

## Two readings

**The model's ranking is a snapshot of the distribution it trained on.**
At day 0 the score order matches the true grades perfectly. As the best
item decays and a lower one rises, the frozen order ranks an
increasingly wrong list — the model is not broken, it is simply dated.
The decay is smooth because the shift is gradual.

**Freshness is a ranking property, not a deployment nicety.** The drop
from 1.000 to 0.371 is a quality loss with no change to the model's
weights. Production fine-rankers buy freshness with retraining cadence —
daily, hourly, or online updates — and the cadence is an explicit choice
against the measured decay curve, exactly the curve this run draws.

## The fix and its trade

The fix is to set the retraining cadence from the measured decay curve, not
from a calendar habit. The executed run prices the failure: freezing the
score order at day 0 and moving the true grades drops NDCG 1.000 to 0.628
to 0.505 to 0.437 to 0.371 over days 0-4 — a quality loss with no change
to the model's weights, which is the exact failure mode that makes "train
once, deploy forever" unaffordable for a moving catalogue.

The trade, named: freshness costs compute and pipeline latency, and the
cadence is a contract against the curve. A daily retrain buys back the
day-1 0.628 read at the price of a nightly training job; an hourly or
online update buys more at the price of pipeline stability and label
window trade-offs (the delayed-feedback window from the recommendation
track is the same decision). The curve also names the guardrail: the team
must pick the maximum acceptable NDCG drop and derive the cadence from it,
because the alternative is a staleness SLA that nobody owns.

## Who owns the loop

- **The model team** owns the retraining cadence, chosen against the decay
  curve and the maximum acceptable drop.
- **The data pipeline team** owns the freshness of the training window —
  the cadence is only as good as the lag between event, label, and training
  snapshot.
- **The product team** owns the staleness SLA: the maximum NDCG drop a
  deployed model may reach before a refresh is mandatory is a product
  promise, priced against the compute budget.

## Evidence boundary

The executed hand-built distribution shift (illustrative, deterministic).
It demonstrates the mechanism; real decay rates are measured on held-out
log data and drive the retraining schedule.

## Check your mental model

Answer each before opening it.

**1. Why does NDCG fall if the model's weights never change?**

<details>
<summary>Answer</summary>

Because NDCG measures the ranking against the current true grades, and
the true grades move. The weights are frozen; the world is not. What
ranked perfectly on day 0 ranks poorly once the best item decays and a
new one rises. The model is not becoming worse at what it learned — the
world is becoming different from what it learned.

</details>

**2. What determines the retraining cadence?**

<details>
<summary>Answer</summary>

The measured decay curve against the cost of retraining. A fast-moving
catalog needs frequent updates because the curve drops quickly; a stable
one can refresh rarely. The trade is explicit: each retraining run costs
compute and pipeline time, and it buys back the NDCG the curve shows it
has lost. The curve is the evidence that makes the cadence a decision
rather than a habit.

</details>

## Next

Back to [stage 04](../), or to
[the calibration that decides](../the-calibration-that-decides/) for the
value-side property the same model must also keep honest.
