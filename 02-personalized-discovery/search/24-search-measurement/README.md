---
status: verified
level: applied
base: scratch
label: Search measurement
verified: 2026-08-07
---

# Every zero-result query is a decision

**Question:** [stage 13's NDCG and MRR](../13-search-evaluation/)
measured ranked quality over queries that returned results. This stage
asks about the queries that returned nothing, and answers: the
zero-result rate is a coverage signal whose breakdown says which fix
each zero needs.

**Before this:** [stage 13 — search evaluation](../13-search-evaluation/)
for the ranking metrics, and [stage 19 — query expansion](../19-query-expansion/)
for one of the fixes zeros need.

## The rate, executed

The run ([record](runs/2026-08-07-search-measurement.md)) reads four
queries against a small index:

| query | result | cause |
|---|---|---|
| headphones | zero | vocabulary miss — no such term in the index |
| wireless earbuds | zero | catalog gap — no earbuds in the catalogue |
| heaphones | zero | catalog gap — no misspelling correction |
| bluetooth speaker | 3 hits | normal result |

Zero-result rate: 75.0% (3/4).

## The mechanism, named

Every zero is a query the index cannot answer, and the breakdown decides
the fix. A catalog gap is a supply problem; a misspelling is a query-
repair problem; a vocabulary miss is a retrieval-model problem. The same
rate can hide three different failures, which is why the report needs
the causes, not just the number. The [zero-matters detour](when-the-zero-result-rate-matters/)
prices the rate through abandonment; the [session detour](when-the-click-is-a-query/)
shows why a per-query verdict can misread a recovered session.

## Why this belongs in the mission

Stage 13 measured how well ranked results satisfy queries that have
results. This stage completes the search report: the queries with no
results are where the funnel loses users before ranking ever matters —
the same logic as [stage 02's recall rule](../../shared/02-recall/), applied to
the search surface.

## Evidence boundary

The executed rate over four hand-built queries (illustrative,
deterministic). It demonstrates the breakdown; real zero-result
measurement needs the query log, the catalog, and a cause taxonomy
validated against what actually fixed each zero.

## Check your mental model

Answer each before opening it.

**1. Why is the rate not enough by itself?**

<details>
<summary>Answer</summary>

Because the same rate can hide different failures. A catalog gap, a
misspelling, and a vocabulary miss all produce zeros, and each needs a
different fix — more inventory, query repair, or a better retrieval
model. The breakdown is the decision; the rate is only its headline.

</details>

**2. What does the zero-result rate have to do with the funnel?**

<details>
<summary>Answer</summary>

It is a coverage metric at the top of the funnel: a query that returns
nothing loses the user before ranking ever runs. The
[zero-matters detour](when-the-zero-result-rate-matters/) prices it —
8% zeros with 60% abandonment is thousands of lost users a day — which
is why it belongs in the search report next to NDCG and MRR.

</details>

## Next

This closes the advanced search track (stages 19-24). The mission's
search surface now runs from raw query to measured outcome. Return to
[the mission README](../../) for the full path.

A detour from here: [a failed query can be a recovered
session](when-the-click-is-a-query/) — the executed session read: the
first query `heaphones` gets no click, the corrected `headphones` does,
so session metrics catch the recovery that per-query metrics call a
miss.

Another detour: [zero results is a coverage metric with a revenue
shape](when-the-zero-result-rate-matters/) — the executed pricing read:
8% of 100,000 daily queries return nothing and 60% of those users leave,
an estimated 4,800 lost users a day.
