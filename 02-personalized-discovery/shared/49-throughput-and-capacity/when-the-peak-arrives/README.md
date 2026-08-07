---
status: verified
level: applied
base: scratch
label: When the peak arrives
verified: 2026-08-07
---

# The peak is a capacity decision, not a load average

**Question:** [stage 49's capacity](../) sized the service by load. This
chapter asks what happens when the load spikes, and answers: a ten-minute
spike is a capacity decision, not a load average — the queue grows,
latency crosses the deadline, and the share of dropped queries is the
real cost.

**Before this:** [stage 49 — throughput and capacity](../) and its
executed queue simulation.

## The spike, executed

The run ([record](runs/2026-08-07-peak-arrives-read.md)) simulates the
base load at 30 req/s with the service mean at 17ms:

| load | p50 | p99 | over 100ms |
|---|---:|---:|---:|
| 1x (30 req/s) | 10ms | 267ms | 18.8% |
| 2x (60 req/s) | 8737ms | 11850ms | 99.4% |
| 5x (150 req/s) | 108383ms | 208810ms | 100.0% |

## The reading

At 1x the service is comfortable; at 2x the tail crosses the deadline;
at 5x most queries miss it. The peak does not raise the average — it
floods the queue. Capacity for the peak is bought with idle servers the
rest of the day, or paid for with dropped queries at the peak. The
decision is the trade between the two, and it belongs to whoever knows
what a dropped query costs.

## Evidence boundary

The executed spike over three declared multiples (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the actual arrival curve, the cost of a dropped query, and the idle cost
of standby capacity before choosing where on the curve to sit.

## Check your mental model

Answer each before opening it.

**1. Why does 2x load push the p50 from 10ms to seconds?**

<details>
<summary>Answer</summary>

Because the queue saturates: at 60 req/s against a 17ms mean service,
requests arrive faster than they finish, so nearly every request waits
behind a growing backlog. The p50 stops being "the fast typical query"
and becomes "a query that waited in line". The peak does not raise the
average; it flips the queue into overload.

</details>

**2. What is the real cost of the 5x peak?**

<details>
<summary>Answer</summary>

Every query over the deadline is effectively a failed or degraded
response — 100% of them at 5x. The cost is not latency on a chart; it is
users who left, ads that did not load, or searches that returned nothing.
That is the number to compare against the idle cost of keeping standby
servers for the ten minutes a day the spike lasts.

</details>

## Next

Back to [stage 49](../). The [tail-costs
detour](../when-the-tail-costs/) is the same lesson without the spike:
even at steady load, the mean underestimates what the tail demands.
