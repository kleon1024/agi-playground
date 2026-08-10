---
status: verified
level: applied
base: scratch
label: Ad externality
verified: 2026-08-07
---

# The aggregate says keep the ad. The engaged slice pays for it.

**Question:** the mission's contract states the defining feature — every
ad displaces an organic result. This stage quantifies the displacement,
then audits the operational symptom: the aggregate ad-value view says
the ad earns its slot, while a user slice the platform can least afford
to damage is paying for it. The failure is a hidden slice, and the fix
is measured externality per user and per slot.

**Before this:** [stage 17 — budget pacing](../17-budget-pacing/) for how
ads get delivered, and [stage 05's value tree](../../shared/05-value-tree/) for how
organic and ad value are priced together.

## The mechanism, executed

The run ([record](runs/2026-08-06-ad-externality.md)) executes the
displacement model on a five-slot slate with organic values
[0.9, 0.8, 0.7, 0.5, 0.3]:

| ads | organic kept | displaced | ad value |
|---|---:|---:|---:|
| 1 | 2.9 | 0.3 | 0.6 |
| 2 | 2.4 | 0.8 | 1.2 |
| 3 | 1.7 | 1.5 | 1.8 |

An ad slot has two sides: the revenue it earns and the organic value it
pushes out. The displacement is the organic value of the items the ads
replace. The ad's net value to the platform is revenue minus displacement
— and the trade is real: two ads earn 1.2 in ad value but destroy 0.8 in
organic value.

<!-- interactive: AdExternality -->

## The failure mode, named and audited

**The aggregate hides who pays.** The audit
([record](runs/2026-08-07-slice-externality.md)) draws 20,000 users
(fixed seed): a casual slice whose organic items are low-value, and an
engaged slice whose items are high-value, with one ad per user (utility
0.40):

| slice | share | organic displaced | net value per user |
|---|---:|---:|---:|
| casual | 75.0% | 0.2000 | +0.2000 |
| engaged | 25.0% | 0.7249 | -0.3249 |
| aggregate | 100% | 0.3312 | +0.0688 |

The symptom is measured: the aggregate net is +0.0688, so an ad-load
decision made on the aggregate keeps the ad — while the engaged slice
loses 0.32 per user because the ad displaces the high-value organic that
drives their sessions. The slice that pays is the one the platform can
least afford to damage, and only per-slice stratification exposes it.

**A single high-value slot hides the tail.** The
[when-the-slot-hides-the-whale detour](when-the-slot-hides-the-whale/)
measures the displacement distribution when one slate in ten carries a
0.95 whale at the ad's position: the average is 0.2307 while P90 and P99
sit at 0.9500. The mean prices routine slots; the tail is where the
user's most valuable result dies.

**Scarcity amplifies the externality.** The
[when-the-slot-is-scarce detour](when-the-slot-is-scarce/) sweeps slate
length: the same ad displaces 0.60 in a 4-slot slate but 0.20 in an
8-slot one. The externality is a property of the slot supply, which is
why slot count is a decision variable, not a constant.

**The externality flips sign with relevance.** The
[when-the-ad-is-relevant detour](when-the-ad-is-relevant/) compares ad
user value against the displaced organic item: an irrelevant ad loses
0.5, a relevant ad gains 0.7. The externality is a comparison, and only
combined pricing (stage 05's value tree) can make it.

## The fix and its trade

The fix is a net-value rule that prices displacement per user slice and
per slot position: admit an ad only when its net value clears the organic
bar, using measured externality instead of an average. The audit's slice
table prices the rule — the aggregate +0.0688 passes while the engaged
slice loses -0.3249 per user against casual +0.2000 — and the whale
detour shows the mean 0.2307 hides a P90/P99 displacement of 0.9500 where
the user's most valuable result dies.

The trade is that the fix costs measurement and cannot be settled by the
model alone. Real organic-value loss requires experiments that estimate
substitution per position and per user slice; until then the value tree
prices one average displacement that is wrong for the slice that pays.
Slot count is a decision variable, not a constant — the same ad displaces
0.60 in a 4-slot slate and 0.20 in an 8-slot one — and the ad-load
decision is where the platform chooses which point on that curve it sits,
trading ad revenue against the retention the engaged slice represents.

## Who owns the loop

The displacement only earns what someone is accountable for at each side
of the externality loop, and each owner is tied to one of the failure
modes above:

- **The value-tree and ranking team** owns the combined pricing: admitting
  an ad only when its net value clears the organic bar, per user slice
  and per slot position. It owns the hidden-slice and whale failures —
  the audit measured aggregate +0.0688 against engaged -0.3249, and a
  P90/P99 displacement of 0.9500 under a 0.2307 average (Anderson &
  Coate, 2005, *Review of Economic Studies* 72(4):947-972: the
  privately optimal ad load can exceed the socially optimal one when
  the content-value externality is unpriced).
- **The experimentation and measurement team** owns the externality
  estimate: field experiments that measure organic-value loss per
  position and per user, and the tail monitor that catches what the
  mean hides. It owns the aggregate-looks-fine failure — Blake, Nosko &
  Tadelis (2015, *Econometrica* 83(1):155-174) is the standing example
  of paid placement substituting for organic results that would have
  delivered the value anyway.
- **The ads product team** owns the ad-load and slot-count decisions:
  how many ads a surface carries per context, balancing ad revenue
  against the displacement curve. It owns the scarcity failure — the
  same ad costs 0.60 in a 4-slot slate and 0.20 in an 8-slot one, and
  the load decision chooses where on that curve the platform sits.

When the ownership is implicit, the measurement team reports an aggregate
net value, the value tree prices ads at one average displacement, and
the engaged slice's loss shows up later as retention — the symptom the
stage opened with.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search — and states the defining trade: every ad
displaces an organic result. This stage closes the loop the auction
(stage 14) opened: the auction prices the impression, the ranking picks
it (stage 15), pacing delivers it (stage 17), and the externality prices
what all of it displaces. The value tree (stage 05) is where the
decision is made; this stage provides the measured cost that decision
needs.

## Evidence boundary

The executed displacement model over one hand-built slate and the
audits' synthetic users and impressions (fixed seeds, assumed ad
utility) are illustrative and deterministic. They demonstrate the
displacement arithmetic and the hidden-slice and tail patterns; they do
not measure real organic-value loss, which requires experiments that
estimate substitution per position and per user slice.

## Check your mental model

Answer each before opening it.

**1. Why is the ad's value not just its revenue?**

<details>
<summary>Answer</summary>

Because the ad consumes a slot an organic result would have used. The
organic item's value (relevance, engagement, long-term user value) is
lost when the ad takes its place — that loss is the externality. A
platform that counts only ad revenue is double-counting: it records the
gain and ignores the displaced organic value it caused.

</details>

**2. Your ad-load experiment says ads add value, but heavy users'
engagement is dropping. Where do you look?**

<details>
<summary>Answer</summary>

At net ad value by user slice, before the aggregate. The audit measured
aggregate +0.0688 while the engaged slice ran at -0.3249 — the slice
whose organic feed is most valuable is the one losing it. The aggregate
experiment averages the loss away; the per-slice number exposes which
users pay, and the value tree re-prices the ad against the organic item
it displaces in that slice.

</details>

**3. Where does the platform decide how much organic it may displace?**

<details>
<summary>Answer</summary>

In the value tree (stage 05). The ad enters the slate only when its net
value — revenue minus displacement — clears the organic bar, exactly as
stage 05's auction lets an ad enter only when its utility exceeds the
displaced organic item's. The externality is the measured cost that makes
that decision, and it is the same trade across recommendation, search,
and ads.

</details>

## Next

This closes the ads track. The mission's three surfaces are now complete:
recommendation (stages 00-09), search (10-13), ads (14-18). Return to
[the mission README](../../) for the full path.

A detour from here: [the average displacement hides the one result that mattered](when-the-slot-hides-the-whale/) — the executed distribution read: average displacement 0.2307, P90/P99 0.9500, so the mean hides the one-in-ten context where the ad kills the user's most valuable result.

Another detour: [scarcity amplifies the externality](when-the-slot-is-scarce/) — the executed sweep read: the same ad displaces 0.60 in a 4-slot slate but 0.20 in an 8-slot one, so slot count is part of the ad decision.

A third detour: [the externality flips sign when the ad is relevant](when-the-ad-is-relevant/) — the executed sign flip read: an irrelevant ad displacing a 0.7 organic item loses 0.5 while a relevant ad gains 0.7, which is why the value tree prices the combination.

The mission opened with the contract's warning: recommendation, search,
and ads cannot be optimized independently because one cannibalizes the
others. This stage closes that loop. The value tree (stage 05) prices the
combination; the externality quantifies what the ad actually costs. A
platform that ranks ads by revenue alone over-inserts them; one that
prices displacement runs the auction the mission's decision actually
requires.
