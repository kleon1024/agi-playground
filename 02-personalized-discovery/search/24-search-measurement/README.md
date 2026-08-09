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

<!-- interactive: SearchMeasurement -->

## The mechanism, named

Every zero is a query the index cannot answer, and the breakdown decides
the fix. A catalog gap is a supply problem; a misspelling is a query-
repair problem; a vocabulary miss is a retrieval-model problem. The same
rate can hide three different failures, which is why the report needs
the causes, not just the number. The [zero-matters detour](when-the-zero-result-rate-matters/)
prices the rate through abandonment; the [session detour](when-the-click-is-a-query/)
shows why a per-query verdict can misread a recovered session.

## How you find it: the funnel audit, executed

The funnel is reported as an aggregate, and the failure mode the
aggregate hides is the slice that collapses while the mean stays flat.
The run ([record](runs/2026-08-07-measure-audit.md)) emits the search
funnel over four slices — device crossed with query stratum:

| slice | queries | zero | click | conversion |
|---|---:|---:|---:|---:|
| desktop-head | 10,000 | 2% | 45% | 2.00% |
| desktop-tail | 2,000 | 8% | 38% | 1.50% |
| mobile-head | 12,000 | 4% | 40% | 1.80% |
| mobile-tail | 3,000 | 25% | 22% | 0.20% |

The verdict is HIDDEN SLICE: the aggregate (1.67% conversion, 5.9%
zero) looks normal while mobile-tail — 11% of traffic — converts at
0.20% with a 25% zero-result rate. The slice barely moves the mean,
which is exactly why the mean cannot be the report: a failing slice
that is a small traffic fraction is invisible in the aggregate and
incident-sized in its own row. The decision that follows: report the
funnel per slice, and treat a slice whose rate is a third of the
aggregate as an incident, not a rounding error.

## The fix and its trade

The fix is to report the funnel per slice and to break every zero-result
query into its cause — catalog gap, misspelling, or vocabulary miss —
because the same rate hides three different failures with three
different fixes. The executed audit prices the failure the fix removes:
the aggregate (1.67% conversion, 5.9% zero) looks normal while
mobile-tail — 11% of traffic — converts at 0.20% with a 25% zero-result
rate; the slice barely moves the mean, which is exactly why the mean
cannot be the report. The zero-rate breakdown is equally structural: of
four queries, one is a vocabulary miss ("headphones" — no such term in
the index), two are catalog gaps (no earbuds in the catalogue; no
misspelling correction for "heaphones"), and one is normal.

The trade, named: per-slice reporting costs slice attributes on every
log line, and the cause taxonomy costs validation against what actually
fixed each zero — and the alternative is an aggregate that certifies a
failing slice as "the funnel is flat." A slice whose rate is a third of
the aggregate is an incident, not a rounding error, and a zero-result
rate without its causes is a headline with no decision attached.

## Who owns the loop

The funnel is the search surface's outcome; someone must own what the
numbers mean, and the handoffs are where measurement fails:

- **The measurement or analytics team** owns the funnel itself: the
  per-slice report, the cause taxonomy for zeros, and the session
  definition that the numbers depend on. It owns the metric, and the
  when-the-session-definition-moves detour is its failure mode.
- **The product or search owner** owns the decision the funnel feeds:
  which slice gets the fix, whether mobile-tail is a supply problem or
  a query problem, and what "improved" means this quarter. It owns the
  verdict, and the audit's HIDDEN SLICE result is its signal.
- **The data or logging team** owns the raw material: the query log,
  the session boundary, and the slice attributes that make the funnel
  auditable at all. It owns the data, and the
  when-the-zero-result-rate-matters detour is its pricing.

When the ownership is implicit, the analytics team reports an
aggregate, the product owner reads the headline, and nobody owns the
slice — so a mobile-tail collapse ships as "the funnel is flat" until
the slice gets reported.

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

And a third: [one log, two funnels, two conclusions](when-the-session-definition-moves/) — the same six-event log reports 100% success
under a 30-minute timeout and 40% under topic continuation, so the
definition has to be frozen before the numbers mean anything.
