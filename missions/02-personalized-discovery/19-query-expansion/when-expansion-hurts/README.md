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
