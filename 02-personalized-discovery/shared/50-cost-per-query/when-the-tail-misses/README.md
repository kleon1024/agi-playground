---
status: verified
level: applied
base: scratch
label: When the tail misses
verified: 2026-08-07
---

# The cache discounts the head and leaves the tail paying the full cascade

**Question:** [stage 50's cache detour](../when-the-cache-pays/) priced
the hit rate. This chapter asks which queries can hit at all, and
answers: query frequency is heavy-tailed, so the cache discounts the
head and never touches the long tail of unique queries — which pay the
full cascade cost and are the ones where the per-query budget is worst.

**Before this:** [stage 50 — cost per query](../) for the cascade cost
the cache discounts, and the [cache-pays detour](../when-the-cache-pays/)
for the hit-rate arithmetic this detour stratifies by query frequency.

## The stratified cost, executed

The run ([record](runs/2026-08-07-tail-misses-read.md)) splits traffic
into three query-frequency segments and prices each at the full cascade
cost (4.0 units) or the cache-hit cost (0.05 units):

| segment | traffic | hit rate | cost per query |
|---|---:|---:|---:|
| head | 40% | 95% | 0.25 |
| mid | 30% | 50% | 2.02 |
| tail | 30% | 0% | 4.00 |
| blended | 100% | 53% | 1.91 |

## The reading

The blended number (1.91 units against 4.00 uncached) is real but
misleading: it hides that 30% of traffic still pays the full 4.0,
because a unique query never repeats and never hits. The cache is a
head discount, not a capacity plan — the savings cap at the share of
traffic that repeats, and the tail is exactly where the per-query cost
is worst. Personalization makes the problem worse: the more the page is
personalized, the more of the traffic is unique, and the cache savings
shrink with it.

The tail is also where the stage's scale audit bites: cold, unique
queries are the recall-miss queries, and recall is the stage that
dominates the budget as the catalogue grows. So the two findings read
together — the cache can't help the tail, and the tail is where the
cost per query is highest and where recall owns the spend. The fixes
that actually move the tail cost are candidate-budget cuts and cheaper
recall for cold queries, not a bigger cache.

## Evidence boundary

The executed arithmetic over three declared traffic segments
(illustrative, deterministic). It demonstrates the stratification; real
cache design must measure the actual query-frequency distribution, the
per-query cache-hit rate by segment, and the recall-miss share before
sizing the cache against the blended number.

## Check your mental model

Answer each before opening it.

**1. Why can a cache never serve the tail queries?**

<details>
<summary>Answer</summary>

Because a cache serves what it has seen: a query that appears once in
the whole traffic stream is served from the cache on its first — and
only — occurrence at best, and usually not at all, so its effective hit
rate is zero. The cache's value is bounded by the share of traffic that
repeats, which is the head, not the tail.

</details>

**2. Why does personalization shrink the cache's savings?**

<details>
<summary>Answer</summary>

Because personalization makes queries unique: a slate built from the
user's session and history repeats less than a shared popular slate, so
more of the traffic moves from the head into the tail. The blended
saving falls toward the tail's full-cost share as the repeat rate
drops — which is why the cache is a head optimization, and why the tail
needs a different lever.

</details>

## Next

The query has a price; [stage 51 — new-user
experience](../../51-new-user-experience/) asks what to serve before the
logs exist — the traffic segment where this detour's tail is the whole
population.
