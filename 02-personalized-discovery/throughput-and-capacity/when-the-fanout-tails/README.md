---
status: verified
level: applied
base: scratch
label: When the fan-out tails
verified: 2026-08-07
---

# The query is as slow as its slowest shard

**Question:** [stage 49's capacity](../) sized one server by its queue.
This chapter asks what happens when one query touches many shards, and
answers: the query takes the max over its shards, so a 1% slow component
becomes an 18% slow query at fan-out 20 — and hedging (two copies, first
to finish wins) cuts the miss rate back to 3.4% at the price of 2x shard
work.

**Before this:** [stage 49 — throughput and capacity](../) and its queue
run, plus the [sizing-to-the-mean detour](../when-the-tail-costs/) for
the deadline the amplified tail misses.

## The amplification, executed

The run ([record](runs/2026-08-07-fanout-tails-read.md)) sends 10,000
queries against shards drawn from a 10ms / 150ms / 800ms mix and reads
the query as the max over its shards, plus a hedged variant at fan-out
20:

| fan-out | p99 | over 500ms |
|---:|---:|---:|
| 1 | 800ms | 1.1% |
| 5 | 800ms | 5.2% |
| 20 | 800ms | 18.5% |
| hedged-20 | 800ms | 3.4% |

## The reading

Per-shard latency never changed — the same 1% slow component produces a
query miss rate that grows from 1.1% to 18.5% as the fan-out factor
grows. This is the amplification Dean and Barroso name in "The Tail at
Scale" (Communications of the ACM, 2013): a query that fans out to N
independent shards is as slow as its slowest shard, so the tail is a
probability problem, not a per-shard latency problem. Hedging — send two
copies and take the first — cuts the miss rate to 3.4% because a query
only misses when both copies draw a slow shard; the price is 2x shard
work, which is why hedging is a budget decision, not a default.

The lesson for capacity planning: a per-shard p99 means nothing once a
query depends on the max of many shards. The number that matters is the
query-level tail, and it is a function of the fan-out factor and the
slow component's share — which is why a capacity team sizes against the
query path, not the component average.

## The fix and its trade

The fix is to size against the query-level tail — a function of the
fan-out factor and the slow component's share — and to budget hedging
where the deadline demands it. The executed simulation prices the
failure: the identical 1 percent slow component produces 1.1 percent
queries over 500ms at fan-out 1, 5.2 percent at fan-out 5, and 18.5
percent at fan-out 20, because the query is the max over its shards.
Hedging cuts the miss rate to 3.4 percent, since a hedged query only
misses when both copies draw a slow shard (0.185 squared).

The trade is that hedging is 2x shard work: the second copy doubles the
load on the very shards the query depends on, so the repair has a
capacity cost that the measurement team must price against the deadline
it protects. A per-shard p99 means nothing once a query depends on the
max of many shards, so the capacity number that matters is the
query-level tail — measured per query type, because fan-out differs
across the product.

## Who owns the loop

- **The capacity team** sizes against the query path and the query-level
  tail, not the component average.
- **The serving-infrastructure team** owns the fan-out factor per query
  type and the hedging budget that cuts the amplified tail.
- **The measurement team** measures the actual fan-out factor and the
  slow component's share, the two inputs the sizing formula depends on.

## Evidence boundary

The executed simulation over 10,000 declared queries (illustrative,
deterministic, seeded). It demonstrates the amplification mechanism; real
systems must measure the actual fan-out factor per query type, the slow
component's share, and the hedging budget before deciding where the
deadline is met.

## Check your mental model

Answer each before opening it.

**1. Why does a 1% slow shard become an 18% slow query at fan-out 20?**

<details>
<summary>Answer</summary>

Because the query is the max over its shards: the probability that none
of the 20 shards is slow is 0.99^20, about 0.815, so roughly 18.5% of
queries contain at least one slow shard and pay its latency. The slow
component's share is amplified by the fan-out factor, not by the shard's
own latency.

</details>

**2. Why does hedging cut the miss rate to 3.4% instead of to zero?**

<details>
<summary>Answer</summary>

Because a hedged query still misses when both copies draw a slow shard:
0.185^2 is about 0.034. Hedging does not remove the slow shard; it gives
each query a second independent draw, which turns the amplified
probability into its square. The residual miss rate is the cost side of
the redundancy trade.

</details>

## Next

The query path is sized; [stage 50 — cost per
query](../../50-cost-per-query/) prices what each query actually costs,
where the 2x shard work hedging introduced is a line item in the budget.
