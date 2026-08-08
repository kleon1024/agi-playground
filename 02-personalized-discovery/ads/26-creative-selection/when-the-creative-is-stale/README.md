---
status: verified
level: applied
base: scratch
label: When the creative is stale
verified: 2026-08-07
---

# Logged CTR mixes quality with wear

**Question:** [stage 26's creative selection](../) picks the creative
an ad shows. This chapter reads the executed wear comparison and asks
what logged CTR hides.

**Before this:** [stage 26 — creative selection](../) and its executed
per-context CTR model.

## The wear, executed

The run ([record](runs/2026-08-07-stale-creative-read.md)) reads three
creatives with their exposure histories:

| creative | logged CTR | exposure |
|---|---:|---|
| creative_a | 0.06 | 200,000 impressions |
| creative_b | 0.04 | mature |
| creative_c | 0.03 | new (cold start) |

## The reading

Logged CTR mixes the creative's quality with its wear. creative_a's
0.06 reflects 200,000 exposures — users have seen it, and its true
value has decayed below the log. creative_c's 0.03 is a cold-start
estimate with no wear history. A selection model that averages logged
CTR keeps choosing the stale winner on history while its actual value
falls, and never gives the new creative the traffic it needs to
estimate. Selection needs recency-aware estimates, not just averages.

## The fix and its trade

The measured fix is a recency-aware estimate: score the creative on a
rolling window or a decaying average so the estimate follows wear, and
allocate a small exploration budget so cold creatives get the traffic
their estimate needs. The stage's audit prices both halves: greedy on
lifetime CTR serves the stale winner all 20,000 placements for 635
clicks, while a recency-weighted EWMA (828) and Thompson sampling with
decaying counts (807) switch to the better creative once its estimate
moves (Moriwaki, Nakagawa, Hisano & Ariu, 2019, arXiv:1908.08936, model
creative value as wear-in and wear-out over served impressions; He et
al., 2014, ADKDD, describe the online-learning pipeline that keeps such
estimates fresh at serving scale). The trade is on the window: too
short, and the estimate chases noise and churns the selection; too
long, and it lags the wear the way the lifetime average does — the
0.06-forever estimate this detour names is the long-window extreme.

## Who owns the loop

- **The creative-ranking team** owns the recency-aware estimate: rolling
  windows or decaying averages that follow wear, so the 0.06-forever
  winner stops winning on history.
- **The delivery and exploration team** owns the cold-start traffic
  allocation that prices new creatives — the epsilon dial is its
  control.
- **The ads-measurement team** owns the per-creative-age split: CTR by
  exposure history, so wear and quality are read separately in the
  campaign report.

## Evidence boundary

The executed comparison over three declared creatives (illustrative,
deterministic). It demonstrates the confound; real systems model
creative wear per segment and use exploration (traffic allocation) to
keep cold-start estimates honest.

## Check your mental model

Answer each before opening it.

**1. Why is creative_a's 0.06 not its true value?**

<details>
<summary>Answer</summary>

Because the log mixes quality with wear. creative_a earned that 0.06
partly because it was fresh; after 200,000 exposures its marginal click
rate has decayed, but the average still carries the early high-rate
history. The average overstates what a new impression of creative_a is
worth now.

</details>

**2. What does a cold-start creative need?**

<details>
<summary>Answer</summary>

Traffic to estimate — which a pure average-based selection never gives
it, because it always loses to the stale winner. Selection needs an
exploration allocation (some impressions for new creatives) and
recency-aware estimates, or the system locks onto yesterday's winner
forever.

</details>

## Next

Back to [stage 26](../), where the creative is part of the ad's value.
The [context detour](../when-the-creative-context-changes/) shows the
second confound: the same creative's value also changes per placement.
