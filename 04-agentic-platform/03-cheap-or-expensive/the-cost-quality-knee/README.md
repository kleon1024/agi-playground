---
status: verified
level: applied
base: scratch
label: The cost-quality knee
verified: 2026-08-06
---

# The expensive tier is not the fastest

**Question:** [stage 03's tier comparison](../) resolved every attempt at
every tier, so cost and latency are the differentiators. This chapter reads
the recorded run and asks where the tiers actually sit.

**Before this:** [stage 03's tier comparison](../) and its recorded JSONL.

## The tiers, read

The run ([record](runs/2026-08-06-knee-read.md)) reads the recorded costs:

| tier | \$/attempt | median wall-clock | turns |
|---|---:|---:|---:|
| haiku | 0.1604 | 90.8s | 10.5 |
| sonnet | 0.5368 | 63.6s | 9.8 |
| opus | 0.8226 | 83.8s | 11.2 |

All tiers: 6/6 resolved.

## Two readings

**When resolve rate separates nothing, cost and latency are the strategy.**
Every tier resolved every attempt — 18/18 total — so the comparison is not
"which tier wins" but "which tier is worth its price." The knee: sonnet is
cheaper than opus (0.54 vs 0.82 per attempt) AND faster (63.6s vs 83.8s
median), so the most expensive tier is not the fastest — opus costs 5x
haiku with no resolve gain and slower median latency than sonnet.

**The run's own probe on the patches is what makes the tiers comparable.**
Because resolve was saturated, the stage probed the patches for
generality — whether the fix transfers beyond the failing test. That is
the quality axis resolve could not show, and it is what turns three
identical resolve tables into a real comparison.

## The fix and its trade

The fix is to report cost and latency beside resolve rate, and to probe
the patches when resolve saturates: every tier resolved 18/18, so the
comparison is not "which tier wins" but "which tier is worth its price."
The trade is that the probe, not the resolve table, carries the quality
axis — three tiers at 6/6 look identical, and without the probe a tier
that overfits the test suite would still "resolve" everything. The knee
measured here (sonnet cheaper and faster than opus: \$0.54 vs \$0.82 and
63.6s vs 83.8s) is only visible because the stage kept the cost and
latency columns; dropping them would leave the most expensive tier
looking justified by nothing.

## Who owns the loop

- **The routing owner** owns the tier decision: cost per attempt is not
  the strategy when resolve is saturated — cost per resolved and the
  quality probe are.
- **The eval team** owns the probe and its boundary: it checks
  generality, and it was written after reading diffs, so it finds
  failure modes without estimating rates.
- **The cost owner** owns the numbers' provenance: the figures are
  list-price equivalents on a subscription, and the tier ratios, not the
  absolute dollars, are the durable part.

## Evidence boundary

The recorded tier run (18 attempts, 2 tasks x 3 tiers x 3 seeds, list-price
equivalent costs on a subscription). It reads that artifact; it does not
re-call any model and the costs are list-price, not billed charges.

## Check your mental model

Answer each before opening it.

**1. Why is cost per attempt not the same as cost per resolved task?**

<details>
<summary>Answer</summary>

Because at this stage every attempt resolved, the two are the same — which
is the point: resolve saturation removes the denominator difference. At
stage 01 (no harness), resolve differed by tier, so per-success cost was
the metric. Here the stage's question is what the tier is worth when it
always resolves, and the answer is cost and latency.

</details>

**2. What does the probe add that the resolve table cannot?**

<details>
<summary>Answer</summary>

A quality axis. Three tiers at 6/6 resolve look identical; the patch probe
checks whether each fix generalizes beyond the specific failing test. That
is where a tier could quietly overfit to the test suite and still "resolve"
everything — the probe is what keeps the all-equal resolve table from
being the whole story.

</details>

## Next

Back to [stage 03](../), or to
[when every tier resolves everything, which tier won](../the-tier-that-won/)
which reads the same run's winner side.
