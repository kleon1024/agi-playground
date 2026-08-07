---
status: verified
level: applied
base: scratch
label: When the policy is biased
verified: 2026-08-07
---

# The label carries the position it was collected in

**Question:** [stage 53's allocation](../) ranks by CTR. This chapter
asks whether the CTR itself can be trusted, and answers: CTR logged at
the top of the page is inflated by position — the label carries the
position it was collected in, and ranking on the raw estimate entrenches
the bias.

**Before this:** [stage 53 — fairness and allocation](../) and its
executed exposure-budget read.

## The correction, executed

The run ([record](runs/2026-08-07-policy-is-biased-read.md)) compares
exposure by raw CTR and position-adjusted CTR:

| item | raw ctr | raw exposure | adjusted ctr | adjusted exposure |
|---|---:|---:|---:|---:|
| P1001 | 0.048 | 53% | 0.036 | 35% |
| P1002 | 0.041 | 33% | 0.034 | 29% |
| P1003 | 0.026 | 8% | 0.030 | 20% |
| P1004 | 0.022 | 5% | 0.028 | 16% |

## The reading

The raw numbers hand most exposure to the items that sat at the top of
the page; the position-adjusted numbers move the tail from 14% to 36% of
exposure. The bias is in the collection policy, and correcting it is not
fairness — it is measurement: top-of-page clicks are inflated by
visibility, so the raw CTR is a ranking decision dressed as data. Any
allocation built on it (stage 53) inherits the bias, which is why
position adjustment comes before the fairness question, not after.

## Evidence boundary

The executed comparison over four declared items (illustrative,
deterministic). It demonstrates the mechanism; real systems must estimate
the position effect from their own logs and adjust before ranking on
CTR, remembering that the adjustment itself depends on the policy that
collected the data.

## Check your mental model

Answer each before opening it.

**1. Why is P1001's raw CTR of 0.048 misleading?**

<details>
<summary>Answer</summary>

Because it was measured at the top of the page, where visibility inflates
clicks: the same item in a lower slot would click less. The adjusted
estimate (0.036) strips the position effect, and P1001's real advantage
shrinks. The raw number is not a lie about the top slot — it is a lie
about the item.

</details>

**2. Why is correcting this "measurement", not "fairness"?**

<details>
<summary>Answer</summary>

Because the adjustment is not giving anyone anything — it is removing a
confound so the ranking sees the item's true rate. Fairness (stage 53's
floor) then decides how much exposure the tail deserves at the measured
rates. Doing fairness before the correction would allocate on top of a
bias, spending the constraint to compensate for a measurement error
instead of fixing the error.

</details>

## Next

Back to [stage 53](../). The [constraint-bites
detour](../when-the-constraint-bites/) is the other half of the design:
the floor's measured price once the CTRs are honest.
