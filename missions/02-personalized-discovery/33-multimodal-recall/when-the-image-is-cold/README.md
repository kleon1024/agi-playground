---
status: verified
level: applied
base: scratch
label: When the image is cold
verified: 2026-08-07
---

# The cold image is reachable through one modality only

**Question:** [stage 33's multimodal recall](../) makes cold items
retrievable through content vectors. This chapter reads the executed
reachability check and asks which modality a cold image can be found
through.

**Before this:** [stage 33 — multimodal recall](../) and its executed
reachability model.

## The check, executed

The run ([record](runs/2026-08-07-image-is-cold-read.md)) tests an
image-only item with zero interactions:

| item | vectors | interactions | image query | text query |
|---|---|---:|---|---|
| item_c | image | 0 | True | False |

## The reading

The image vector makes the item reachable for image queries but not
text ones. The VLM closes one modality's gap and leaves the other — a
cold item is only as retrievable as its available content, per query
type. The practical consequence is that the recall design cannot assume
"cold items are retrievable"; it has to know per item which content
exists, because the answer changes by query type.

## Evidence boundary

The executed check over one declared item (illustrative, deterministic,
assumed vector presence). It demonstrates the mechanism; real recall
needs the embedding models and a measured recall@k per query type over
the cold catalogue.

## Check your mental model

Answer each before opening it.

**1. Why does the image vector not help text queries?**

<details>
<summary>Answer</summary>

Because matching happens in vector space: a text query is embedded and
matched against item vectors. The item has only an image vector, so a
text query has nothing of its own modality to match — unless the model
can map cross-modality, the image item is invisible to text retrieval.
The VLM produced the image vector; it did not produce a text
description for the item.

</details>

**2. What does the recall design need to know per item?**

<details>
<summary>Answer</summary>

Which content exists. The reachability matrix is per item and per query
type — an image-only item is reachable by image query, a text-only item
by text query, an item with neither by nothing. The design cannot claim
"cold items are retrievable" as one property; it has to carry the
modality set, which is exactly what the executed read shows item_c
needs.

</details>

## Next

Back to [stage 33](../). The
[modality-mismatch detour](../when-the-modality-mismatch/) shows the
competition cost when a text query faces an image-only item.
