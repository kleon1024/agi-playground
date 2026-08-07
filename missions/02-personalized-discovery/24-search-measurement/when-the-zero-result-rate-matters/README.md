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
