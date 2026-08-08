---
status: verified
level: applied
base: scratch
label: When the ad is relevant
verified: 2026-08-06
---

# The externality flips sign when the ad is relevant

**Question:** [stage 18's ad externality](../) showed every ad displaces
organic value. This chapter reads the executed sign flip and asks when
displacement is actually a loss.

**Before this:** [stage 18 — ad externality](../) and its executed
displacement model.

## The sign flip, executed

The run ([record](runs/2026-08-06-relevant-ad.md)) compares the ad's user
value against the 0.7 organic item it displaces:

| ad user value | net | label |
|---:|---:|---|
| 0.2 | -0.5 | net loss |
| 0.7 | 0.0 | neutral |
| 1.4 | +0.7 | net gain |

## Two readings

**The externality is the difference, not the ad.** An irrelevant ad (0.2)
displacing a 0.7 organic item is a 0.5 loss to the user; a relevant ad
(1.4) is a 0.7 gain. The same slot, the same displacement — the sign
comes from the ad's user value relative to what it replaced. The
externality is not a constant tax on ads; it is a comparison.

**This is why the value tree prices the combination.** Stage 05's value
tree does not ban ads or rank them by revenue alone — it prices the
ad-plus-organic slate together. The sign flip is the mechanism that makes
combined pricing necessary: a relevant ad earns the right to a slot, an
irrelevant one does not, and only the difference between the two tells
them apart.

## Who owns the loop

- **The value-tree and ranking team** owns the admission rule: admit an
  ad only when its user value clears the organic item it displaces, per
  slot and per user.
- **The experimentation and measurement team** owns the per-slice
  externality estimate — relevance is per-user and per-context, so the
  sign flip has to be measured, not assumed.
- **The ads product team** owns the relevance bar the value tree prices
  against, balancing ad revenue against the displacement cost this
  detour quantifies.

## Evidence boundary

The executed sign flip over three ad values against one hand-built
displaced organic value (illustrative, deterministic). It demonstrates
the mechanism; real placement needs measured organic-value loss per
position and per user.

## The fix and its trade

The measured fix is to price the combination, not the ad: admit an ad
only when its user value clears the organic item it displaces, per slot
and per user — the sign-flip table is the decision rule (net +0.7 for
the relevant ad, -0.5 for the irrelevant one). The trade is in the
measurement: relevance is a per-user, per-context property, so the
externality must be estimated per slice — the stage audit found the
aggregate net +0.0688 while the engaged slice lost -0.3249 — and field
experiments are the honest estimator (Blake, Nosko & Tadelis, 2015,
*Econometrica* 83(1):155-174, ran a paid-search experiment at eBay and
measured that brand ads displaced organic results with little
incremental value). A platform that assumes one ad value for everyone
prices the externality at the wrong point on the relevance curve.

## Check your mental model

Answer each before opening it.

**1. Why is the 0.7 ad neutral rather than harmful?**

<details>
<summary>Answer</summary>

Because it replaces an item worth exactly what it provides. The user gets
0.7 from the ad and loses 0.7 from the displaced organic item — no net
change. The slot reallocated value without destroying any. Neutrality is
the dividing line: any ad worth more than the item it displaces is a net
win, any ad worth less is a net loss, and the line sits at equality.

</details>

**2. What makes a relevant ad worth 1.4 to the user?**

<details>
<summary>Answer</summary>

The same thing that makes it relevant: it answers the user's intent better
than the item it pushed out — a product they were already looking for, an
offer that fits their context. Relevance is not the ad's quality in the
abstract; it is the ad's value relative to the organic item at the same
position. That relativity is exactly what the executed comparison
quantifies.

</details>

## Next

Back to [stage 18](../), or to
[scarcity amplifies the externality](../when-the-slot-is-scarce/) for
how slot supply moves the same comparison.
