---
status: verified
level: applied
base: scratch
label: When the tail costs
verified: 2026-08-07
---

# Sizing to the mean is sizing to a fiction

**Question:** [stage 49's capacity](../) sized by the deadline. This
chapter asks what the mean alone would have concluded, and answers: mean
service time suggests one capacity, the tail demands another — a server
provisioned on the mean drops a real share of queries past the deadline.

**Before this:** [stage 49 — throughput and capacity](../) and its
executed queue simulation.

## The mean's verdict, executed

The run ([record](runs/2026-08-07-tail-costs-read.md)) serves a mean of
17ms (mean capacity 59 req/s) at fractions of that capacity:

| load | p50 | p99 | over 100ms |
|---|---:|---:|---:|
| 50% of capacity (29 req/s) | 10ms | 242ms | 16.8% |
| 80% of capacity (47 req/s) | 71ms | 519ms | 43.6% |
| 100% of capacity (59 req/s) | 1144ms | 4112ms | 94.3% |

## The reading

At the capacity the mean suggests, a tenth of queries miss the deadline;
at half that load the tail still dominates the p99. Provisioning on the
mean is how a service "at capacity" spends its budget failing the slow
queries the mean never saw. The tail is a property of the distribution,
not a rounding error: the 5% of queries that take 150ms accumulate in the
queue at high load and become the p99 the users actually feel.

## The fix and its trade

The fix is to set capacity against the percentile the deadline names,
using the full measured service-time distribution, not the mean. The
executed simulation prices the failure — at the mean's verdict (59 req/s)
94.3 percent of queries miss the 100ms deadline, at 80 percent of that
load 43.6 percent still miss, and even at 50 percent (29 req/s) the tail
keeps 16.8 percent over. A server provisioned on the mean spends its
budget failing the slow queries the mean never saw.

The trade is that capacity set on the percentile is headroom the server
does not use most of the day: the gap between mean capacity and
percentile capacity is the cost of the tail, paid in idle hardware so
the slow 5 percent do not compound into the p99 users feel. The
service-time distribution, measured, is the input; the deadline is the
constraint; and the owner of the deadline decides which percentile the
capacity is actually bought for.

## Who owns the loop

- **The capacity team** measures the full service-time distribution and
  sizes against the percentile the deadline names.
- **The serving team** owns the deadline and the queue behavior that
  turns the slow 5 percent into the felt p99.
- **The product owner** decides which percentile the surface's deadline
  implies, since a 100ms p99 and a 100ms p50 buy different fleets.

## Evidence boundary

The executed queue simulation over declared service times (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the full service-time distribution, not the mean, and set capacity
against the percentile their deadline names.

## Check your mental model

Answer each before opening it.

**1. Why does 50% of mean capacity still miss 16.8% of deadlines?**

<details>
<summary>Answer</summary>

Because the mean hides the tail: the 5% of queries at 150ms dominate the
percentile even at moderate load. At 29 req/s most queries are fast, but
the slow ones arrive often enough that their wait time compounds and the
p99 climbs to 242ms. The mean said the server was half-idle; the deadline
said a sixth of users waited too long.

</details>

**2. What number should capacity actually be set against?**

<details>
<summary>Answer</summary>

The load at which the named percentile — p99, or whatever the surface's
deadline implies — clears the latency budget. That load is typically far
below the mean-capacity figure, and the gap is the cost of the tail. The
service-time distribution, measured, is the input; the deadline is the
constraint; the capacity is whatever satisfies both.

</details>

## Next

Back to [stage 49](../). The [peak-arrives
detour](../when-the-peak-arrives/) is the same tail under a spike: the
queue flood that turns a ten-minute surge into a capacity decision.
