---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Observability
---

# A mean step time hides the step that just took three times as long

**Goal:** instrument a real training loop with real per-step timing, and
compute the distribution — not a single average — the same way
[the serving stage](../why-concurrency-pays/) already insists on for
inference latency: p50 and p95, always, never a lone mean.

Every mission in this repository reports wall-clock in its `runs/` entries.
None of them show *why* that number is what it is — whether every step took
about the same time, or whether a few slow steps dragged a mean up while most
steps were fast. That distinction is the entire point of observability: a
mean can look fine while a tail of slow steps quietly doubles a job's real
completion time.

**Before this:** [`foundations/04-distributed-training/orchestration/`](../../../foundations/04-distributed-training/orchestration/) measured
*which job* gets a slot first. This chapter measures *how long a slot's work
actually takes*, step by step, once it has one.

```bash
cd core && python instrumented_train.py --steps 200 --out ../runs
```

## The one idea in this chapter

`core/instrumented_train.py` imports `Config` and `Transformer` unmodified
from [mission 01's pretraining core](../../02-pretrain/core/model.py)
— no line of that file changes — and wraps its own training step with
`time.perf_counter()` before and after each forward/backward/optimizer-step,
collecting one real sample per step. After 5 unmeasured warmup steps (same
reason `foundations/04-distributed-training/orchestration` needs one: lazy initialization cost that has
nothing to do with steady-state latency) and 200 measured steps on a tiny
2-layer, 128-dim model:

```
step time p50 = 18.45ms   p95 = 21.14ms
histogram (step-time buckets, count):
  16.43ms : ################################################################ (76)
  18.12ms : ##################################################################### (99)
  19.81ms : ################ (16)
  21.50ms : ## (2)
  23.19ms : #### (4)
  26.57ms : ## (2)
  28.26ms : # (1)
```

Most steps (175 of 200) land in the two fastest buckets, 16-20ms. But the
tail is real: a handful of steps ran 23-28ms — 25-50% slower than the
typical step, almost certainly Python garbage collection or OS thread
scheduling jitter landing on that particular step, not anything about the
model or data. **A mean over these 200 steps would be pulled toward that
tail without telling you the tail exists.** p50 (18.45ms) tells you what a
typical step costs; p95 (21.14ms) tells you what a not-rare-at-all step
costs; the histogram tells you the shape neither single number can. All
three come from the same 200 real samples — this is not three different
runs, it's three different ways of reading one measured distribution.

## Why a counter and a histogram are different instruments

`counters["steps"]` and `counters["tokens"]` are monotonic counts — they only
increase, and they answer "how much work happened," a question a single
number can fully answer. Step-time is a *distribution*, not a count — the
same total step count could hide a distribution that is uniformly 18ms or
one that is 15ms half the time and 40ms the other half, and only the
histogram (or the percentiles computed from it) distinguishes the two.
Reaching for a mean where a distribution is the real answer is the single
most common observability mistake this chapter exists to name.

## What this does not show

**No real GPU.** This run is CPU-only, on a model sized to run in
milliseconds per step specifically so the *instrumentation pattern* is
checkable quickly. A production training job's step-time tail has different
real causes (data-loader stalls, NCCL collective stragglers, checkpoint
writes landing mid-step) that this toy loop's tail (GC pauses, OS
scheduling) does not represent.

**No real metrics backend.** `core/` collects samples in-process and dumps
one JSON file at the end. A real observability stack (Prometheus scraping a
`/metrics` endpoint, a Grafana dashboard, an OpenTelemetry collector) streams
these numbers continuously and lets you query them after the fact across
many runs — none of that infrastructure is built or claimed here; this
chapter teaches the *statistic*, not the *pipeline* that would serve it at
scale in production.

## A brief history

The percentile-over-mean argument this chapter makes has a canonical
reference: Dean and Barroso's "The Tail at Scale" (*Communications of the
ACM*, 2013) documented, at Google's production scale, that a service's p99
latency governs user-perceived performance far more than its mean once
enough parallel calls are in flight -- because a single slow straggler
dominates a fan-out request. That is the same distinction this chapter's
p50/p95 histogram draws for a training loop's own per-step time, just
without the fan-out.

## Exercises

1. Raise `--steps` to 1000 and watch whether p95 stabilizes or the tail
   grows — a fixed OS/GC-jitter tail should stay roughly the same absolute
   size regardless of step count, while a tail that scales with step count
   would point to a real leak (e.g. an unbounded list growing every step).
2. Deliberately inject a slow step (e.g. `time.sleep(0.05)` every 20th step)
   and confirm it shows up in p95 but not necessarily in p50 — the exact
   distinction a mean would blur.
3. Compute p99 instead of p95 and compare how much more the single slowest
   observed step (28.26ms here) dominates it.

## Run record

[`runs/2026-08-01-instrumented-training.md`](runs/2026-08-01-instrumented-training.md)
— 200 steps, CPU (local dev box), \$0.

A detour from here: [the step that the mean hides](when-the-tail-waits/) —
the recorded distribution read: p50 18.45ms and mean 18.72ms hide the
29.94ms max (1.6x the mean), which is why p95 exists as the metric a
latency budget actually needs.
