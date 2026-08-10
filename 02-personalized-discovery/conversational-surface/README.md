---
status: verified
level: frontier
base: none
label: The conversational surface
verified: 2026-08-08
---

# When does the result page become a conversation?

**Question:** a search user types a query, gets nothing worth clicking, and
reformulates. The result page records that as two failed queries. When the
surface is a conversation, the same two turns are one recovered session — the
second turn is the point. This chapter asks what the session actually changes
as the unit of search, and what a conversational surface should optimize
instead of click rate.

**The artifact this chapter follows** is the per-query-versus-session verdict,
read from this mission's own AOL query-log run:

```text
per-query report counts 46.6% of queries as failures (zero clicks)
the session read reclassifies 19.9% of those as recovered sessions
```

By the end you will be able to say which part of the loop the conversational
surface actually repairs, and where its addressable gap sits.

**Before this:** [when-the-click-is-a-query](../../search/24-search-measurement/when-the-click-is-a-query/),
whose session-recovery read this chapter re-reads, and
[stage 36](../../search/36-conversational-search/), whose resolution audit
stratifies the same question by session length.

## The failure mode: the per-query report measures the wrong unit

The AOL read splits 21.9M queries by what happened after each one: clicked,
reformulated, or abandoned. On a per-query verdict, 46.6% are failures — no
click. But 19.9% of those zero-click queries had a reformulation that then
clicked. The user got what they wanted; the query-level report calls the
episode a failure twice.

The failure mode is not the reformulation — users always reformulated. It is
the measurement: a click-based report cannot see a session, so the loop
optimizes the wrong thing. Google's I/O 2026 announcement makes the stakes
explicit — AI Mode passed 1 billion monthly users and AI Overviews 2.5
billion, with the next user action moving from clicking a link to asking a
follow-up in the same thread
([developer keynote, 2026-05-19](https://developers.googleblog.com/all-the-news-from-the-google-io-2026-developer-keynote/);
[Antigravity, 2026-05-18](https://antigravity.google/blog/io-2026/)). When the
product's primary surface is a conversation, session recovery *is* the primary
engagement metric, not a diagnostic. The measurement unit is the session, and
the loop must be built to resolve within it.

## How you find the case

The recorded runs make the gap legible because they separate the verdict from
the unit. The query-log read reclassifies 19.9% of zero-click queries as
recovered, and splits recovery by query frequency:

| Stratum | Recovered | Reformulated, no click | Abandoned |
|---|---|---|---|
| head (>= 1000 occurrences) | 4.3% | 5.2% | 90.5% |
| body (10..999) | 13.0% | 12.9% | 74.1% |
| tail (< 10) | 27.5% | 21.2% | 51.3% |

Recovery concentrates in the tail — the long tail is where reformulation
happens, because head queries were already optimized and head users already
know the answer. The correction channel splits 23.2% near-edit typo fix versus
76.8% semantic reformulation, so the surface that repairs these sessions is
mostly meaning, not spelling.

The resolution audit adds the second leg: aggregate resolution of 0.680 is a
short-session artifact — sessions of 2–4 turns resolve at 0.980, sessions of
12–24 turns at 0.380. The tail where recovery concentrates is exactly where
resolution is hardest, because long sessions lose the first-turn grounding
that the follow-up needs. The addressable gap of a conversational surface is
the reformulated-but-unresolved share — 16.5% of zero-click queries — not the
click rate.

## The fix and its trade

The fix is to change the unit of measurement to the session, and to make the
loop repair within it: keep the thread, resolve follow-ups against the
first-turn grounding, and treat a recovered reformulation as success. The
trade is measurable in the same runs. The session read reclassifies 19.9% of
zero-click queries as recovered — that is the measurement gain, and it is
real. But the resolution audit shows the same unit exposes the failure the
click view hid: resolution falls from 0.980 (head sessions) to 0.380 (tail
sessions) because long conversations lose the referent. A conversational
surface that fixes the unit without fixing the grounding simply moves the
failure inside the session, where it is harder to see.

Two limits are structural. First, the reformulated-but-unresolved share (16.5%)
is the boundary of what a repair loop can reach: 4.5% of zero-click queries
had a near-edit fix offered and nothing clicked, and 75.6% had no repair
attempted at all — the surface can only recover sessions where the user kept
typing. Second, the fix changes what "good" means, which changes every
downstream decision: when the unit is the session, CTR is still measured but
is no longer the thing the loop optimizes, and the latency and cost budgets of
the loop grow because each turn may now call a model
([the survey's search section](../../../reference/research/agentic-paradigm-restructuring.md)).

<!-- interactive: SessionRecoveryLoop -->

## Who owns the loop

- **The measurement owner** owns the unit: the per-query report and the
  session report will disagree by design, and choosing the session changes
  what counts as a failure.
- **The retrieval owner** owns the tail: recovery concentrates where head
  optimization never reaches, and the tail is where the loop's repair budget
  should go.
- **The conversation owner** owns grounding: the resolution audit shows the
  referent is what long sessions lose, so pinning or compressing the first
  turns is a conversation-layer decision, not a ranking decision.

## Check your mental model

1. The query-level report counts 46.6% of queries as failures, and the
   session read reclassifies 19.9% of those as recovered. What does that
   reclassification actually change — the user's behavior or the loop's
   target?

<details>
<summary>Answer</summary>

It changes the loop's target. The user behaved the same way in both readings —
they reformulated and clicked. The per-query report called the episode two
failures because it measured clicks; the session report counts it as one
recovery because it measures resolution. The reclassification does not fix the
user's experience, it fixes what the loop optimizes, which is the precondition
for fixing the experience.

</details>

2. Recovery concentrates in the tail (27.5%) and resolution is hardest in the
   tail (0.380 vs 0.980). Why is that combination the surface's addressable
   gap rather than a contradiction?

<details>
<summary>Answer</summary>

The tail is where users reformulate most — head queries were already optimized
and head users already know the answer — so the tail is where the recovery
opportunity sits. Resolution is hardest there because long sessions lose the
first-turn grounding. The gap is the reformulated-but-unresolved share (16.5%):
users are already doing the repair work, and the surface fails to carry it
across turns. That is a loop defect the conversational surface can fix, unlike
the abandoned share where no repair was attempted.

</details>

## What this does not prove

**The session verdict is a definition choice, and it moves the numbers.** The
read uses a 30-minute timeout and a bounded 25-query attribution window; an
unbounded window attributes recoveries across a whole session and inflates
the recovered share. The 19.9% figure is the bounded definition, and a
different boundary changes it.

**The AOL corpus is 2006 web search.** The tail behavior and the
reformulation channels are a historical query log, not the conversational
surface it predicts; the correction-channel split (23.2% typo, 76.8%
semantic) is the distribution of a log that predates every current assistant.

**The resolution audit is a 10-session log.** The head/tail resolution split
(0.980 vs 0.380) is a mechanism demo on a tiny log, not a population
measurement; it shows the failure mechanism exists, not its real prevalence.
The AI Mode user counts are a dated 2026 snapshot from Google's own
announcement.

**Next:** [what replaces the score?](../../recommendation/35-verification-replaces-score/)
— the same loop, read from the ranking side: when generation replaces the
ranked list, which mechanisms survive and which failure moves.
