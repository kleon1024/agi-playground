---
status: verified
level: applied
base: scratch
label: When the interval decides
verified: 2026-08-06
---

# The bigger gap is not the more certain one

**Question:** [the significance chapter](../) compared two item-set sizes
with the same true effect. This chapter reads the recorded bootstrap and
asks why the larger observed gap is the one that proves nothing.

**Before this:** [the significance chapter](../) and its recorded paired
bootstrap.

## The two rows, read

The run ([record](runs/2026-08-06-interval-read.md)) reads the recorded
JSON:

| condition | score A | score B | observed gap | 95% CI | excludes 0 |
|---|---:|---:|---:|---|---|
| n=300 | 0.693 | 0.560 | 0.133 | (0.060, 0.207) | YES |
| n=25 | 0.640 | 0.440 | 0.200 | (−0.040, 0.440) | NO |

Both conditions have the same true per-item effect (+0.06).

## Two readings

**The point estimate and the confidence interval are different axes.** The
n=25 condition shows the *larger* observed gap (0.200 vs 0.133) — the same
true effect, sampled with more noise at low N, can easily look bigger by
chance. But its interval is wide enough to include zero, so no claim
survives. The n=300 condition's narrower interval sits entirely above zero:
the smaller-looking gap is the only one the data actually supports.

**The interval is the number that ships.** A ship/reject decision cannot be
made from the point estimate — it is made from whether the interval excludes
zero. The chapter's paired design cancels the item-difficulty noise both
scores share, and the recorded run is the concrete case where that design
matters: two scores, two intervals, and exactly one verdict.

## Evidence boundary

The recorded bootstrap (2,000 resamples per condition, one seed, synthetic
paired outcomes with a declared true effect of +0.06). It reads that
artifact; it does not re-run the bootstrap and does not extend the result
to real model scores, where the chapter's own discussion of test choice is
the boundary.

## Check your mental model

Answer each before opening it.

**1. How can the bigger gap (0.200) be the less certain result?**

<details>
<summary>Answer</summary>

Because the gap is a point estimate and the interval is the uncertainty
around it. At n=25, every draw of the sample moves the estimate a lot, so
the interval around 0.200 is wide — (−0.040, 0.440) — and includes zero. At
n=300 the noise is smaller, so the interval around 0.133 is narrow and
sits above zero. Confidence comes from the width, not the center.

</details>

**2. Why is "excludes zero" the decision rule rather than "gap is large"?**

<details>
<summary>Answer</summary>

Because zero is the null — "no real difference." A gap that is large but
whose interval includes zero is consistent with the null: the observed
difference could be pure sampling noise. Only when the interval excludes
zero has the data ruled the null out, which is the threshold a ship/reject
decision actually needs.

</details>

## Next

Back to [the significance chapter](../), or to
[why believe the number](../../../missions/01-language-model-agent/07-eval/why-believe-the-number/)
which applies the same discipline to a single score.
