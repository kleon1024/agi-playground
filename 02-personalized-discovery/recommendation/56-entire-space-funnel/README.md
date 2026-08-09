---
status: verified
level: applied
base: scratch
label: Entire-space funnel
verified: 2026-08-07
---

# The sparse target is learned on the wrong population

**Question:** stage 04 predicted several labels off one shared trunk and
left each head to its own training set. This stage asks what happens when
the rarest label — payment — is only observed below a click, and answers:
a head trained on the clicked subset is both starved and
selection-biased, so the fix is to model the funnel on the full exposure
space and derive the conditional instead of training it directly.

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
multi-task trunk this stage's trick plugs into, and [stage 05 — the value
tree](../../shared/05-value-tree/) for why each probability must be honest.

## The two training sets, executed

The run ([record](runs/2026-08-07-entire-space-funnel.md)) generates
impressions with a known click rate and a pay-given-click rate, then
trains a pay head on the clicked subset and an ESMM-style head on the
full space:

| head | positives | cvr auc |
|---|---:|---:|
| clicked subset | 705 | 0.735 |
| entire space (ctcvr) | 936 | 0.740 |

<!-- interactive: EntireSpaceFunnel -->

## The mechanism, named

Payment is a funnel event: it is only observed after a click, so a pay
head trained on clicked samples never sees the impressions that did not
click. That is not just fewer positives — it is a different statistical
problem, because the training population (clicked) differs from the
population the head must score (all exposures). The ESMM-style trick
trains two heads on the full space: a CTR head on every impression, and
a CTCVR head on every impression with the product label click-and-pay.
The pay conditional is then derived as CTCVR over CTR, which keeps the
funnel constraint p(pay) <= p(click) structural and gives the sparse
event the whole exposure space as its ground.

## Why this belongs in the mission

The mission's funnel is what makes the three systems one: every stage
that follows — the value tree, the ads auction, the budget pacing —
multiplies probabilities together. A conditional trained on the wrong
population is biased even when its ranking looks fine, and the bias
propagates into every product of probabilities downstream. This stage is
where the funnel stops being a diagram and becomes the training scheme.

## The fix and its trade

The fix is to stop training the pay head on the clicked subset and model
the funnel on the full exposure space instead: a CTR head and a CTCVR head
train on every impression, and the pay conditional is derived as
CTCVR over CTR. The executed read prices the repair — the same 936
positives give the full-space head a CVR AUC of 0.740 against 0.735 on
the clicked subset, and the head that scores the full funnel is no longer
ranking a population it never trained on.

The trade is that the trick moves the difficulty, it does not remove it.
The derived conditional explodes wherever CTR is tiny — a small CTCVR
error at 2% CTR is a 3x swing in p_pay (the
[ratio that explodes](when-the-ctcvr-disagrees/) detour) — so the
derivation needs a per-slice clip and a calibration check, not a global
formula. And full-space training needs the joint label distribution and
the funnel's intermediate events, which is a label-pipeline cost the
clicked-subset shortcut never paid. The shortcut's real price is the
0.448-versus-0.618 censored read: the head that never sees a non-click is
worse than random on the funnel it is asked to score.

## Who owns the loop

- **The label and sample team** owns the joint click-and-pay label on the
  full exposure space, the funnel's intermediate events, and the
  eligibility record — the ground the two heads train on. Without the
  full-space ground, the scheme collapses back into the censored subset.
- **The model team** owns the two heads and the derived conditional:
  the ratio is computed at score time, clipped per slice, and re-checked
  where CTR is small.
- **The evaluation team** owns the full-funnel read: CVR AUC and the
  derived conditional's calibration must be measured on all impressions,
  not on the clicked population the old head was judged on.
- **The downstream teams** (value tree, auction, pacing) own the contract
  that every probability they multiply is a marginal on the same exposure
  space — which is what makes the clip and the calibration check their
  concern, not just the ranking team's.

## Evidence boundary

The executed synthetic read over declared click and pay rates
(illustrative, deterministic). It demonstrates the population and
positives effect; real entire-space modeling needs the joint label
distribution, the funnel's intermediate events, and a check that the
derived conditional stays calibrated in the slice where CTR is small.

## Check your mental model

Answer each before opening it.

**1. Why is training the pay head on clicked samples more than just
fewer positives?**

<details>
<summary>Answer</summary>

Because the training population is different from the scoring
population: clicked impressions are a selected subset, so the head
learns pay inside that subset and never sees the exposures where pay is
structurally impossible. Fewer positives is the symptom; the selection
bias is the disease, and it is why the fix is a different training
scheme, not a bigger loss weight.

</details>

**2. What does the multiplicative CTCVR structure guarantee?**

<details>
<summary>Answer</summary>

That p(pay) is never larger than p(click), because it is the product of
the click probability and a conditional bounded by one. Probability
semantics are enforced by construction instead of by post-hoc clamping,
which is the consistency this mission's downstream stages rely on when
they multiply scores together.

</details>

## Next

The funnel's labels also arrive late: [a conversion that happens
tomorrow is labeled a negative today](when-the-cvr-is-censored/) — the
executed read: censored pay ranking collapses to 0.448 versus 0.618 for
the full-space head.

Deriving pay as a ratio has its own failure: [the ratio explodes
wherever p(click) is tiny](when-the-ctcvr-disagrees/) — the executed
read: at 2% CTR a small CTCVR error is a 3x swing in the derived
conditional.
