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

## How you find it: the load scan with a deadline, executed

Capacity is found by load-testing with a deadline, not by arithmetic on
the mean. The run ([record](runs/2026-08-07-throughput-and-capacity.md))
scans arrival rates from 20 to 60 req/s, and the audit
([record](runs/2026-08-07-capacity-audit.md) —
[`prod/capacity_audit.py`](prod/capacity_audit.py)) reads the load at
which the deadline percentile is met:

| load | utilization | p50 | p95 | p99 | over 100ms |
|---:|---:|---:|---:|---:|---:|
| 20 | 34% | 10ms | 150ms | 170ms | 10.3% |
| 30 | 51% | 10ms | 150ms | 267ms | 17.9% |
| 40 | 68% | 10ms | 250ms | 370ms | 28.4% |
| 45 | 76% | 44ms | 324ms | 459ms | 37.8% |
| 50 | 85% | 100ms | 460ms | 620ms | 48.4% |
| 55 | 94% | 192ms | 745ms | 933ms | 68.8% |
| 60 | 102% | 1850ms | 3003ms | 3223ms | 94.2% |

The verdict is DEADLINE UNACHIEVABLE: p95 of the service mix (150ms)
exceeds the 100ms deadline at every load, because the 5% slow service
is itself over the deadline. No machine count satisfies a p95 deadline
tighter than the service tail — the mean capacity (59 req/s) is the
divergence load, not a serving answer, and the fix is cutting the
service tail (hedge, timeout, parallel shards) before adding machines.
This is the audit half of the stage's claim: the tail is a property of
the service-time distribution, and capacity planning that skips the
load test confuses the divergence load with the deadline load. Dean and
Barroso make the same point for fan-out systems ("The Tail at Scale",
Communications of the ACM, 2013): per-component latency means nothing
once a query depends on the max of many components.

## The fix and its trade

The fix is to load-test with a deadline and cut the service tail before
adding machines: no machine count satisfies a p95 deadline tighter than
the service mix's own tail, so the levers are hedging, timeouts, and
parallel shards on the slow component. The audit prices the repair — the
p95 of the service mix (150ms) exceeds the 100ms deadline at every load
while p50 stays at 10ms, and at 55 req/s the p99 reaches 933ms with 68.8
percent of queries over the deadline — so the mean capacity (59 req/s)
describes when the queue diverges, not when the page meets its budget.

The trade is that cutting the tail spends latency budget or work
elsewhere, and the capacity number expires whenever the inputs move. A
hedge serves a redundant shard at 2x work to cut a fan-out's miss rate
from 18.5 percent back to 3.4 percent, and the peak detour shows the
arrival curve is part of the answer: at 2x the base load the p50 crosses
into seconds and at 5x nearly every query misses the deadline, so the
capacity scan has to be re-run when the deadline, the service-time
distribution, or the launch calendar changes — the traffic team owns the
arrival curve, the service owner owns the tail, and neither can be
replaced by buying servers.

## Who owns the loop

The scan produces a number; someone must own what happens when the
deadline moves, and the handoff is where capacity planning fails:

- **The serving platform team** owns the load test and the capacity
  number: the arrival curve, the deadline per surface, and the load at
  which p95 misses. It owns the instrument, not the fix.
- **The service owner** owns the service-time distribution: the slow
  component that the scan exposes, and the decision to cut it (hedge,
  timeout, shard-parallel) rather than add machines to a tail no
  machine count satisfies.
- **The traffic team** owns the arrival curve: the peak plan (the
  when-the-peak-arrives detour) and the launch calendar that decides
  whether the platform's servers ever see the scan's crossing load.

When the ownership is implicit, the load test runs into a vacuum: the
platform team can name the crossing load, but nobody owns the service
tail, so the response to "p95 misses at every load" is buying servers —
the expensive way to fail the slow queries the mean never saw.

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

**3. Why is the mean capacity (59 req/s) not a capacity answer?**

<details>
<summary>Answer</summary>

Because it is the divergence load — where the arrival rate equals the
mean service rate and the queue grows without bound — not the load where
the deadline is met. Here the p95 of the service mix itself (150ms)
already misses the 100ms deadline at every load, so no server count
clears the deadline; the mean number describes when the queue diverges,
which is a different question from whether the page meets its budget.

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

A third detour: [the query is as slow as its slowest
shard](when-the-fanout-tails/) — the executed read: the same 1% slow
component becomes an 18.5% slow query at fan-out 20, and hedging cuts
the miss rate back to 3.4% at 2x shard work.
