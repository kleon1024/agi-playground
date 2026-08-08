---
status: verified
level: applied
base: scratch
label: Exposure bias
verified: 2026-08-07
---

# The model only ever sees what the old model showed

**Question:** every prior stage trained on logged interactions. This
stage asks how much those logs can be trusted, and answers: not clicked
is not the same as not liked when exposure itself is confounded — the
old model's favorites are both shown more and placed higher — and the
corrections are propensity weighting and random-exposure traffic.

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the model
whose training data this stage audits.

## The confound, executed

The run ([record](runs/2026-08-07-exposure-bias.md)) generates items
whose exposure and position boost depend on an unobserved popularity
confounder, then compares a naive model on the logged rows, an
inverse-propensity (IPS) model, and a model on random-exposure traffic:

| model | quality rank correlation |
|---|---:|
| naive on log | 0.874 |
| propensity (IPS) | 0.962 |
| random exposure | 0.995 |

## The mechanism, named

Recommendation systems train on what they showed, and what they showed
was decided by the previous model. Exposure is therefore confounded with
the old score and with position: a popular item is shown more, appears
higher, and gets clicked more for reasons that have nothing to do with
the user liking it. A naive model learns "shown often" as if it were
"liked". Weighting each logged row by the inverse exposure propensity
removes most of the selection confound; random-exposure traffic — a
small bucket that shows items uniformly — is the gold reference because
it has neither selection nor position bias.

## Why this belongs in the mission

Every measured outcome in this mission — the report stage's baselines,
the feedback loops stage's popularity collapse, the fairness stage's
allocation — is read off logged interactions. If the logs inherit the
policy's blind spots, the measurements inherit them too, so the exposure
mechanism is the foundation under the mission's evidence, not a footnote
about data hygiene.

## The fix and its trade

The fix is two corrections that address two different biases. Inverse
propensity weighting removes the selection confound — who was shown — by
reweighting each logged row by the inverse probability of exposure, and
the executed read shows it moving the quality rank correlation from 0.874
naive to 0.962. Random-exposure traffic is the gold reference at 0.995,
because it is the only data clean of both selection and position bias.

The trade, named: IPS is high-variance exactly where it matters — the
inverse of a small, noisy propensity is a huge weight, and the executed
noisy-propensity read collapses the correlation to 0.376 before a cap
restores it. And IPS corrects selection, not position: a high-placed item
still got a position boost inside its own click, so the correction
requires a propensity model that is itself logged and audited, plus the
random bucket — which costs real traffic that does not optimize the
current policy. The cheap alternative, training on the log as-is, looks
fine on the items the old model showed a lot and is blind everywhere
else.

## Who owns the loop

- **The logging team** owns what is in the log — the exposure decision,
  the position, and the click — because every correction downstream is
  bounded by what this team records.
- **The model team** owns the propensity estimator and its audit: the
  correction is only as trustworthy as the estimate it divides by, and the
  noisy-propensity read is its regression test.
- **The serving and exploration team** owns the random-exposure bucket —
  its size is a product decision that trades traffic for an unbiased
  reference, and the bucket is the only full answer to position bias.
- **The evaluation team** owns the naive-versus-corrected read on the
  whole catalogue, including the never-shown tail where no correction has
  a row to work with.

## Evidence boundary

The executed synthetic read over a declared popularity confounder and
position boost (illustrative, deterministic). It demonstrates the
confound and the two corrections; real systems must estimate
propensities from the logging policy, validate them against random
traffic, and accept that IPS corrects selection, not position — the
random bucket is the only full answer.

## Check your mental model

Answer each before opening it.

**1. Why does the naive model rank well on the items the old model
showed a lot?**

<details>
<summary>Answer</summary>

Because on those items the click signal is abundant and the confound is
invisible: the model learns the boost as if it were quality. The bias
shows where the confound is strongest — popular items ranked too high,
never-shown items ranked from nothing — which is exactly the failure a
rank correlation over the whole catalogue exposes.

</details>

**2. What does IPS correct, and what does it not?**

<details>
<summary>Answer</summary>

It corrects the selection confound — who was shown — by reweighting
rows by the inverse probability of exposure. It does not correct
position: a high-placed item still got a boost inside its own click.
The two biases need different fixes, and only exposure that ignores both
— random traffic — is clean of both.

</details>

## Next

Propensity weights are high variance: [a noisy inverse can let one row
steer the fit](when-the-propensity-is-noisy/) — the executed read:
correlation 0.980 with exact propensities, 0.376 with noisy ones, 0.986
after capping.

Exploration traffic is thin: [2% exploration reaches under 200 of 2,000
items](when-exploration-traffic-is-thin/) — the executed read, and why
the long tail still needs content-based recall.
