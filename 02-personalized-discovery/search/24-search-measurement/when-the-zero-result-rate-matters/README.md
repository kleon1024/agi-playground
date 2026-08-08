---
status: verified
level: applied
base: scratch
label: When the zero-result rate matters
verified: 2026-08-07
---

# Zero results is a coverage metric with a revenue shape

**Question:** [stage 24's search measurement](../) reads the zero-result
rate. This chapter prices it and asks why it belongs in the report
next to NDCG and MRR.

**Before this:** [stage 24 — search measurement](../) and its executed
zero-result model.

## The cost, executed

The run ([record](runs/2026-08-07-zero-matters-read.md)) prices the
rate through abandonment on a daily volume:

| number | value |
|---|---:|
| daily queries | 100,000 |
| zero-result | 8,000 (8%) |
| likely lost users | 4,800 (60% abandonment) |

## The reading

8% of queries return nothing and 60% of those users leave — an estimated
4,800 lost users a day. The zero-result rate is not a log curiosity; it
is a coverage metric with a revenue shape. NDCG and MRR measure how
well ranked results satisfy queries that have results; the zero-result
rate measures the queries where ranking never ran, which is where the
funnel loses users before quality can matter.

## The fix and its trade

The fix is to price the zero-result rate through abandonment as a
coverage metric with a revenue shape, with the causes attached. The
executed pricing shows the shape: 100,000 daily queries, 8,000
zero-result (8%), and at 60% abandonment an estimated 4,800 lost users
per day. NDCG and MRR measure how well ranked results satisfy queries
that have results; the zero-result rate measures the queries where
ranking never ran, which is where the funnel loses users before quality
can matter.

The trade, named: the pricing depends on an abandonment rate that must
be measured from follow-up session behavior, not assumed — and the
headline 8% without the cause breakdown (catalog gap versus misspelling
versus vocabulary miss) cannot decide between a supply fix, a query-
repair fix, and a retrieval-model fix. The zero-result rate earns its
place in the report only when it carries both the revenue shape and the
decision attached.

## Who owns the loop

- **The analytics team** owns the abandonment pricing and the
  zero-result cause taxonomy.
- **The data team** owns the follow-up session behavior the abandonment
  rate is measured from.
- **The product owner** owns the fix decision the causes imply — supply,
  query repair, or retrieval — and the budget that goes with it.

## Evidence boundary

The executed pricing over declared daily volume and abandonment rates
(illustrative, deterministic). It demonstrates the shape; real numbers
come from the query log and follow-up session behavior, and the
abandonment rate is measured, not assumed.

## Check your mental model

Answer each before opening it.

**1. Why is a zero-result a revenue story rather than a log detail?**

<details>
<summary>Answer</summary>

Because it sits at the top of the funnel with an abandonment cost. If
60% of users who see nothing leave, each zero-result query is a lost
session — and at 8% of daily volume that is thousands of users a day.
The metric's shape is demand lost before ranking ever runs.

</details>

**2. What does the rate add that NDCG and MRR do not cover?**

<details>
<summary>Answer</summary>

NDCG and MRR are conditional on having results to rank — they say
nothing about the queries that returned nothing. The zero-result rate
measures the uncovered part of the query space, and its breakdown (the
stage's table) says which fix each zero needs. The report needs both:
quality over the covered space, coverage of the rest.

</details>

## Next

Back to [stage 24](../), which completes the search report. The
[session detour](../when-the-click-is-a-query/) shows the metric's
other blind spot: per-query verdicts misread recovered sessions.
