---
status: verified
level: applied
base: scratch
label: Frequency capping
verified: 2026-08-07
---

# The cap that reads the aggregate curve keeps serving the segment that stopped clicking

**Question:** [stage 17's budget pacing](../17-budget-pacing/) decided
when to deliver. This stage asks how many times one user may see the
same ad, and answers: CTR decays with exposure, so the cap is a value
decision about where delivery is still worth anything — and the audit
shows why the cap has to be set per segment, not off the aggregate
curve.

**Before this:** [stage 17 — budget pacing](../17-budget-pacing/) for
delivery, and [stage 15 — eCPM ranking](../15-ecpm-ranking/) for what
the ad's expected value is.

## The mechanism, executed

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

The marginal impression's value collapses: CTR falls from 0.050 to
0.002 across seven exposures. A cap at three keeps the high-value
exposures; uncapped, the ad keeps burning impressions at near-zero
click value while annoying the user. The cap is a value decision, not a
rule of thumb — and the [cap-bites detour](when-the-cap-bites/) shows
its other side: the same budget reaches fewer users as the cap rises,
so the cap is a budget allocation between reach and frequency.

<!-- interactive: FrequencyCapping -->

## The failure mode, named and audited

**The aggregate curve hides the segment that stopped clicking.** The
audit ([record](runs/2026-08-07-segment-decay.md)) draws 20,000
impressions (fixed seed) across three segments — casual, standard,
power — with different fatigue curves and different exposure
distributions:

| segment | share | mean CTR | dead share |
|---|---:|---:|---:|
| casual | 30.0% | 0.0458 | 0.0% |
| standard | 50.0% | 0.0328 | 7.2% |
| power | 20.0% | 0.0133 | 40.6% |
| aggregate | 100% | 0.0328 | 11.7% |

The symptom is measured: aggregate CTR 0.0328 looks healthy — it is the
standard curve's own number — while the power slice runs at 0.0133 with
40.6 percent of its impressions served at or below 0.005 CTR. A cap
read off the aggregate curve keeps serving the slice that stopped
clicking, and a global cap trades away healthy casual clicks to do it:
cap 3 cuts 6,269 impressions and sacrifices 28.5 casual expected
clicks to save 7.3 power clicks, while per-segment caps (casual 7,
standard 3, power 2) cut 6,152 impressions and lose 0 casual clicks.
Stratifying by segment is how the case is found; per-segment caps are
how the trade is tuned.

**The cap is only as good as the counter that feeds it.** The cap is
enforced on an identity object — a cookie, an app install id, a
logged-in user id — and identity breaks. The
[counter-drift detour](when-the-counter-drifts/) serves 10,000 users
where 30 percent lose their counter at least once: the campaign serves
6,167 extra impressions at about one-third of the first-three click
value (0.0139 versus 0.0400), and the dead share rises from 0.0 to 3.1
percent. A reset counter is censored exposure treated as zero, and the
cap cannot tell a new user from an erased history (Buchbinder, Feldman,
Ghosh & Naor, 2014, J. Scheduling, analyze frequency capping with
identities; Aharon et al., 2023, arXiv:2312.05052, report a 7.3 percent
revenue lift from soft frequency capping in Yahoo Gemini Native — the
value a working cap protects).

**The cap trades reach for frequency.** The [cap-bites
detour](when-the-cap-bites/) allocates a 10,000-impression budget:
10,000 users reached at cap 1, 1,000 at cap 10. A high cap preserves
per-user value but shrinks the audience, so the cap is a budget
allocation, not a display setting — and the [fatigue
detour](when-fatigue-hits/) prices what the cap saves: over one
million impressions the capped campaign earns 40,000 expected clicks
against 22,429 uncapped.

## The fix and its trade

The fix is per-segment caps keyed to a stable identity counter, because
fatigue is per segment and delivery is per identity. The audit prices
both halves: aggregate CTR 0.0328 passes while the power slice runs at
0.0133 with 40.6 percent of its impressions dead, and per-segment caps
(casual 7, standard 3, power 2) cut 6,152 impressions while losing zero
casual clicks — where a global cap 3 cuts 6,269 impressions and
sacrifices 28.5 casual expected clicks to save 7.3 power clicks.

The trade is that the cap is a budget allocation, and both dials cost
something. A higher cap preserves per-user value but shrinks the
audience: a 10,000-impression budget reaches 10,000 users at cap 1 and
1,000 at cap 10. The counter is load-bearing — when 30 percent of users
lose their counter at least once, the campaign serves 6,167 extra
impressions at about a third of the first-three click value (0.0139
versus 0.0400) and the dead share rises to 3.1 percent. Per-segment caps
add serving complexity for exactly the audience that stopped clicking,
which is why the identity and measurement teams own the counter and the
dead share the cap reads.

## Who owns the loop

The cap only works if someone is accountable at each side of the
delivery loop, and each owner is tied to one of the failure modes
above:

- **The delivery and ads-serving team** owns the cap's execution: the
  per-segment curve, the counter read at serve time, and the cap
  decision per user. It owns the hidden-slice failure — the audit
  measured the power slice at 0.0133 mean CTR under an aggregate 0.0328
  pass, with per-segment caps cutting 6,152 impressions while losing
  zero casual clicks.
- **The data and identity team** owns the counter that makes the cap
  real: stable identity, the exposure log, and the join of the two. It
  owns the reset failure — a counter that vanishes re-opens the cap,
  and the detour measured 6,167 over-served impressions from it
  (Buchbinder, Feldman, Ghosh & Naor, 2014, show the cap's guarantees
  depend on the identity it is keyed to).
- **The ads-product and measurement team** owns the fatigue curve and
  the cap policy: measured decay per segment, the dead share monitor,
  and the reach-frequency trade against the campaign's goal. It owns
  the trade failure — cap 3 sacrifices 28.5 casual clicks to save 7.3
  power clicks, which is a product decision about whose clicks matter
  (Aharon et al., 2023, priced the payoff of capping well at +7.3
  percent revenue).

When the ownership is implicit, serving applies a global cap from an
aggregate curve, identity ships no stable counter, and the power slice
keeps receiving impressions it stopped clicking — while the campaign
report shows a healthy 0.03 CTR and nobody owns the 40 percent dead
share.

## Why this belongs in the mission

The mission's contract states that every ad displaces an organic result.
Frequency capping is the delivery-side version of that discipline: an ad
shown past its useful exposures is not only wasting the advertiser's
delivery — it is occupying slots that would have shown something else,
multiplying the externality [stage 18](../18-ad-externality/) priced.
The audit adds the industrial detail: the cap is set per segment because
fatigue is per segment, and the counter is per identity because delivery
is per identity — both are cases the aggregate curve hides.

## Evidence boundary

The executed CTR decay over seven exposure counts and the audit's
20,000 synthetic impressions (fixed seed) are illustrative and
deterministic. They demonstrate the mechanism and the hidden-slice
arithmetic; real caps are set from measured fatigue per user and per
creative, per-segment monitoring needs enough impressions per segment
to detect the gap, and the reset rate is measured per browser, app, and
market rather than declared.

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

**2. Your campaign CTR is healthy, but one segment's delivery is
worthless. Where do you look?**

<details>
<summary>Answer</summary>

At per-segment decay before the aggregate. The audit measured aggregate
0.0328 while the power slice ran at 0.0133 with 40.6 percent of its
impressions at or below 0.005 CTR. A global cap read off the aggregate
curve keeps serving that slice, and a global cap that protects it
over-cuts the casual segment — 28.5 casual clicks lost to save 7.3
power clicks. Stratify by segment to find the case, then set the cap
per curve.

</details>

**3. What does the cap assume about the counter it reads?**

<details>
<summary>Answer</summary>

That the counter equals true exposure. In production the counter is
keyed to an identity object that resets — a cleared cookie, a new
browser, a second device — and a reset re-opens the cap. The
counter-drift detour measured the cost: 6,167 extra impressions at a
third of the click value when 30 percent of users lose their counter at
least once. The cap needs a stable identity or a counter that treats
erased history as censored, not zero.

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

A third detour: [the cap reads a counter that can reset underneath
it](when-the-counter-drifts/) — the executed identity read: when 30
percent of users lose their counter at least once, the campaign serves
6,167 extra impressions at one-third of the click value, so the cap is
only as strong as the identity it is keyed to.
