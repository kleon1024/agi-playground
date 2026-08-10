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

## The fix and its trade

The failure mode is a budget set from the mean: it says "18.7ms is fine"
and silently misses the step that takes 29.94ms — 1.6x the mean — which in
a real serving system is exactly the step that becomes a timeout. You find
the case by reading the recorded distribution rather than re-running the
training: the mean (18.72ms) sits close to p50 (18.45ms) because the
histogram is concentrated at the centre, and that closeness is precisely
the blindness — the mean only diverges from the median when a long tail
skews the distribution, and this recorded run's skew is sharp at the max.

The fix is to set the budget from a percentile that names how often the
timeout fires: p95 (21.14ms) is above the mean by 13% and below the max by
42%, so it captures the slow tail without being driven by a single outlier,
and p99 is the stricter variant for harder SLOs. The trade is strictness
for coverage — a budget set from the mean at 25ms silently fails the 20% of
steps above it, while a p95 budget buys the tail at the cost of rejecting
latencies the mean would have accepted. The chapter's evidence boundary is
explicit: it reads the recorded 200-step artifact (one model, one batch
shape, local CPU lane; loss on random input is not a learning claim) and
does not extend the distribution to GPU or multi-tenant serving, where tail
behavior changes.

## Who owns the loop

- **The observability team** owns the histogram contract: the recorded
  p50/mean/p95/min/max row is the artifact this chapter reads, and the
  percentile-over-mean discipline is the reporting standard it inherits
  from the parent chapter.
- **The serving team** owns the timeout: the SLO that decides whether a
  30ms step is fine inside a 100ms budget or fatal inside a 25ms one, and
  the p95/p99 choice is how often the timeout may fire.
- **The evaluation team** owns the budget decision: which percentile the
  latency budget is set from, and the verification that a change to the
  step-time distribution actually moved the tail the budget was meant to
  bound.
- **The model team** inherits the read: a step-time distribution is how a
  training or serving change is attributed, and the max-versus-mean gap is
  the signal that a mean-based report is hiding a real tail.

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
[the serving latency chapters](../../why-concurrency-pays/)
where the same p50/p95 discipline applies to a real decoder.
