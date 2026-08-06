---
status: verified
level: applied
base: scratch
label: When the tail waits
verified: 2026-08-06
---

# The step that the mean hides

**Question:** [the observability chapter](../) instrumented a training loop
and recorded the per-step time distribution. This chapter reads the
recorded histogram and asks what the mean cannot say.

**Before this:** [the observability chapter](../) and its recorded
instrumented run.

## The distribution, read

The run ([record](runs/2026-08-06-tail-read.md)) reads the recorded JSON:

| p50 | mean | p95 | min | max |
|---:|---:|---:|---:|---:|
| 18.45ms | 18.72ms | 21.14ms | 16.43ms | 29.94ms |

200 steps, 102,400 tokens.

## Two readings

**The mean is close to p50 and hides the tail.** 18.72ms mean vs 18.45ms
p50 — the mean is dominated by the typical step. The max step, 29.94ms, is
1.6x the mean. A latency budget set from the mean says "18.7ms is fine"
and silently misses the step that takes 30ms — which, in a real serving
system, is the step that becomes a timeout.

**p95 is the metric that catches what the mean cannot.** 21.14ms at p95 is
above the mean by 13% and below the max by 42%: it captures the slow tail
without being driven by a single outlier. This is why the chapter's
histogram, not its mean, is the evidence — and why the observability
chapter's own instrumented run reports p50 and p95 rather than an average.

## Evidence boundary

The recorded 200-step instrumented run (one model, one batch shape, local
CPU lane; the loss is on random input and is not a learning claim). It
reads that artifact; it does not re-run the training and does not extend
the distribution to GPU or multi-tenant serving, where tail behavior
changes.

## Check your mental model

Answer each before opening it.

**1. Why is the mean (18.72ms) so close to p50 (18.45ms)?**

<details>
<summary>Answer</summary>

Because most steps are near the typical time — the distribution is
concentrated, so the average lands where the median is. The mean only
diverges from the median when the distribution is skewed by a long tail,
and the recorded histogram shows exactly how mild that skew is at the
center and how sharp it is at the max. The mean is not wrong; it is blind
to the tail.

</details>

**2. When does the difference between mean and p95 decide a budget?**

<details>
<summary>Answer</summary>

Whenever the budget is a timeout. A 30ms step is fine inside a 100ms
budget and fatal inside a 25ms one — and a budget set from the mean would
have picked 25ms, missing the 20% of steps above it. p95 (or p99, for
harder SLOs) is the number that says how often the timeout fires, which is
the question a latency budget actually answers.

</details>

## Next

Back to [the observability chapter](../), or to
[the serving latency chapters](../../../missions/01-language-model-agent/05-serve/why-concurrency-pays/)
where the same p50/p95 discipline applies to a real decoder.
