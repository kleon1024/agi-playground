---
status: verified
level: applied
base: scratch
label: Throughput and capacity
verified: 2026-08-07
---

# Capacity is throughput times deadline, not throughput times average latency

**Question:** stages 43-48 made the pipeline fresher and the slate
smarter. This stage asks how much machine that costs, and answers: a
query takes a service time and requests arrive at a rate, so capacity
planning is throughput times deadline — the tail grows first, and sizing
to the average latency misses it.

**Before this:** [stage 08 — serving](../08-serving/) for the serving
path and its p95 budget, and [stage 48 — realtime user
state](../48-realtime-user-state/) for the per-request features this
load carries.

## The tail, executed

The run ([record](runs/2026-08-07-throughput-and-capacity.md)) simulates
a queue with 10ms mean service and 5% of queries at 150ms:

| load | p50 | p95 | p99 | over 100ms |
|---|---:|---:|---:|---:|
| 20 req/s | 10ms | 150ms | 170ms | 10.3% |
| 40 req/s | 10ms | 250ms | 370ms | 28.4% |
| 55 req/s | 192ms | 745ms | 933ms | 68.8% |

## The mechanism, named

Service averages 17ms, so the naive capacity is roughly 59 req/s. The
tail grows first: at 55 req/s the p99 is many times the p50 and a real
share of queries miss the 100ms deadline. The queue grows when arrival
rate nears service capacity, and the slow queries — not the average — are
what push latency past the deadline. Capacity planning is throughput
times deadline, not throughput times average latency: a service "at
capacity" by the mean is spending its budget failing the slow queries the
mean never saw.

## Why this belongs in the mission

The cascade's promise is a good slate inside a latency budget. This stage
is the accounting that keeps that promise: every stage added in 43-48 —
the store read, the realtime features, the monitors — spends the same
deadline and the same servers. Sizing to the mean is how a mission that
works in the demo dies under the peak, so capacity is not an
infrastructure afterthought; it is part of the ranking decision.

## Evidence boundary

The executed queue simulation over declared service times (illustrative,
deterministic). It demonstrates the mechanism; real capacity planning
needs the measured service-time distribution, the real arrival curve
(including the peak), and the deadline per surface.

## Check your mental model

Answer each before opening it.

**1. Why does the p50 stay at 10ms while the p99 grows to 933ms?**

<details>
<summary>Answer</summary>

Because most queries are fast — the p50 is unchanged by the queue — while
the slow 5% arrive into a growing backlog and wait behind each other. The
mean and median both look healthy while the tail explodes, which is why
the deadline metric is a percentile: a service judged by its average is
failing exactly the users who are waiting longest.

</details>

**2. What does "capacity" actually mean once the tail counts?**

<details>
<summary>Answer</summary>

A load below which the required percentile clears the deadline — e.g. the
load where p99 stays under 100ms. That is a different number than the
mean-service throughput, and the gap is the cost of the tail. Capacity is
therefore measured as throughput times deadline, and it changes whenever
the deadline, the service time, or the arrival curve changes.

</details>

## Next

The capacity number is set; stage 50 prices what each query actually
costs. A detour from here: [the peak is a capacity decision, not a load
average](when-the-peak-arrives/) — the executed read: at 2x the base load
the p50 crosses into seconds, and at 5x nearly every query misses the
deadline.

Another detour: [sizing to the mean is sizing to a fiction](when-the-tail-costs/)
— the executed read: at "100% of mean capacity" nine of ten queries miss
the deadline.
