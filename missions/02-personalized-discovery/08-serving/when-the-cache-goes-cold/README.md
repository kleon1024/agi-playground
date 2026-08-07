---
status: verified
level: applied
base: scratch
label: When the cache goes cold
verified: 2026-08-07
---

# The cache that misses together

**Question:** [stage 08's serving path](../) holds a p95 latency budget.
This chapter reads the executed refresh-policy run and asks why cache
misses are a tail problem rather than a mean problem.

**Before this:** [stage 08 — serving](../) and its executed latency
analysis.

## The policies, executed

The run ([record](runs/2026-08-07-cold-cache-read.md)) compares two
refresh policies over 100 requests (2 ms hit, 50 ms miss):

| policy | p95 |
|---|---:|
| synchronized refresh | 50 ms |
| staggered refresh | 2 ms |

## Two readings

**Cache misses are cheap alone and expensive together.** One miss costs
50 ms; twenty misses in the same window push the p95 to 50 ms because a
fifth of requests now pay the miss price. The same number of refreshes
staggered across the day keeps the p95 at 2 ms. The cost is not in the
misses — it is in the correlation between them.

**Tail latency is a scheduling property as much as a compute one.** The
work performed is identical in both runs; only the timing differs. A
synchronized refresh converts a cold window into a p95 breach, and the
failure is invisible to average latency. Stage 08's p95 budget is a
statement about correlation: the serving path has to schedule refreshes
so that misses do not arrive together, which is a design decision, not an
operational accident.

## Evidence boundary

The executed hand-built request timeline (illustrative, deterministic).
It demonstrates the correlation mechanism; real caches have measured
miss costs and refresh durations, which set the stagger that keeps the
tail inside the budget.

## Check your mental model

Answer each before opening it.

**1. Why is the p95 50 ms when most requests hit?**

<details>
<summary>Answer</summary>

Because p95 reports the 95th percentile, and a synchronized refresh puts
20 of 100 requests into the miss window. The fifth of requests that miss
all pay 50 ms, so the 95th percentile is a miss. Average latency hides
this — the mean stays near 10 ms — which is why the budget is stated as
p95 and why the schedule must keep misses from clustering.

</details>

**2. What does the staggered policy change about the same work?**

<details>
<summary>Answer</summary>

Nothing about the amount of work — the same number of refreshes happen —
and everything about when. Each staggered refresh misses at most one or
two requests, so no window contains a cluster of misses and the p95
stays at the hit cost. The run isolates the variable: identical work,
different correlation, different tail. The serving design chooses the
correlation on purpose.

</details>

## Next

Back to [stage 08](../), or to
[the cut that bites](../when-the-cut-bites/) for the latency the pre-rank
cut buys on the same serving path.
