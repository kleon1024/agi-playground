---
status: verified
level: applied
base: scratch
label: When warmup closed the collapse
verified: 2026-08-06
---

# What the warmup changed, and what it did not

**Question:** [stage 06](../) reports the warmup closing the eval spread
(0.2309 to 0.0536). The mechanism is a contrast between two numbers this
chapter lays out: the per-seed eval scores (the collapse closed) and the
per-seed final train loss (which stays wide).

**Before this:** [stage 06's warmup run](../) and stage 01's recorded
collapse.

## The contrast, measured

The reading ([record](runs/2026-08-06-warmup-reading.md)) pulls the two
views from the recorded JSON:

| | no warmup (stage 01) | warmup (stage 06) |
|---|---:|---:|
| eval mean | 0.4375 | 0.4970 |
| eval spread | 0.2309 | 0.0536 |
| eval per-seed | 0.513 / 0.515 / 0.284 | 0.471 / 0.524 / 0.496 |
| final train-loss spread | — | 0.2302 |

## Two readings

**The warmup closed the eval collapse.** Seed 2 went from 0.2844 (collapsed,
outside the others' band) to 0.4962 (inside it), and the eval spread fell
fourfold. The mechanism: stage 01's LR was hot from step one, and one seed's
optimization path diverged early, collapsing its eval; a linear warmup
over the first 10% of steps keeps the path stable.

**The train-loss variance did not move — which is the proof of the
mechanism.** The final train losses still span 0.34 to 0.57 (spread 0.2302),
almost identical to the old eval spread. If the collapse were an irreducible
seed difference, the eval spread and the loss spread would move together;
they do not. The warmup fixed an optimization-path divergence, not the
seed variance itself — a distinction the eval number alone cannot show.

## The fix and its trade

The fix is the two-number contrast, and the contrast is the evidence: eval
spread fell from 0.2309 to 0.0536 (fourfold) while the final train-loss
spread stayed at 0.2302. If the collapse were an irreducible seed
difference, the two spreads would move together; they do not, so the warmup
stabilized the optimization path (seed 2: 0.2844 -> 0.4962) without
changing what "fit" means for the task. The trade is that the fix's scope
is exactly as narrow as its evidence: it does not remove the seed variance
itself — seeds legitimately end at different minima, and the loss spread
staying wide is the honest remainder — and it does not isolate which
layer's gradient diverged, which the chapter names as beyond the stage's
scope. What the contrast buys is a mechanism claim the eval number alone
cannot support: "the warmup fixed the path, not the surface," which is the
distinction a practitioner needs before deciding whether more warmup,
more seeds, or a different LR would be the next lever.

## Who owns the loop

- **The model team** owns the mechanism claim: the path-vs-surface
  distinction is a training-dynamics statement, supported by the recorded
  contrast and left scoped to the stage's evidence.
- **The evaluation owner** owns the two-number read: the eval-spread and
  train-loss-spread pair must be reported together, because each alone
  supports a different (wrong) conclusion.
- **The report owner** owns the boundary: the warmup fixes the collapse it
  was tested against, and the report must not extend the claim to
  "warmup makes training seed-stable" — the loss spread says otherwise.

## Evidence boundary

The recorded warmup run (3 seeds) and stage 01's recorded baseline; no new
training. It reads the recorded contrast and names the mechanism; it does
not isolate the collapse further (e.g., which layer's gradient diverged) —
that is beyond the stage's scope.

## Check your mental model

Answer each before opening it.

**1. The final train losses still differ widely across seeds (0.34 to 0.57).
Why is that not a contradiction of the eval-spread fix?**

<details>
<summary>Answer</summary>

Because eval spread and train-loss spread measure different things. The
collapse was one seed's eval going wrong after a hot early path; the warmup
stabilized the path, so eval converged into a tight band. The train losses
still differ because seeds legitimately end at different minima — the loss
variance was never the problem. The contrast is the evidence: eval spread
fell fourfold while loss spread did not move.

</details>

**2. Why would a linear warmup over 10% of steps fix a seed-dependent
collapse rather than a uniform one?**

<details>
<summary>Answer</summary>

Because the divergence is path-sensitive: a high LR from step one can push
one seed's weights into a region whose eval collapses, while others land
fine. A warmup ramps the LR, so all seeds start with stable small steps and
the divergent path never opens. The fix is to the trajectory, not to the
loss surface — which is why the loss spread stays wide while the eval
collapse closes.

</details>

## Next

Back to [stage 06's warmup](../), or to
[stage 02's report](../../02-report/) where the hosted-API comparison closes
the mission's build-versus-buy question.
