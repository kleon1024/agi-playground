# Run: 24 — session recovery over the AOL 2006 query log

**Date:** 2026-08-08
**Command:** `uv run python core/session_recovery.py <aol-collection-dir>`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** about 7 minutes (two passes over 21.9M rows).
**Cost:** \$0 (local lane).

## Purpose

Measure, on a real query log, how many zero-click queries are recovered
sessions: the user reformulated and the reformulation clicked. The
per-query verdict (clicked or not) is the report that counts zero-click
queries as failures; the session verdict reclassifies a share of them as
recovered. The read also splits recovery by query frequency (head / body /
tail) and by channel (near-edit typo fix versus semantic reformulation).

## Data

Files 01-06 of the AOL 2006 user-ct collection (Pass, Chowdhury, and
Torgeson, InfoScale 2006): 21,876,184 queries from 394,411 users,
downloaded 2026-08-08 from the archive.org mirror of the canonical
collection (`aolsearchdata2006`, files verified by gzip integrity check).
Files 07-10 of the ten-file collection were rate-limited at download time
and are not in this read. Only aggregates are reported; no raw query is
emitted.

Definitions, fixed before the run:

- session: consecutive queries of one user separated by at most 30
  minutes (Jones and Klinkner, CIKM 2008, on session segmentation);
- reformulation: a later query that shares a token with the earlier
  query, or is within edit distance 2 of it (the reformulation
  heuristics Huang and Efthimiadis, CIKM 2009, classify);
- recovered: a zero-click query with a clicked reformulation within the
  next 25 queries of the same session (bounded attribution window:
  recovery is treated as a local event);
- abandoned: a zero-click query with no reformulation within the window.

## Output

```
== 1. the corpus, read ==
files 6 of user-ct-test-collection-01..10 | lines 21,876,184
queries 21,876,184 | clicks 11,671,377 | zero-click 10,204,807 | malformed 0
unique normalized queries 6,424,220 | head >= 1000 | body 10..999 | tail < 10

== 2. the session read: per-query verdict vs session verdict ==
queries classified 21,876,183 | sessions 6,460,458 | 30-min timeout | unsorted rows 31

verdict                      queries  pct of all pct of zero-click
clicked                   11,671,377       53.4%               n/a
zero-click: recovered      2,026,678        9.3%             19.9%
zero-click: reformulated, no click   1,683,323        7.7%             16.5%
zero-click: abandoned      6,494,805       29.7%             63.6%

per-query report counts 46.6% of queries as failures (zero clicks); the session read reclassifies 19.9% of those as recovered sessions

== 3. the distribution read: recovery by query frequency ==
stratum        queries   traffic  zero-click of zero-click recovered of zero-click abandoned
head         2,719,046     12.4%       50.8%                    4.3%                   90.5%
body         7,559,784     34.6%       41.8%                   13.0%                   74.1%
tail        11,597,353     53.0%       48.8%                   27.5%                   51.3%

== 4. the correction channel: what recovers, and what never does ==
recovered via near-edit typo fix (edit distance <= 2): 470,885 ( 23.2% of recovered)
recovered via semantic reformulation: 1,555,793 ( 76.8% of recovered)
fix offered, still nothing (a near-edit reformulation existed in the session, none clicked): 459,172 (  4.5% of zero-click)
no repair attempted in session: 7,718,956 ( 75.6% of zero-click)
(a query whose recovering reformulation is a near-edit fix is the stage-19 correction channel; a semantic reformulation is not)

== verdict ==
RECOVERED SESSION: the per-query failure rate overstates loss; the session read reclassifies 19.9% of zero-click queries as recovered sessions.
```

## Notes

- The bounded 25-query attribution window is a definition choice; an
  unbounded "any later query in the session" scan makes the read
  quadratic on pathological long sessions and attributes recoveries
  across a whole 30-minute window.
- Citations verified 2026-08-08: Pass, Chowdhury, and Torgeson, "A
  Picture of Search", InfoScale 2006, DOI 10.1145/1146847.1146848; Jones
  and Klinkner, "Beyond the Session Timeout", CIKM 2008, DOI
  10.1145/1458082.1458176; Huang and Efthimiadis, "Analyzing and
  Evaluating Query Reformulation Strategies in Web Search Logs", CIKM
  2009, DOI 10.1145/1645953.1645966; Radlinski and Joachims, "Query
  Chains", KDD 2005, DOI 10.1145/1081870.1081899.
