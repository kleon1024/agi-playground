---
status: verified
level: applied
base: scratch
label: When the zero-result rate matters
verified: 2026-08-08
---

# Zero results is a coverage metric with a revenue shape

**Question:** [stage 24's search measurement](../) reads the zero-result
rate. This chapter prices it and asks why it belongs in the report next
to NDCG and MRR. The pricing, measured over a real query log, is not one
number: 63.6% of zero-click queries end the session, but the split runs
against intuition — head queries abandon nine times out of ten while
most tail zero-clicks get a second attempt, and one in six zero-clicks
retries and still fails.

**Before this:** [stage 24 — search measurement](../) and its executed
zero-result model. The log is the same AOL 2006 read the
[session detour](../when-the-click-is-a-query/) executes; only
aggregates are reported.

## The cost, measured

The toy pricing ([record](runs/2026-08-07-zero-matters-read.md)) fixes
the shape on declared volume: 8% of queries return nothing and 60% of
those users leave. The real read
([record](../when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md))
replaces both assumptions with measured values over 21,876,184 queries:
10,204,807 (46.6%) produced no click, and the session verdict splits
them:

| zero-click outcome | queries | pct of zero-click | reading |
|---|---:|---:|---|
| recovered — reformulated, clicked | 2,026,678 | 19.9% | not lost at all |
| reformulated, still no click | 1,683,323 | 16.5% | retried and failed |
| abandoned — no reformulation | 6,494,805 | 63.6% | session ended |

The middle row is the revenue shape. 1.68 million queries over three
months — 7.7% of everything — are users who tried a second time and
still got nothing. That is demand the system saw twice and lost twice,
the strongest lost-user signal in the log. The abandoned row is larger
but ambiguous, and the distribution read shows why.

## The distribution read: abandonment is not uniform

Splitting the same zero-clicks by query frequency:

| stratum | traffic | zero-click | of zero-click recovered | of zero-click abandoned |
|---|---:|---:|---:|---:|
| head | 12.4% | 50.8% | 4.3% | 90.5% |
| body | 34.6% | 41.8% | 13.0% | 74.1% |
| tail | 53.0% | 48.8% | 27.5% | 51.3% |

Head zero-clicks abandon almost always: a user who typed `ebay`, saw
the page, and clicked nothing is not going to reformulate. The 90.5%
abandonment is mostly satisfied-without-click and direct navigation —
the log cannot tell which. Tail zero-clicks are the opposite: half of
them get a second query, and 27.5% recover into a clicked
reformulation. The tail is where a zero is a miss the user is actively
fixing; the head is where a zero is usually a completed task the log
cannot see.

## The fix and its trade

The fix is to report the zero-click rate as the three-way split —
recovered, reformulated-no-click, abandoned — sliced by stratum, with
the cause taxonomy (catalog gap versus misspelling versus vocabulary
miss) attached. The single "zero-result rate" is the same defect as the
single recovery rate: it hides the 19.9% that were never lost and the
16.5% that failed twice.

The trade, named: the measured read prices clicks, not results. AOL 2006
records queries and clicks, not what was rendered, so "zero-click" and
"zero-result" are not the same set — a query can render results and
still get no click. Production attribution closes that gap with
instrumented result-rendering and follow-up behavior (does the user
return later, or from another channel), which the 2006 log cannot
provide. The abandonment numbers also inherit the session definitions —
the 30-minute timeout and the 25-query attribution window — whose cost
the [session-definition detour](../when-the-session-definition-moves/)
owns.

## Who owns the loop

- **The analytics team** owns the three-way split and the cause
  taxonomy — which zero needs which fix.
- **The data team** owns the session-shaped log and the return-rate
  join — the follow-up behavior that separates satisfied-without-click
  from lost.
- **The product owner** owns the fix decision the causes imply —
  supply, query repair, or retrieval — and the budget that goes with it.
- **The search-quality team** owns the reformulated-no-click slice —
  the double failure that says the catalog, not the corrector or the
  ranker, is the bottleneck.

## Evidence boundary

The measured read is real: files 01–06 of the AOL 2006 user-ct
collection, 21,876,184 queries, analyzed with a deterministic stdlib
script ([record](../when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md)).
What it does not prove:

- The log is 2006 desktop web search — one engine's users. Abandonment
  rates are not transferable; production systems read their own log.
- Zero-click is not zero-result: no rendering information exists in this
  log, so the satisfied-without-click share of the abandoned row is
  unknowable here. That is exactly the instrumented follow-up a
  production system adds.
- Only aggregates are reported; no raw query is printed. Files 07–10 of
  the collection were rate-limited at download time and are not in this
  read.
- The split numbers inherit the session and attribution definitions;
  each is a documented choice that moves the numbers.

## Check your mental model

Answer each before opening it.

**1. Why is the reformulated-no-click slice the strongest lost-user
signal?**

<details>
<summary>Answer</summary>

Because it is a double failure: the user tried again and still got
nothing. Unlike the abandoned row, it cannot be explained by
satisfaction-without-click — a user who reformulates wants a result and
leaves empty-handed. 7.7% of all queries in the measured log took this
shape.

</details>

**2. Why does head abandonment not mean head loss?**

<details>
<summary>Answer</summary>

A head zero-click is usually a completed task: `ebay` with no click is
likely direct navigation or satisfaction without a click, not a failed
search. The log cannot tell which, so head abandonment is ambiguous —
the report should not price it as lost without the follow-up read.

</details>

**3. What does the stratum split add to the zero-click report?**

<details>
<summary>Answer</summary>

It shows where the fix lands. Tail zero-clicks are actively recovered
(27.5%) or abandoned in a way a fix might have prevented; head
zero-clicks are a measurement problem, not a retrieval problem. The
aggregate 63.6% describes neither.

</details>

## Next

Back to [stage 24](../), which completes the search report. The
[session detour](../when-the-click-is-a-query/) shows the metric's
other blind spot: per-query verdicts misread recovered sessions.
