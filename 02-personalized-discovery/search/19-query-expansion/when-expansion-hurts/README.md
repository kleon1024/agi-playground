---
status: verified
level: applied
base: scratch
label: When expansion hurts
verified: 2026-08-08
---

# Expansion trades precision for recall

**Question:** [stage 19's query expansion](../) repairs and expands
queries. This chapter reads the executed ambiguity case and asks what
expansion costs when the term has more than one sense — then measures
the same risk over a real query log, where on the rare queries expansion
targets most, one in five zero-clicks reformulates and still fails.

**Before this:** [stage 19 — query expansion](../) and its executed
edit-distance model. The log read is the AOL 2006 session read the
[session detour](../../24-search-measurement/when-the-click-is-a-query/)
executes; only aggregates are reported.

## The ambiguity, executed

The run ([record](runs/2026-08-07-expansion-hurts-read.md)) expands the
ambiguous query `apple`:

| query | hits | relevant |
|---|---|---|
| base `apple` | 4 | all four relevant |
| expanded | 4 | includes the wrong senses |
| new hits from expansion | 0 | — |

The toy demonstrates the mechanism: expansion traded precision for
recall and lost on both. The base query's four hits are all relevant;
the expanded query still returns four but now includes phone and laptop
documents — `apple` means phone in one context and fruit in another,
and the ambiguity is the cost. No new relevant hits were added, so the
widen bought nothing but noise.

## The risk, measured

The toy fixes the mechanism; the real read prices how often the risk
lands. Expansion fires most on rare queries — they need the repair
most — and the tail is exactly where the log shows the failure
boundary. The session-recovery run
([record](../../24-search-measurement/when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md))
splits zero-click outcomes by query frequency over 21,876,184 queries:

| stratum | traffic | of zero-click recovered | of zero-click reformulated, no click | of zero-click abandoned |
|---|---:|---:|---:|---:|
| head | 12.4% | 4.3% | 5.2% | 90.5% |
| body | 34.6% | 13.0% | 12.9% | 74.1% |
| tail | 53.0% | 27.5% | 21.2% | 51.3% |

On the tail, 27.5% of zero-clicks recover through a reformulation —
that is expansion's realistic upside, the recall the repair can earn.
But 21.2% reformulate and still fail: the user did the equivalent of
expanding the query and nothing helped. That slice is the measured
price of expansion's risk on exactly the queries it targets — repair
attempted, wrong senses or an empty catalog, still nothing clicked. The
channel read adds the split: 76.8% of recoveries are semantic
reformulations, which is the expansion side's business; only 23.2% are
near-edit typo fixes, which [the correction detour](../when-the-correction-helps/)
owns.

## The fix and its trade

The fix is a sense signal before the query is widened — expansion must
know which meaning the user intended — measured as added relevant recall
against added irrelevant retrieval. The toy read shows why: with recall
already complete, expansion can only add wrong senses. The log read
bounds the opportunity: even a perfect sense model cannot recover more
than the 27.5% of tail zero-clicks that actually recover; the 51.3% that
never reformulate are not expansion's to fix, and the 21.2% that
reformulate and fail are a catalog or retrieval problem, not a query
problem.

The trade, named: a sense model costs context signals the string does
not carry — click evidence and query co-occurrence — and adds a model
and a serving dependency to the expansion path. The alternative,
expanding without a sense signal, widens every ambiguous term and lets
the index outrank noise it was never meant to see. The log's own numbers
are the guardrail: if the reformulated-no-click share of the tail grows,
expansion is adding wrong senses faster than it recovers recall, and the
gate should tighten.

## Who owns the loop

- **The expansion team** owns the sense model and the gate that stops an
  ambiguous term from widening.
- **The retrieval team** owns the noise the widened query introduces and
  the outranking cost it imposes on the index.
- **The data and logging team** owns the click and co-occurrence evidence
  the sense signal is derived from.
- **The search-quality team** owns the reformulated-no-click read — the
  slice that says the fix belongs in the catalog or retrieval, not in
  wider queries.

## Evidence boundary

Two reads, honestly separated. The index read
([record](runs/2026-08-07-expansion-hurts-read.md)) is one ambiguous
term against one hand-built index — illustrative, deterministic, a
mechanism demo; it demonstrates the precision risk, not its frequency.
The log read is real: files 01–06 of the AOL 2006 user-ct collection,
21,876,184 queries, a deterministic stdlib script, aggregates only. What
it does not prove:

- The log has no relevance judgments; the reformulated-no-click share is
  a behavioral proxy for expansion failure, not a precision measurement.
  Production systems measure added relevant recall against added
  irrelevant retrieval on their own log.
- The log is 2006 desktop web search; the stratum shares are not
  transferable numbers.
- Files 07–10 of the collection were rate-limited at download time and
  are not in the read.
- The channel definitions (edit-distance-2 near-edit, 25-query
  attribution window) are documented choices that move the shares.

## Check your mental model

Answer each before opening it.

**1. Why did expansion add no relevant hits here?**

<details>
<summary>Answer</summary>

Because the base query already retrieved the relevant documents, and
the expansion only added documents for the other sense of `apple`. When
recall is already complete, expansion has nothing to recover — it can
only add noise, which is a pure precision loss.

</details>

**2. What does the tail's reformulated-no-click slice tell you about
expansion risk?**

<details>
<summary>Answer</summary>

That on the queries expansion targets most, repair fails even when
attempted — 21.2% of tail zero-clicks reformulate and still get
nothing. The user performed the expansion and it did not help, so the
bottleneck is what is retrievable (catalog, sense, inventory), not the
query widening. When this slice grows, widen less.

</details>

**3. What would make expansion safe for an ambiguous term?**

<details>
<summary>Answer</summary>

A sense signal: evidence about which meaning the user intends, such as
their history or the query's context. Stage 23's personalization is
exactly such a prior. Without it, expansion widens every sense
indiscriminately and lets the wrong documents in.

</details>

## Next

Back to [stage 19](../), where correction is measured by the recall it
recovers. The [correction detour](../when-the-correction-helps/) shows
the side where repair does recover recall.
