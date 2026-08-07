---
status: verified
level: applied
base: scratch
label: Ads measurement
verified: 2026-08-07
---

# Measure the ad by what it changed

**Question:** every ads stage so far optimized what the platform
controls. This stage asks how anyone knows the ad worked, and answers:
by incrementality — the exposed group's outcome minus the control
group's, the part the ad actually caused.

**Before this:** [stage 24 — search measurement](../../search/24-search-measurement/)
for the measurement discipline, and [stage 27 — bid strategy](../27-bid-strategy/)
for the advertiser whose budget the measurement decides.

## The lift, executed

The run ([record](runs/2026-08-07-ads-measurement.md)) compares exposed
and control conversion rates:

| group | conversion rate |
|---|---:|
| exposed | 0.032 |
| control | 0.028 |
| lift | 14.3% |
| increment | 0.4 points |

## The mechanism, named

The exposed group converts at 0.032, but 0.028 of that would have
happened without the ad. The increment is 0.4 points — the part the ad
actually caused. Attribution that ignores the control group credits the
ad with the baseline, which is the [overcount detour](when-attribution-overcounts/)
measures, and the [zero-lift detour](when-the-incrementality-is-zero/)
shows why the null result matters: a campaign that delivered millions
of impressions and changed nothing must be reported as exactly that.

## Why this belongs in the mission

This is the ads track's version of the mission's outcome rule — every
capability claim is backed by a measurable outcome. Recommendation has
its offline replay; ads have incrementality. Without the control group,
the ads track would report clicks it never caused, which is the same
failure as a random split leaking the future in [stage
00](../../shared/00-interactions/): the measurement, not the model, decides what
the numbers mean.

## Evidence boundary

The executed incrementality split over two declared rates (illustrative,
deterministic). It demonstrates the arithmetic; real incrementality
needs a properly randomized holdout, which the mission's ad-load
guardrail (hold the ad load fixed across arms) is the offline analogue
of.

## Check your mental model

Answer each before opening it.

**1. Why does the raw click rate overstate the ad's effect?**

<details>
<summary>Answer</summary>

Because some of the exposed users would have converted anyway. The
control group converts at 0.028, so the ad's increment is only the
difference — 0.4 points out of 0.032. Without a control group, the
baseline gets credited to the ad, and spend follows the wrong signal.

</details>

**2. What is a zero-lift result for?**

<details>
<summary>Answer</summary>

It is the null result measurement exists to find. If exposed and control
both convert at 0.030, the campaign changed nothing, and a report that
shows clicks without lift is crediting spend with no effect. Reporting
zero lift is how the measurement protects the next budget decision.

</details>

## Next

This closes the advanced ads track (stages 25-30). The mission's three
surfaces — recommendation, search, ads — now each run from problem to
measured outcome. Return to [the mission README](../../) for the full
path.

A detour from here: [the measurement model decides which channel gets
the budget](when-attribution-overcounts/) — the executed credit read:
the three touchpoints share 0.4/0.2/0.4, but last-click gives email all
1.0, overcounting by 0.6 and misallocating spend.

Another detour: [zero lift is the null result measurement exists to
find](when-the-incrementality-is-zero/) — the executed null read:
exposed and control both convert at 0.030 for a +0.0% lift, so the
campaign changed nothing and a report that hides it credits spend with
no effect.
