---
status: verified
level: applied
base: scratch
label: When the second model costs
verified: 2026-08-07
---

# The calibration layer is a second model with its own freshness cost

**Question:** the stage-64 audit shows the naive click head's calibration
slope at 1.188 — the ranking score is not a probability. This chapter
repairs the mapping with temperature scaling and measures the real cost:
the calibrated head is only as fresh as its re-fit cadence.

**Before this:** [stage 64](../) and [stage 05 — the value
tree](../../../shared/05-value-tree/), where every probability the model
emits feeds money decisions. This detour is the probability-repair axis
of the seesaw.

## The repair, executed

The run ([record](runs/2026-08-07-calibration-layer-read.md)) fits a
temperature on the head's scores and reads the slope/intercept pair
before and after a distribution shift:

| read | slope | intercept |
|---|---:|---:|
| raw scores | 1.098 | -0.067 |
| temperature-scaled | 0.983 | -0.009 |
| shifted, raw | 1.097 | -0.165 |
| shifted, stale T | 0.980 | -0.106 |

Fitted temperature: 0.85.

## The reading

Temperature scaling (Guo et al., ICML 2017, arXiv:1706.04599) moves the
slope from 1.098 to 0.983 on the split it was fitted on — the ranking
score becomes a probability. But the layer is a second model: after a
shift, the raw scores' intercept moves (-0.067 to -0.165) and the frozen
temperature is wrong for the new distribution (intercept -0.106 instead
of -0.009). The cost is operational, not architectural: a monitoring job
on the slope/intercept pair, a re-fit cadence, and a handoff to every
pCTR consumer. The value tree multiplies the number, so an uncalibrated
or stale head leaks into every downstream decision — the same ownership
shape as the model-staleness loop, one layer down.

## Evidence boundary

The executed synthetic read over one fitted temperature and one declared
shift (illustrative, deterministic, single seed). It demonstrates the
repair and its freshness failure; real systems must monitor the
slope/intercept pair on production traffic and set the re-fit cadence
from the measured shift rate.

## Check your mental model

Answer each before opening it.

**1. Why does a frozen temperature break after a shift?**

<details>
<summary>Answer</summary>

Because temperature is a summary of the score distribution it was fitted
on. When the distribution shifts — new items, new traffic mix, a
reranker change upstream — the same temperature maps the new scores to
the wrong probabilities. The executed read shows the intercept drifting
to -0.106 with the stale T, while a fresh fit would have read -0.009.

</details>

**2. What is the calibration layer's real cost?**

<details>
<summary>Answer</summary>

Operations: a monitoring job on the slope/intercept pair, a re-fit
cadence tied to the measured shift rate, and a handoff to every consumer
of the probability. It is a second model, and it fails like one — not a
one-time fix.

</details>

## Next

Back to [stage 64](../), where the three axes of the seesaw — slice,
task, and calibration — are now all readable.
