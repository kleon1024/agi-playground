---
status: verified
level: applied
base: scratch
label: When the click is a query
verified: 2026-08-08
---

# A failed query can be a recovered session

**Question:** [stage 24's search measurement](../) reads the query log.
This chapter asks whether a zero-click query is a failure or a step in a
recovery, and answers with a real log: across 21.9 million queries, the
per-query report calls nearly half of all queries failures, and the
session read reclassifies one in five of those as recovered — the user
reformulated, and the reformulation clicked. The recovery is not spread
evenly: tail queries recover at more than six times the head-query rate.

**Before this:** [stage 24 — search measurement](../) and its executed
zero-result model. The log analyzed here is the canonical public query
log — AOL 2006 ([Pass et al.](#evidence-boundary)) — standing in for a
private production log. The run reads only aggregates; no raw query from
it is printed anywhere in this chapter.

## The session, executed

The two-query session ([record](runs/2026-08-07-query-session-read.md))
fixes the mechanism in one row:

| query | outcome |
|---|---|
| heaphones | no click |
| headphones | click on d2 |

Judged alone, the first query is a failure; judged as a session, it is
the intent the second query satisfied — the reformulation is itself the
correction signal. This chapter measures how often that shape actually
happens: of the queries a per-query report counts as failures, how many
are recovered sessions?

## The recovery, measured

The run ([record](runs/2026-08-08-query-log-session-recovery.md)) reads
files 01–06 of the AOL 2006 collection: 21,876,184 queries from 394,411
users, split into 6,460,458 sessions by a 30-minute timeout
([Jones and Klinkner](#evidence-boundary) show the alternatives; the
session-definition detour owns their cost). Each query gets two verdicts:
the per-query verdict (clicked or not) and the session verdict (what
happened later in the session):

| verdict | queries | pct of all | pct of zero-click |
|---|---:|---:|---:|
| clicked | 11,671,377 | 53.4% | — |
| zero-click: recovered | 2,026,678 | 9.3% | 19.9% |
| zero-click: reformulated, no click | 1,683,323 | 7.7% | 16.5% |
| zero-click: abandoned | 6,494,805 | 29.7% | 63.6% |

The per-query report counts 46.6% of all queries as failures; the session
read reclassifies 19.9% of those as recovered — 2.0 million queries over
three months, roughly 22,000 per day, that a per-query-only report
certifies as lost. A per-query-only report measures the system at its
worst moment, before the user fixed the query for it.

## The distribution read: who recovers, and who never does

The aggregate recovery rate is real but coarse. Splitting the same log by
query frequency — head (at least 1,000 occurrences), body (10–999), tail
(fewer than 10) — changes the picture:

| stratum | queries | traffic | zero-click | of zero-click recovered | of zero-click abandoned |
|---|---:|---:|---:|---:|---:|
| head | 2,719,046 | 12.4% | 50.8% | 4.3% | 90.5% |
| body | 7,559,784 | 34.6% | 41.8% | 13.0% | 74.1% |
| tail | 11,597,353 | 53.0% | 48.8% | 27.5% | 51.3% |

The tail is where recovery lives. Tail queries are the ambiguous ones —
misspelled, underspecified, often with no good result — so the next
query carries the fix. Head queries recover almost never: a user who
typed `ebay` and clicked nothing is not about to reformulate; the query
was complete, and the zero click means something else (satisfaction
without a click, direct navigation — outcomes the log cannot see).

The lesson: a single recovery rate is the same defect as a single
zero-result rate. The tail is a small share of traffic and a large share
of the divergence — the hidden slice of the funnel audit, moved to the
search log.

## The correction channel: what recovers, and what never does

The recovery has two shapes, and the split prices stage 19's correction:

| channel | count | share |
|---|---:|---:|
| recovered via near-edit typo fix (edit distance at most 2) | 470,885 | 23.2% of recovered |
| recovered via semantic reformulation | 1,555,793 | 76.8% of recovered |
| fix offered, still nothing (a near-edit fix existed, none clicked) | 459,172 | 4.5% of zero-click |
| no repair attempted in session | 7,718,956 | 75.6% of zero-click |

A quarter of recovered sessions (23.2%) are recovered by a near-edit typo
fix — the `heaphones` to `headphones` shape at log scale. That is the
correction channel [stage 19](../../19-query-expansion/) prices: the
corrected query finds what the raw query lost. The other 76.8%
recovered by semantic reformulation, which no spelling corrector will
ever produce. The third row is the boundary the correction detour names:
a near-edit fix was attempted and still nothing clicked — not because
the corrector was wrong, but because the catalog lacks the intended item.

## The fix and its trade

The fix is to report both verdicts — per-query funnel for the mechanics,
session recovery rate for the outcome — each sliced by stratum and
channel.

The trade, named: session metrics cost a session boundary, an attribution
rule, and a log that can join a click back to the reformulation that
produced it. The boundary is a choice with real consequences — the
session-definition detour shows the same log reporting 100% success under
one definition and 40% under another. The attribution rule here (a
zero-click query is recovered when a clicked reformulation follows within
25 queries) is first-match and deliberately bounded: recovery is a local
event, and production systems argue over whether the reformulation
credits the earlier query at all. The pipeline cost is real — per-query
verdicts are one log line each; session verdicts need user ID, timestamp,
and ordering intact. The per-query-only alternative is simpler and
systematically pessimistic on the recovered sessions measurement should
reward — and it throws away the reformulation signal [stage 19's
correction](../../19-query-expansion/) is learned from.

## Who owns the loop

- **The analytics team** owns the session metric and its attribution
  rule — which later query recovers which earlier query.
- **The product owner** owns the session definition — a 30-minute timeout
  and a topic-continuation rule are different products, and it must be
  frozen before the numbers mean anything.
- **The data team** owns the session-shaped log — the user ID, timestamp,
  and ordering that make the recovery join possible.
- **The search-quality team** owns the correction channel read — the
  share of recoveries a spell fix could have produced, and the
  fix-offered-still-nothing slice that says the catalog, not the
  corrector, is the bottleneck.

## Evidence boundary

The measured read is real: files 01–06 of the AOL 2006 user-ct
collection, 21,876,184 queries from 394,411 users, downloaded 2026-08-08
from the archive.org mirror, analyzed with a deterministic stdlib script
([core](core/session_recovery.py), [record](runs/2026-08-08-query-log-session-recovery.md)).
What it does not prove:

- The log is 2006 web search — desktop-era, pre-mobile, one engine's
  users. Recovery rates and the head/tail split are not transferable
  numbers; production systems must read their own private log.
- Only aggregates are reported; raw queries are never printed. The
  collection is a public research corpus but contains real users'
  searches, and the chapter treats it as a private log.
- The definitions are choices — the 30-minute session timeout, the
  reformulation heuristic (shared token or edit distance at most 2), the
  bounded 25-query attribution window, and first-match attribution — and
  each moves the numbers.
- Files 07–10 were rate-limited at download time on 2026-08-08 and are
  not in this read; the full collection is roughly 36M queries.

Citations verified 2026-08-08 (full DOIs in the run record): Pass,
Chowdhury, and Torgeson, "A Picture of Search", InfoScale 2006; Jones
and Klinkner, "Beyond the Session Timeout", CIKM 2008; Huang and
Efthimiadis, "Analyzing and Evaluating Query Reformulation Strategies in
Web Search Logs", CIKM 2009; Radlinski and Joachims, "Query Chains", KDD
2005.

## Check your mental model

Answer each before opening it.

**1. Why is a zero-click query not simply a miss?**

<details>
<summary>Answer</summary>

Because the session may continue and succeed. The user's intent is
stable; the first query failed to express it and the second succeeded.
About one in five zero-click queries is followed by a reformulation that
clicks, far more in the tail than the head. Per-query measurement counts
the first as a failure — but recovery is a property of the session, and
the system's job includes surviving the misspelling.

</details>

**2. What does the head-versus-tail split tell you about the report?**

<details>
<summary>Answer</summary>

A single recovery rate hides where recovery happens. Head queries
almost never recover — their zero clicks mean something other than a
failed expression — while tail queries recover a large share of the time.
The aggregate sits between the two and describes neither; the report has
to carry the split.

</details>

**3. What does the correction channel read add to the recovery rate?**

<details>
<summary>Answer</summary>

It says which recoveries a fix could have produced. A share of recovered
sessions are recovered by a near-edit typo fix — that is stage 19's
correction channel, priced in recovered recall. A larger share recovered
by semantic reformulation, which no corrector produces. A smaller slice
had a near-edit fix attempted and never clicked — the correction was
right and there was nothing to find, which moves the fix to the catalog,
not the corrector.

</details>

## Next

Back to [stage 24](../) and the search funnel. The
[session-definition detour](../when-the-session-definition-moves/) shows
how much the numbers above depend on where a session ends. The
[zero-matters detour](../when-the-zero-result-rate-matters/) prices the
queries that never recover. And [when the correction helps](../../19-query-expansion/when-the-correction-helps/)
owns the channel this chapter measures: correction value is the recall it
recovers, now over a real log.
