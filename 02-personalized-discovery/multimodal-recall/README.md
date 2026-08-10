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

## How you find it: the modality-coverage audit, executed

The failure mode this stage prices is the single-modality item: an item
with one vector is reachable through one surface only, so a query of
the missing modality can never see it. The aggregate "reachable"
figure hides the defect, so the audit
([record](runs/2026-08-07-modality-coverage-audit.md)) stratifies a
20-item log by head and tail and reports coverage per surface:

| stratum | items | image | text | both | single |
|---|---|---:|---:|---:|---:|
| head | 10 | 100% | 100% | 100% | 0% |
| tail | 10 | 50% | 50% | 0% | 100% |

**Verdict:** SINGLE-MODALITY ITEMS ARE HALF-REACHABLE. The aggregate
reachable figure of 100% hides that image-only tail items are invisible
to text queries and text-only items to image queries — half the query
surfaces miss every tail item. **Decision:** report coverage per
modality, and for a single-modality item fall back to the modality it
has or synthesize the missing one (Radford et al. 2021; Liang et al.
2022).

<!-- interactive: MultimodalRecall -->

## The fix and its trade

The fix is per-modality coverage reporting plus a routing rule for
single-modality items: fall back to the modality the item has, or
synthesize the missing one so both query surfaces can reach it. The
executed audit prices the failure — the aggregate reachable figure of
100 percent hides that tail items carry image and text coverage of 50
percent each with zero items holding both, so image-only tail items are
invisible to text queries and text-only items to image queries, and
half the query surfaces miss every tail item.

The trade is that synthesis costs generation and risks the
reachable-but-not-retrievable failure: a synthesized vector puts the
item in the index without making the match good, and routing by the
available modality leaves one surface blind until the missing content
exists. The repair is therefore measured per surface — image and text
coverage reported separately, not one blended recall number — because
the aggregate figure is precisely what let the single-modality defect
live between the embedding, serving, and evaluation teams (Radford et
al. 2021; Liang et al. 2022).

## Who owns the loop

Three teams keep the cold-start loop working, and each owns a piece of
what breaks:

- **The content-embedding team** owns what a vector is worth. The
  [low-quality-content detour](when-the-content-vector-is-low-quality/)
  is theirs: a blurry image or auto-tag text produces a noisy embedding
  that is reachable but not retrievable, so they own the quality gate
  before embedding and the re-embed when the source improves.
- **The serving and indexing team** owns which queries can find which
  items. The [cold-image detour](when-the-image-is-cold/) is theirs: an
  interaction-free item is only as reachable as the modality it has, so
  they own per-item modality routing and the ANN index shape that
  either surface queries.
- **The evaluation and relevance team** owns the per-surface coverage
  report. The [modality-mismatch detour](when-the-modality-mismatch/)
  is theirs: a text query systematically ranks text-rich items above
  image-only ones even at equal relevance, so their metrics have to
  report image and text coverage separately, not one blended recall
  number.

The implicit-ownership consequence: when coverage is reported only in
the aggregate, no team is accountable for the tail items a query
surface silently misses — the embedding team ships vectors, the serving
team answers queries, and the evaluation team reads a 100% figure, so
the single-modality defect lives between all three.

## Why this belongs in the mission

The mission's recall rule is that downstream stages cannot repair what
was never retrieved. Cold start is where that rule bites hardest: the
items the system knows least about are the ones whose quality it must
guess. The VLM is the bridge — the frontier version of stage 01's
content understanding — and it decides which modalities an item can be
reached through, which the cold-image, modality-mismatch, and
low-quality-content detours price.

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

A third detour: [the low-quality content vector is reachable but not
retrievable](when-the-content-vector-is-low-quality/) — the executed
read: recall@3 drops from 8/8 for clean content to 2/4 for low-quality
content, and the displaced items lose to other categories' items.
