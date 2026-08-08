---
status: verified
level: applied
base: scratch
label: When the correction helps
verified: 2026-08-08
---

# Correction recovers what the raw query could not

**Question:** [stage 19's query expansion](../) corrected a query, but
why bother — what does the correction actually buy? This chapter prices
the correction in recall, first over one misspelling against one index,
then over a real query log where the correction channel is measured:
23.2% of recovered sessions recover through a near-edit typo fix, and
4.5% of zero-click queries had such a fix in reach and still recovered
nothing.

**Before this:** [stage 19 — query expansion](../) and its executed
edit-distance model. The log read is the AOL 2006 session read the
[session detour](../../24-search-measurement/when-the-click-is-a-query/)
executes; only aggregates are reported.

## The recovery, executed

The run ([record](runs/2026-08-07-correction-helps-read.md)) retrieves
against the same index with the raw and the corrected query:

| query | document hits |
|---|---:|
| heaphones | 0 |
| headphones | 3 |

The raw query retrieves nothing; the corrected query finds three
documents. The correction's value is exactly the recall it recovers — a
retrieval-side metric, not a query-side nicety. A correction that
produces a nicer string but no recovered documents has changed nothing,
which is why stage 19 measures correction at the index rather than at
the string.

## The correction channel, measured

The one-row demo fixes the mechanism; the real read prices the channel.
The session-recovery run
([record](../../24-search-measurement/when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md))
classifies 21,876,184 queries into sessions and asks how zero-click
queries recover:

| channel | queries | share |
|---|---:|---:|
| recovered via near-edit typo fix (edit distance at most 2) | 470,885 | 23.2% of recovered |
| recovered via semantic reformulation | 1,555,793 | 76.8% of recovered |
| fix in reach, still nothing (a near-edit reformulation existed, none clicked) | 459,172 | 4.5% of zero-click |
| no repair attempted in session | 7,718,956 | 75.6% of zero-click |

About one in five zero-click queries recovers in-session (19.9%), and
of those recovered sessions 23.2% recover through a near-edit typo fix —
the `heaphones` to `headphones` shape at log scale. That is the channel
this stage's correction produces: 470,885 recoveries over three months,
roughly 5,200 per day, that the corrector earns. The other 76.8% recover
through semantic reformulation — different words, same intent — which no
spelling corrector will ever produce; that recovery belongs to the
expansion side of stage 19, not the typo fixer.

The third row is the boundary: 459,172 zero-click queries (4.5%) where
the session contains a near-edit reformulation and still nothing
clicked. The correction was right and there was nothing to find — the
catalog does not contain the intended item. Correction value is not just
what the fix recovers; it is bounded by what the catalog holds.

## The fix and its trade

The fix is to price correction twice: at the index (the toy's document
hits, the mechanism demo) and at the recovery channel (the log's
recovered sessions, the production read). A correction ships only when
the index read shows recovered documents, and its measured value is the
log's recovered-recall share.

The trade, named: the channel read costs the whole session apparatus the
session detour owns — session boundary, attribution window, and a log
with user ID and ordering intact. It also costs a definition:
"near-edit" here is edit distance at most 2 (the Huang and Efthimiadis
reformulation heuristic), and the recovered share moves with the band.
The toy read needs none of that; it also measures nothing about how
often the shape occurs. And the boundary read requires regenerating the
correction candidates from the log after the fact, which a production
correction pipeline can do and a static corpus cannot.

## Who owns the loop

- **The expansion team** owns the correction candidates and the language
  prior that picks among near-distance terms.
- **The retrieval team** owns the index-side recovery read — the
  document hits the corrected query recovers against the declared
  relevance bar.
- **The data team** owns the session-shaped log where the channel is
  measured, plus the candidate regeneration the boundary read needs.
- **The search-quality team** owns the fix-in-reach-still-nothing slice
  — when it grows, the bottleneck is the catalog, not the corrector.

## Evidence boundary

Two reads, honestly separated. The index read
([record](runs/2026-08-07-correction-helps-read.md)) is one misspelling
against one hand-built index — illustrative, deterministic, a mechanism
demo. The channel read is real: files 01–06 of the AOL 2006 user-ct
collection, 21,876,184 queries, a deterministic stdlib script,
aggregates only. What it does not prove:

- The log is 2006 desktop web search; the recovered shares are not
  transferable numbers.
- "Near-edit" is the edit-distance-2 band; other bands move the shares.
- Files 07–10 of the collection were rate-limited at download time and
  are not in the read.
- The candidate read is a proxy: it treats any near-edit reformulation
  in the session as a candidate the corrector could have offered.
  Production systems measure the corrector's actual candidate set.

## Check your mental model

Answer each before opening it.

**1. Why is the correction priced in recovered recall, not in the query
string?**

<details>
<summary>Answer</summary>

Because the system's job is retrieval. The corrected query is only worth
deploying if it finds documents the raw query lost — if it retrieves the
same set, the correction changed nothing observable. Over the measured
log, 23.2% of recovered sessions recover through a near-edit typo fix;
that is the recall the correction channel earns.

</details>

**2. What does fix-in-reach-still-nothing tell you?**

<details>
<summary>Answer</summary>

That the misspelling is not the bottleneck. The user produced a near-edit
query, the session had a correction candidate, and nothing clicked
anyway — the catalog lacks the item or the index cannot express the
intent. Measured: 4.5% of zero-click queries in the log. The fix belongs
in inventory or a different retrieval path, not in more query repair.

</details>

## Next

Back to [stage 19](../), which corrects the query before retrieval. The
[expansion detour](../when-expansion-hurts/) shows the other side: when
repair adds wrong senses instead of recall.
