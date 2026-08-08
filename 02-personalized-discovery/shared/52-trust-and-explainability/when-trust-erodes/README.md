---
status: verified
level: applied
base: scratch
label: When trust erodes
verified: 2026-08-07
---

# A false explanation burns trust faster than a missing one

**Question:** [stage 52's attribution](../) must be verifiable. This
chapter asks what a wrong explanation costs, and answers: a false claim
is a lie the user can check — and opt-outs rise with the share of false
explanations, because the user has evidence against the claim.

**Before this:** [stage 52 — trust and explainability](../) and its
executed contribution read.

## The opt-out curve, executed

The run ([record](runs/2026-08-07-trust-erodes-read.md)) varies the share
of false explanations:

| false explanations | opt-out rate |
|---|---:|
| 0% | 1.0% |
| 5% | 1.8% |
| 20% | 5.2% |
| 50% | 13.0% |

## The reading

Even a 5% false rate nearly doubles opt-outs; at 20% a twentieth of users
leave. The explanation feature was meant to build trust, and a wrong one
burns it faster than a missing one — the user can check "because you
viewed" against their own history, and the check fails. Explanations are
cheap to generate and expensive to get wrong: each false claim converts
the trust the feature was supposed to build into evidence against the
platform.

## The fix and its trade

The fix is to gate the explanation feature on the measured cost: track
the false-explanation rate on live traffic, measure the retention
response, and ship or keep the feature only when the measured cost
clears the trust it is supposed to build. The executed curve prices the
stakes — a 5 percent false rate nearly doubles opt-outs from 1.0 to 1.8
percent, 20 percent false drives 5.2 percent of users to leave, and 50
percent drives 13.0 percent, because each false claim is a lie the user
can check against their own history.

The trade is the asymmetry between a missing explanation and a false
one: a missing one is neutral, and a false one converts the trust the
feature was bought to build into evidence against the platform. Gating
on the measured cost means shipping fewer explanations when the false
rate is high — the feature is cheap to generate and expensive to get
wrong, so the measurement team's false-rate and retention numbers, not
the feature's availability, decide whether the copy stays on the page.

## Who owns the loop

- **The explainability team** owns the false-explanation-rate measurement
  on live traffic, the number the gate is priced on.
- **The product team** owns the feature-gate decision and the
  missing-versus-false trade each surface tolerates.
- **The measurement and analytics team** owns the retention response,
  the second half of the cost that decides whether the feature stays.

## Evidence boundary

The executed curve over declared opt-out responses (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the false-explanation rate on their own traffic and the retention
response, and gate the explanation feature on the measured cost.

## Check your mental model

Answer each before opening it.

**1. Why does 5% false nearly double the opt-out rate?**

<details>
<summary>Answer</summary>

Because the failure is salient: a user who sees "because you viewed this
category" on an item in a category they never viewed has caught the
system in a concrete lie. One such catch outweighs many correct
explanations, because it is proof the explanation cannot be trusted —
and a user who cannot trust the explanation stops trusting the page.

</details>

**2. Why is a false explanation worse than none?**

<details>
<summary>Answer</summary>

A missing explanation is neutral — the user is simply not told why. A
false one is active damage: it makes a claim the user can check and fail,
converting doubt into evidence. The trust-erosion detour's curve shows
the asymmetry: the feature was bought to build trust, and each wrong
claim spends that purchase at a rate a missing feature never would.

</details>

## Next

Back to [stage 52](../). The [explanation-is-wrong
detour](../when-the-explanation-is-wrong/) shows how false claims arise
in the first place: the coefficient, not the contribution, writing the
headline.
