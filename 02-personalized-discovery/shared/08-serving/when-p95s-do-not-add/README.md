---
status: verified
level: applied
base: scratch
label: When p95s do not add
verified: 2026-08-06
---

# Means add for the serial path; tail percentiles do not

**Question:** [stage 08's serving budget](../) composes stage latencies
under a p95 target. This chapter reads the recorded latency run and asks
why the obvious rule — add up the p95s — is wrong.

**Before this:** [stage 08's serving](../) and its recorded latency
harness.

## The numbers, read

The run ([record](runs/2026-08-06-p95-read.md)) reads the recorded output:

| configuration | mean | p95 |
|---|---:|---:|
| serial funnel | 52.73 ms | 72.71 ms |
| parallel, no cache | 31.22 ms | 49.31 ms |
| parallel, 80% cache | 7.00 ms | 34.52 ms |
| p95-sum estimate (parallel) | — | 54.74 ms vs measured 49.31 |

## Two readings

**Summing per-stage p95s overestimates the end-to-end tail.** A request is
slow only when its own stage draws align in the tail, and every stage's
separate 95th-percentile requests usually land on different traces. The
recorded evidence: the p95-sum (54.74 ms) sits 5.43 ms above the measured
parallel p95 (49.31 ms). The trap is that the rule "feels" right and is
wrong — means add, tail percentiles do not.

**The parallel/cache rows are the composition rules in action.** Serial
recall (four queues at the sum of their waits) produced 52.73/72.71 ms;
parallel recall (at the slowest wait) produced 31.22/49.31 ms — the
critical path, not the sum, is what the request pays. The 80% cache row
collapses p95 to 34.52 ms. Parallel fan-out and caching are real changes to
the request's critical path, and the run measures each.

## Evidence boundary

The recorded latency harness (5,000 simulated requests, hand-chosen and
disclosed per-stage lognormals, single process). It reads that artifact; it
does not re-run the simulation and the numbers are outputs of a declared
model, not timings of a real system.

## Check your mental model

Answer each before opening it.

**1. Why does the p95-sum overestimate the end-to-end p95?**

<details>
<summary>Answer</summary>

Because tail events rarely align. The 95th percentile of stage A and the
95th percentile of stage B are different requests' draws; a single request
is slow only when its own draws across stages all land high. Summing the
per-stage p95s assumes the worst case for every stage on the same trace,
which is far rarer than 5% — so the sum (54.74) sits above the true tail
(49.31).

</details>

**2. What does the cache row change about the budget decision?**

<details>
<summary>Answer</summary>

It turns the budget from a question of which stages to cut into a question
of how much to cache. The 80% cache row (p95 34.52 ms) fits the 300ms
target with room to spare, while the uncached parallel row (49.31 ms)
already fits it too — the cache buys margin, not eligibility, at this
scale. The budget decision is about headroom and tail robustness, and the
three rows are the evidence.

</details>

## Next

Back to [stage 08](../), or to
[what the pre-rank cut buys](../when-the-cut-bites/) which reads the same
stage's cut-sweep side.
