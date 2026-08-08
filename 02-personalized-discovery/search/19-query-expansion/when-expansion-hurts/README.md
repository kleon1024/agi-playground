---
status: verified
level: applied
base: scratch
label: When expansion hurts
verified: 2026-08-07
---

# Expansion trades precision for recall

**Question:** [stage 19's query expansion](../) repairs and expands
queries. This chapter reads the executed ambiguity case and asks what
expansion costs when the term has more than one sense.

**Before this:** [stage 19 — query expansion](../) and its executed
edit-distance model.

## The ambiguity, executed

The run ([record](runs/2026-08-07-expansion-hurts-read.md)) expands the
ambiguous query `apple`:

| query | hits | relevant |
|---|---|---|
| base `apple` | 4 | all four relevant |
| expanded | 4 | includes the wrong senses |
| new hits from expansion | 0 | — |

## The reading

Expansion traded precision for recall and lost on both: the base query's
four hits are all relevant, the expanded query still returns four but
now includes phone and laptop documents — `apple` means phone in one
context and fruit in another, and the ambiguity is the cost. No new
relevant hits were added. Expansion needs a sense signal to know which
meaning the user intended before it widens the query.

## The fix and its trade

The fix is a sense signal before the query is widened — expansion must
know which meaning the user intended — measured as added relevant recall
against added irrelevant retrieval. The executed ambiguity prices the
failure: the base query `apple` returns 4 hits, all relevant; expansion
still returns 4 but now includes the wrong senses (phone and laptop
documents), and zero new relevant hits were added. Expansion traded
precision for recall and lost on both: `apple` means phone in one
context and fruit in another, and the ambiguity is the cost.

The trade, named: a sense model costs context signals the string does not
carry — click evidence and query co-occurrence — and adds a model and a
serving dependency to the expansion path. The alternative, expanding
without a sense signal, widens every ambiguous term and lets the index
outrank noise it was never meant to see. Real expansion systems measure
the added relevant recall against the added irrelevant retrieval over
the query log before shipping a term-sense model.

## Who owns the loop

- **The expansion team** owns the sense model and the gate that stops an
  ambiguous term from widening.
- **The retrieval team** owns the noise the widened query introduces and
  the outranking cost it imposes on the index.
- **The data and logging team** owns the click and co-occurrence evidence
  the sense signal is derived from.

## Evidence boundary

The executed comparison over one ambiguous term (illustrative,
deterministic). It demonstrates the precision risk; real expansion
systems measure added relevant recall against added irrelevant
retrieval over the query log before shipping a term-sense model.

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

**2. What would make expansion safe for an ambiguous term?**

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
