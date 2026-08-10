---
status: verified
level: applied
base: scratch
label: When the session definition moves
verified: 2026-08-07
---

# One log, two funnels, two conclusions

**Question:** [stage 24's search measurement](../) reads the query log
and reports the funnel. This chapter reads the executed case where the
funnel numbers change with the session definition — and asks what a
funnel number means when two teams cannot agree on it.

**Before this:** [stage 24 — search measurement](../) and its executed
zero-result model.

## The segmentation, executed

The run ([record](runs/2026-08-07-session-definition-read.md)) segments
one six-event log two ways:

| definition | sessions | success | zero-result sessions | queries/session |
|---|---:|---:|---:|---:|
| 30-minute timeout | 2 | 100% | 0% | 3.0 |
| topic continuation | 5 | 40% | 60% | 1.2 |

## The reading

The 30-minute timeout merges four distinct topics into one session —
running shoes at minute 45, trail runners, headphones, gaming chair —
so the session reports 100% success and hides every failed query. The
topic splitter separates them and exposes 60% zero-result sessions.
Two teams with two definitions look at the same log and reach opposite
conclusions about whether search improved. Jones and Klinkner ("Beyond
the Session Timeout: Automatic Hierarchical Segmentation of Search
Topics in Query Logs", CIKM 2008, pages 699-708) is the reference for
why a fixed timeout is a weak proxy for the real boundary: search
topics span timeouts, and a timeout both merges distinct topics and
splits one topic across sessions.

The operational discipline is that the definition is part of the
measurement: it has to be owned, documented, and frozen before the
numbers mean anything. A funnel change between two months is only
interpretable if the segmentation did not change with it — the
offline-consistency version of the question is "is the metric stable
under the definition, or is the definition what moved?"

## The fix and its trade

The fix is to own, document, and freeze the session definition before
the numbers mean anything. The executed segmentation prices why: the
same six-event log segmented by a 30-minute timeout yields 2 sessions,
100% success, 0% zero-result sessions, and 3.0 queries per session,
while topic continuation yields 5 sessions, 40% success, 60%
zero-result sessions, and 1.2 queries per session — two teams with two
definitions reach opposite conclusions about whether search improved.
Jones and Klinkner (CIKM 2008) show a fixed timeout is a weak proxy for
the real boundary: search topics span timeouts, and a timeout both
merges distinct topics and splits one topic across sessions.

The trade, named: topic segmentation costs measured topic boundaries
over the production query log, and the alternative is a definition that
drifts with the calendar. The offline-consistency discipline is the
same as the rest of the mission: a funnel change between two months is
only interpretable if the segmentation did not change with it — the
question is whether the metric moved or the definition did.

## Who owns the loop

- **The analytics team** owns the session definition and its change
  control — a definition change is a metric change, not a bug fix.
- **The data team** owns production sessionization and the measured
  topic boundaries it is built on.
- **The product owner** owns the interpretation of month-over-month
  funnel changes, which is only valid under a frozen definition.

## Evidence boundary

The executed segmentation over one hand-built six-event log
(illustrative, deterministic). It demonstrates the definition
dependence; real sessionization runs over production query logs with
measured topic boundaries.

## Check your mental model

Answer each before opening it.

**1. How can the same log report 100% success and 40% success?**

<details>
<summary>Answer</summary>

Because success is defined per session and the session count depends on
the segmentation. The timeout merges every topic into two big sessions,
each containing a click — 100%. The topic splitter creates five
sessions, three of which contain only failed queries — 40%. The events
never change; the denominator does.

</details>

**2. What makes a funnel comparison between two months valid?**

<details>
<summary>Answer</summary>

A frozen, documented session definition. If the segmentation logic
changed — timeout length, topic matcher, session merge rules — the
numbers move even when user behavior is identical. The definition is
part of the measurement and has to be versioned like the code that
produces it.

</details>

## Next

Back to [stage 24](../), where the search track's outcome is measured.
The [click-as-query detour](../when-the-click-is-a-query/) covered the
recovery a session reveals; this chapter covered the boundary that
decides what counts as a session at all.
