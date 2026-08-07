---
status: verified
level: applied
base: scratch
label: When the correction helps
verified: 2026-08-07
---

# Correction recovers what the raw query could not

**Question:** [stage 19's query expansion](../) corrected a query, but
why bother — what does the correction actually buy? This chapter reads
the executed retrieval comparison and prices the correction in recall.

**Before this:** [stage 19 — query expansion](../) and its executed
edit-distance model.

## The recovery, executed

The run ([record](runs/2026-08-07-correction-helps-read.md)) retrieves
against the same index with the raw and the corrected query:

| query | document hits |
|---|---:|
| heaphones | 0 |
| headphones | 3 |

## The reading

The raw query retrieves nothing; the corrected query finds three
documents. The correction's value is exactly the recall it recovers — a
retrieval-side metric, not a query-side nicety. A correction that
produces a nicer string but no recovered documents has changed nothing,
which is why stage 19 measures correction at the index rather than at
the string.

## Evidence boundary

The executed comparison over one misspelling against one hand-built
index (illustrative, deterministic). It demonstrates the recovery; real
correction value is measured over the query log, where some
misspellings recover nothing because the catalog does not contain the
intended item at all.

## Check your mental model

Answer each before opening it.

**1. Why is the correction priced in document hits, not in the query
string?**

<details>
<summary>Answer</summary>

Because the system's job is retrieval. The corrected query is only
worth deploying if it finds documents the raw query lost — if it
retrieves the same set, the correction changed nothing observable.
Hits are the measurement; the string is the mechanism.

</details>

**2. What would a correction that recovers nothing tell you?**

<details>
<summary>Answer</summary>

That the misspelling is not the bottleneck. If the corrected term
retrieves nothing either, the catalog lacks the item or the index
cannot express the intent — the fix belongs elsewhere (inventory,
vocabulary, or a different retrieval path), not in more query repair.

</details>

## Next

Back to [stage 19](../), which corrects the query before retrieval. The
[expansion detour](../when-expansion-hurts/) shows the other side:
when repair adds wrong senses instead of recall.
