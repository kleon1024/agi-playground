---
status: verified
level: applied
base: scratch
label: Multimodal recall
verified: 2026-08-07
---

# Content vectors make the cold item reachable

**Question:** stage 02's recall ran on interaction logs, which makes
never-clicked items unreachable. This stage asks what content can do
about cold start and answers: image and text embeddings produced by a
VLM make the item retrievable before it has any interactions.

**Before this:** [stage 02 — recall](../../shared/02-recall/) for the queue
structure and the cold-tail detour, and [stage 01 — content
understanding](../../shared/01-content-understanding/) for the VLM that produces
the vectors.

## The reachability, executed

The run ([record](runs/2026-08-07-multimodal-recall.md)) checks five
items:

| item | vectors | warm/cold | reachable |
|---|---|---|---|
| a | image, text | warm | yes |
| b | image | warm | yes |
| c | image, text | cold | yes |
| d | text | cold | yes |
| e | none | cold | no |

Cold items retrievable: 2/3.

## The mechanism, named

An item is retrievable when a query vector can match it. Interaction
logs cannot produce a query-side match for an item nobody interacted
with — but content can: the VLM embeds the image, the text embedder
embeds the description, and either vector gives the cold item a place
in the index. Item e has neither, so it stays unreachable: a cold item
is only as retrievable as its available content.

## Why this belongs in the mission

The mission's recall rule is that downstream stages cannot repair what
was never retrieved. Cold start is where that rule bites hardest: the
items the system knows least about are the ones whose quality it must
guess. The VLM is the bridge — the frontier version of stage 01's
content understanding — and it decides which modalities an item can be
reached through, which the cold-image and modality-mismatch detours
price.

## Evidence boundary

The executed reachability check over five declared items (illustrative,
deterministic, assumed vector presence). It demonstrates the mechanism;
real recall needs the embedding models, the ANN index, and a measured
recall@k over held-out interactions.

## Check your mental model

Answer each before opening it.

**1. Why does content beat interaction data for cold items?**

<details>
<summary>Answer</summary>

Because interaction data is empty for an item nobody has touched — there
is nothing to learn from. Content is available the moment the item
enters the catalogue: the image and the description exist before the
first click. Embeddings of that content put the item in the index, so
it can be retrieved and eventually earn the interactions that a warm
model uses.

</details>

**2. What decides which modality can reach a cold item?**

<details>
<summary>Answer</summary>

The content the item actually has. An image-only item is reachable by
image queries but not text ones; a text-only item is the reverse; an
item with neither has no vector and stays unreachable (item e). The VLM
closes one modality's gap and leaves the other, so the recall design has
to know per item which content exists.

</details>

## Next

The frontier recommendation track continues. Next is [stage 34 — slate
versus item evaluation](../34-slate-vs-item-evaluation/), where the
metric must see the page the user actually got.

A detour from here: [the image is cold and only one modality can
reach it](when-the-image-is-cold/) — the executed read: the image
vector makes an interaction-free item retrievable by image query but
not by text query.

Another detour: [the modality mismatch biases recall toward
text-rich items](when-the-modality-mismatch/) — the executed read: the
image-only item scores 0.60 through the cross-modal gap against 0.82
for the text item, even when the image is relevant.
