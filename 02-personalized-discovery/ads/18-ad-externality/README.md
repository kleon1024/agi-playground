---
status: verified
level: applied
base: scratch
label: Ad externality
verified: 2026-08-06
---

# Every ad displaces an organic result

**Question:** the mission's contract states the defining feature — every
ad displaces an organic result. This stage quantifies the displacement
and returns the ads track to the value-tree trade the mission began with.

**Before this:** [stage 17 — budget pacing](../17-budget-pacing/) for how
ads get delivered, and [stage 05's value tree](../../shared/05-value-tree/) for how
organic and ad value are priced together.

## The displacement, executed

The run ([record](runs/2026-08-06-ad-externality.md)) executes the
displacement model on a five-slot slate with organic values
[0.9, 0.8, 0.7, 0.5, 0.3]:

| ads | organic kept | displaced | ad value |
|---|---:|---:|---:|
| 1 | 2.9 | 0.3 | 0.6 |
| 2 | 2.4 | 0.8 | 1.2 |
| 3 | 1.7 | 1.5 | 1.8 |

## The mechanism, named

An ad slot has two sides: the revenue it earns and the organic value it
pushes out. The displacement is the organic value of the items the ads
replace. The ad's net value to the platform is revenue minus displacement
— and the trade is real: two ads earn 1.2 in ad value but destroy 0.8 in
organic value.

## Why this is the mission's central trade

The mission opened with the contract's warning: recommendation, search,
and ads cannot be optimized independently because one cannibalizes the
others. This stage closes that loop. The value tree (stage 05) prices the
combination; the externality quantifies what the ad actually costs. A
platform that ranks ads by revenue alone over-inserts them; one that
prices displacement runs the auction the mission's decision actually
requires.

## Evidence boundary

The executed displacement model over one hand-built slate (illustrative,
deterministic, assumed ad utility). It demonstrates the trade; real ad
placement also needs measured organic-value loss per position, which an
online experiment would estimate.

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

**2. Where does the platform decide how much organic it may displace?**

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

A detour from here: [scarcity amplifies the externality](when-the-slot-is-scarce/) — the executed sweep read: the same ad displaces 0.60 in a 4-slot slate but 0.20 in an 8-slot one, so slot count is part of the ad decision.

Another detour: [the externality flips sign when the ad is relevant](when-the-ad-is-relevant/) — the executed sign flip read: an irrelevant ad displacing a 0.7 organic item loses 0.5 while a relevant ad gains 0.7, which is why the value tree prices the combination.
