---
status: verified
level: applied
base: scratch
label: Frequency capping
verified: 2026-08-07
---

# The cap that keeps an ad from repeating itself

**Question:** [stage 17's budget pacing](../17-budget-pacing/) decided
when to deliver. This stage asks how many times one user may see the
same ad, and answers: CTR decays with exposure, so the cap is a value
decision about where delivery is still worth anything.

**Before this:** [stage 17 — budget pacing](../17-budget-pacing/) for
delivery, and [stage 15 — eCPM ranking](../15-ecpm-ranking/) for what
the ad's expected value is.

## The decay, executed

The run ([record](runs/2026-08-07-frequency-capping.md)) reads CTR by
exposure count:

| exposure | CTR |
|---|---:|
| 1 | 0.050 |
| 2 | 0.040 |
| 3 | 0.030 |
| 4 | 0.020 |
| 5 | 0.010 |
| 6 | 0.005 |
| 7 | 0.002 |

## The mechanism, named

The marginal impression's value collapses: CTR falls from 0.050 to
0.002 across seven exposures. A cap at three keeps the high-value
exposures; uncapped, the ad keeps burning impressions at near-zero
click value while annoying the user. The cap is a value decision, not a
rule of thumb — and the [cap-bites detour](when-the-cap-bites/) shows
its other side: the same budget reaches fewer users as the cap rises,
so the cap is a budget allocation between reach and frequency.

## Why this belongs in the mission

The mission's contract states that every ad displaces an organic result.
Frequency capping is the delivery-side version of that discipline: an ad
shown past its useful exposures is not only wasting the advertiser's
delivery — it is occupying slots that would have shown something else,
multiplying the externality [stage 18](../18-ad-externality/) priced.

## Evidence boundary

The executed CTR decay over seven exposure counts (illustrative,
deterministic, assumed fatigue curve). It demonstrates the mechanism;
real caps are set from measured fatigue per user and per creative,
which is the [fatigue detour's](when-fatigue-hits/) arithmetic.

## Check your mental model

Answer each before opening it.

**1. Why is the cap a value decision rather than a display setting?**

<details>
<summary>Answer</summary>

Because the marginal exposure's value changes with count. The fifth
exposure clicks at a tenth of the first's rate, so showing it is
spending delivery on near-zero expected value. Where the cap sits
depends on how the platform prices that decay — which is a value
decision about the trade between frequency and reach.

</details>

**2. What does the cap cost when it is high?**

<details>
<summary>Answer</summary>

Reach. The same 10,000-impression budget reaches 10,000 users at cap 1
and only 1,000 at cap 10 — the cap-bites detour executes the curve. A
high cap preserves per-user value but shrinks the audience, so the
campaign's goal decides which side of the trade it needs.

</details>

## Next

Forward to [stage 26 — creative selection](../26-creative-selection/)
where the ad's content, not just its frequency, is chosen.

A detour from here: [the cap is a budget allocation, not a
setting](when-the-cap-bites/) — the executed reach read: the same
10,000-impression budget reaches 10,000 users at cap 1 and only 1,000
at cap 10, so the cap is the reach-frequency trade, not a display
setting.

Another detour: [more impressions buy fewer clicks once fatigue sets
in](when-fatigue-hits/) — the executed expected-click read: over one
million impressions the capped campaign earns 40,000 expected clicks
while the uncapped earns 22,429, so fatigue is why the cap exists.
