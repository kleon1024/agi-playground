---
status: verified
level: applied
base: scratch
label: When the cache pays
verified: 2026-08-07
---

# The cache pays when the hit rate is a cost decision

**Question:** [stage 50's cascade](../) costs 4.0 units per query. This
chapter asks how a cache changes that arithmetic, and answers: the served
query is cheaper than the computed one — the cache turns a per-query cost
into a per-unique-query cost, and the hit rate decides how much it saves.

**Before this:** [stage 50 — cost per query](../) and its executed cascade
arithmetic.

## The hit-rate sweep, executed

The run ([record](runs/2026-08-07-cache-pays-read.md)) computes the
per-served-query cost from a full cost of 4.0 units:

| hit rate | cost per served query |
|---|---:|
| 0% | 4.00 units |
| 50% | 2.02 units |
| 90% | 0.44 units |
| 99% | 0.09 units |

## The reading

At 90% hits the per-served cost drops to a tenth of the full path. The
cache is not free — it trades freshness for cost, and a stale cached
slate is the same trade as a stale model (stage 46). The hit-rate curve
is where the cache decision is measured: how much of the budget a cache
saves depends on how often the same query returns, which is a property of
the traffic, not of the cache.

## Evidence boundary

The executed sweep over a declared full cost (illustrative,
deterministic). It demonstrates the mechanism; real cache decisions must
measure the actual hit rate per query class, the staleness cost of a
cached slate, and the invalidation rules that balance them.

## Check your mental model

Answer each before opening it.

**1. Why does 50% hits save only half the cost, not exactly half?**

<details>
<summary>Answer</summary>

Because a served query still costs something: 4.0 units for a miss, 0.08
for a cheap cache read on a hit, so 50% hits gives 2.02 units — slightly
more than half. The cache removes the expensive path but adds a cheap
one; the arithmetic is miss-rate times full cost plus hit-rate times
cache-read cost.

</details>

**2. What does a cache have in common with a stale model?**

<details>
<summary>Answer</summary>

Both trade freshness for cost. A cached slate is a snapshot: the fresher
the user's state, the more the cache is wrong about it. The same measured
staleness logic from stage 46 applies — how old a cached value may be
before the savings stop paying — which is why cache invalidation is a
policy decision, not a plumbing detail.

</details>

## Next

Back to [stage 50](../). The [model-is-too-big
detour](../when-the-model-is-too-big/) is the other side of the budget:
what a bigger model buys, and whether the gain clears the doubled bill.
