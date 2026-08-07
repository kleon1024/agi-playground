---
status: verified
level: applied
base: scratch
label: When fatigue hits
verified: 2026-08-07
---

# More impressions buy fewer clicks once fatigue sets in

**Question:** [stage 25's frequency capping](../) limits exposures per
user. This chapter reads the executed expected-click comparison and
asks what the cap actually saves.

**Before this:** [stage 25 — frequency capping](../) and its executed
CTR-decay model.

## The comparison, executed

The run ([record](runs/2026-08-07-fatigue-read.md)) computes expected
clicks over one million impressions with and without the cap:

| delivery | expected clicks |
|---|---:|
| capped at 3 | 40,000 |
| uncapped | 22,429 |
| lost to fatigue | 17,571 |

## The reading

More impressions do not buy more clicks once fatigue sets in — the
uncapped run wastes the same budget for fewer clicks. The reason is the
stage's decay curve: after the third exposure, each additional
impression clicks at a fraction of the first's rate, and a million
impressions at those near-zero rates deliver a worse total than the
capped run. Fatigue is why the cap exists: it concentrates delivery
where the ad still earns its slot.

## The fix and its trade

The measured fix is to cap where the marginal exposure stops earning —
and to set that point per segment, because fatigue is per segment. The
stage's hidden-slice audit is the same arithmetic at production scale:
the aggregate curve reads cap 3 and sacrifices 28.5 casual expected
clicks to save 7.3 power clicks, while per-segment caps (casual 7,
standard 3, power 2) cut 6,152 impressions and lose 0 casual clicks.
The trade is on the cap's reach side, not its click side: the capped
run here earns 40,000 expected clicks against 22,429 uncapped, but it
also reaches fewer users per budget (the [cap-bites
detour](../when-the-cap-bites/) shows 10,000 users at cap 1 versus
1,000 at cap 10). Aharon et al. (2023, arXiv:2312.05052) priced the
reward side of getting the trade right — soft frequency capping lifted
revenue 7.3 percent in Yahoo Gemini Native — and the trade itself is
why the cap is a product decision, not a default.

## Evidence boundary

The executed expected-click arithmetic over a declared impression count
and decay curve (illustrative, deterministic). It demonstrates the
mechanism; real fatigue curves are estimated per user segment and
creative, and the cap is set against the measured curve.

## Check your mental model

Answer each before opening it.

**1. How can fewer impressions produce more clicks?**

<details>
<summary>Answer</summary>

Because the cap concentrates impressions where the click rate is high.
The capped run spends its delivery on the first three exposures, whose
rates are 0.05-0.03; the uncapped run spends most of its million
impressions at rates near 0.002. The sum favors the high-rate
concentration.

</details>

**2. What does the uncapped run waste besides clicks?**

<details>
<summary>Answer</summary>

User tolerance and the slots themselves. Every near-zero-exposure
impression is an ad the user did not want in a slot that could have
shown something else — the displacement cost stage 18 priced. Fatigue
is the ads-side version of the same externality: delivery past the
useful exposure is cost without return.

</details>

## Next

Back to [stage 25](../), where the cap is a value decision. The
[cap-bites detour](../when-the-cap-bites/) shows the cap's other cost:
shrinking reach.
