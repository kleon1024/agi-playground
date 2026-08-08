---
status: verified
level: applied
base: scratch
label: When the typo is a real word
verified: 2026-08-07
---

# The misspelling that string correction cannot see

**Question:** [stage 19's query expansion](../) repairs queries by edit
distance. This chapter reads the executed case where the typo is itself
a valid catalog term — and asks what happens when distance-based
correction never fires.

**Before this:** [stage 19 — query expansion](../) and its executed
edit-distance model.

## The real-word error, executed

The run ([record](runs/2026-08-07-real-word-typo-read.md)) checks the
query `shorts` against a catalog that also contains `shoes`:

| check | result |
|---|---|
| is `shorts` a catalog term? | yes — no correction fires |
| nearest other term by edit distance | `shirts` (distance 1) |
| distance to the intended `shoes` | 2 — not even the nearest candidate |
| retrieval outcome | BM25 serves shorts to a user who wanted shoes |

## The reading

Every string-level corrector has this blind spot: a misspelling that is
itself a valid word is invisible to it, because the check "is this
token known?" passes. The distance to the intended word does not matter
— correction only runs when the token is unknown, and this token is
known. The evidence that the user meant `shoes` lives outside the
string: the click log (a `shorts` query that clicks shoe results) and
query co-occurrence. This is why production correction stacks log
evidence on top of distance. Hirst and Budanitsky ("Correcting
real-word spelling errors by restoring lexical cohesion", Natural
Language Engineering 11(1), 2005) formalize the same class — real-word
errors can only be detected from context, never from the lexicon.

The search-team version of the question is: does your zero-result rate
or your click-through actually catch this? A `shorts` query that
returns shorts results will look healthy on both — the failure is a
relevance miss that no funnel metric sees until a user types `shoes`
instead.

## The fix and its trade

The fix is to stack log evidence on top of edit distance — click logs and
query co-occurrence — because a real-word error is invisible to any
string-level repair. The executed check prices the failure: `shorts` is
a valid catalog term, so no correction fires; the nearest other term is
`shirts` (distance 1); the distance to the intended `shoes` is 2, not
even the nearest candidate; and BM25 serves shorts to a user who wanted
shoes. The check "is this token known?" passes, so the error never
reaches the corrector. Hirst and Budanitsky (2005) formalize the same
class: real-word errors can only be detected from context, never from
the lexicon.

The trade, named: a log-derived context model costs click data, privacy
surface, and a serving dependency — and the failure it catches is
otherwise invisible: a `shorts` query that returns shorts results looks
healthy on zero-result rate and click-through, so no funnel metric sees
the relevance miss until a user types `shoes` instead. The repair is
worth exactly the mis-serve volume the log evidence measures.

## Who owns the loop

- **The expansion team** owns the log-derived context model that detects
  real-word errors.
- **The data and logging team** owns the click and co-occurrence evidence
  the model reads, including its privacy boundary.
- **The relevance team** owns the mis-serve read — the funnel metrics
  that look healthy while a real-word miss ships are their blind spot
  to close.

## Evidence boundary

The executed membership-and-distance check over one query and one
catalog (illustrative, deterministic). It demonstrates why the error is
invisible to string repair; real real-word-error detection needs a
log-derived context model, which this chapter does not build.

## Check your mental model

Answer each before opening it.

**1. Why does edit distance fail on `shorts` for `shoes`?**

<details>
<summary>Answer</summary>

Because correction only runs on unknown tokens. `shorts` is in the
vendor's catalog, so the "is this a valid term?" check passes and the
distance computation is never reached. The error is invisible to any
string-level check — it is only detectable from context, which is what
log-based evidence supplies.

</details>

**2. What would make the system catch this typo?**

<details>
<summary>Answer</summary>

A context prior: click logs showing that `shorts` queries convert on
shoe pages, or co-occurrence statistics. With that evidence the system
can re-score the query even though every string check passes — the
correction becomes a decision about intent, not about spelling.

</details>

## Next

Back to [stage 19](../), where correction is measured by the recall it
recovers. The [expansion detour](../when-expansion-hurts/) shows the
precision cost of widening a query; this chapter showed the class of
error that widening cannot see at all.
