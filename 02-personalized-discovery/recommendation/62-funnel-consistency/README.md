---
status: verified
level: applied
base: scratch
label: Funnel consistency
verified: 2026-08-07
---

# A probability that cannot exist, served to the next stage

**Question:** the funnel stages train separate heads on separate labels.
This stage asks whether their outputs compose, and answers: a conditional
read as a marginal produces order probabilities above click probabilities —
numbers that violate the funnel by construction — and the fix is to chain
the marginals instead of swapping them.

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
multi-head trunk, and [stage 05 — the value tree](../../shared/05-value-tree/)
for why each probability is multiplied downstream.

## The two reads, executed

The run ([record](runs/2026-08-07-funnel-consistency.md)) reads an order
head trained on clicked impressions as a marginal (broken) and chained
(click marginal x order conditional):

| read | order log-loss | violations |
|---|---:|---:|
| broken (conditional as marginal) | 0.672 | 649 / 1,000 |
| chained | 0.501 | 0 by construction |

## The mechanism, named

A head trained on clicked impressions estimates p(order|click). Using it
as p(order|impression) overstates the marginal — the clicked population
converts at a higher rate than the full exposure space — so the pipeline
reports an order probability above a click probability on most impressions.
The chained read multiplies the marginal click probability by the
conditional, which keeps monotonicity structural and recovers the marginal
the downstream stage actually blends. This is the same
population-vs-scoring-space distinction as stage 56, applied to the
outputs rather than the training sets.

## Why this belongs in the mission

The value tree, the ads auction, and budget pacing all multiply funnel
probabilities. A stage that emits an impossible probability does not fail
on its own page; it fails inside every downstream product. Enforcing
consistency at the read is cheaper than debugging the value estimate.

## The fix and its trade

The fix is to chain the marginals at the read: multiply the click
marginal by the order conditional instead of reading the conditional as
if it were a marginal. The executed read prices the repair — the broken
read lands at an order log-loss of 0.672 with 649 of 1,000 impressions
violating the funnel, and the chained read drops to 0.501 with zero
violations by construction, because monotonicity is structural rather
than clamped.

The trade, named: the chain is only as honest as its inputs. It
faithfully multiplies an overconfident click head's inflation straight
through to the order probability — the constraint-hurts detour shows a
2.25x-overconfident click head manufacturing a 0.27 order estimate
against the independent model's correct 0.12 — so calibration must
precede chaining, and the constraint is a consistency guard, not a
substitute for honest heads. The cheap half of the fix is free: the
violation rate needs no labels, so it can run continuously on serving
traffic as the standing check.

## Who owns the loop

- **The label and sample team** owns the population each head trains on —
  the conditional-as-marginal confusion is born here, when one head is
  trained on clicked rows and another on the full space and the outputs
  are compared as if they were the same thing.
- **The model team** owns each head's output and its calibration — the
  chain cannot repair a head that overstates its probability.
- **The serving team** owns the chained read at score time: the value
  estimate that leaves the score path must already be the chained
  product, because downstream stages multiply whatever they receive.
- **The monitoring team** owns the per-slice violation-rate alert — the
  free check that catches a new head or a drifted population before the
  value estimates are consumed.

## Evidence boundary

The executed synthetic read over 1,000 held-out impressions (illustrative,
deterministic). It demonstrates the violation and its repair; real systems
must monitor the violation rate across slices and gate the chain on the
calibration of each conditional.

## Check your mental model

Answer each before opening it.

**1. Why does the conditional read as a marginal overstate p(order)?**

<details>
<summary>Answer</summary>

Because the clicked population is a selected subset with a higher
conversion rate than the exposure space. The head's estimate is correct
for the population it trained on and wrong for the population it scores.

</details>

**2. Why is the violation count the cheapest check?**

<details>
<summary>Answer</summary>

Because p(order) > p(click) is a probability that cannot exist, so a
violation rate on a sample is a direct signal that somewhere a conditional
is being read as a marginal — no labels or ground truth needed.

</details>

## Next

The constraint's own failure: [enforcing the funnel on an uncalibrated
click head manufactures a worse order estimate](when-the-constraint-hurts/),
and the raw symptom: [heads that disagree about the funnel
itself](when-the-order-exceeds-the-click/).
