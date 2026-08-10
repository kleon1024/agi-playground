---
status: verified
level: applied
base: scratch
label: When the content vector is low quality
verified: 2026-08-07
---

# The low-quality content vector is reachable but not retrievable

**Question:** [stage 33's multimodal recall](../) makes cold items
retrievable through content vectors. This chapter reads what happens
when the content itself is low quality — a blurry image, an auto-tag
text — and the embedding that comes out is noisy.

**Before this:** [stage 33 — multimodal recall](../) and its executed
reachability model, and the [cold-image detour](../when-the-image-is-cold/).

## The low-quality vector, executed

The run ([record](runs/2026-08-07-content-vector-read.md)) embeds 12
items across four categories — two clean items per category (small
embedding noise) and one low-quality item per category (large noise) —
and measures recall@3 per quality stratum:

| stratum | items | recall@3 |
|---|---|---:|
| clean content | 8 | 8/8 |
| low-quality content | 4 | 2/4 |

## The reading

The low-quality item is in the index — it has a vector — but its noisy
embedding sits far from its category. Recall drops from 8/8 for clean
content to 2/4 for low-quality content, and the displaced items lose to
other categories' items (D2 enters category C's top-3, B3 enters
category D's top-3). Displacement is a lottery: the noise stays near
the centroid half the time (A3, B3) and drifts the other half (C3, D3).
Reachability is a quality property, not a presence property — the item
can be retrieved in theory and never in practice. The fix is a
content-quality gate before embedding (blur, resolution, caption
coverage, auto-tag confidence) and re-embedding when the source
improves; the modality gap (Liang et al. 2022) is why you cannot cheaply
repair the displaced vector in embedding space.

## The fix and its trade

The fix is a content-quality gate before embedding — blur, resolution,
caption coverage, auto-tag confidence — and a re-embed when the source
improves. The executed read prices the failure: recall@3 holds 8/8 for
clean content and falls to 2/4 for low-quality content, with the
displaced items losing to other categories' items (D2 enters category
C's top-3, B3 enters category D's top-3). The low-quality item is in
the index, so coverage reports it reachable; the noisy vector just
never wins the retrieval race.

The trade is that the gate rejects or downranks content at the margin
and can lose items whose quality looks low but is genuine, and the
re-embed costs compute every time the source improves. The repair is
upstream of the embedding because the defect is in the input — the
modality gap makes post-hoc vector repair an expensive synthesis
problem (Liang et al. 2022) — and the gate's threshold is a measured
decision, set against the recall@k the threshold costs or buys.

## Who owns the loop

- **The content-embedding team** owns the quality gate before embedding
  and the re-embed when the source improves.
- **The serving and indexing team** owns the reject-or-downrank rule
  that keeps a noisy vector from displacing clean items.
- **The evaluation team** owns the recall@k per quality stratum and the
  measured gate threshold that prices the reject decision.

## Evidence boundary

The executed synthetic read over 12 items with declared noise levels
(deterministic seed, illustrative). It demonstrates the mechanism —
noisy embeddings lose the retrieval race at the margin — but real
recall@k over held-out queries needs the actual embedding models, where
the failure shows as systematically lower recall and higher
cross-category contamination for low-quality content, and the quality
gate's threshold is a measured decision.

## Check your mental model

Answer each before opening it.

**1. Why does the aggregate "reachable" figure hide this failure?**

<details>
<summary>Answer</summary>

Because reachability counts presence, not position. Every low-quality
item has a vector, so the index reports it reachable — but reachability
says nothing about where the vector sits. The audit in [stage 33](../)
measures coverage, and this detour measures the position: the noisy
vector sits far enough from its category to lose the top-3 race half
the time. Coverage and retrieval quality are different axes, and the
aggregate hides the second one.

</details>

**2. Why is the fix upstream of the embedding, not in it?**

<details>
<summary>Answer</summary>

Because the embedding is downstream of the content. A blurry image
produces a blurry embedding no matter which encoder you run; the defect
is in the input, so the cheapest repair is to gate content quality
before embedding — reject or downrank content that fails a blur,
resolution, or caption-coverage check — and re-embed when the source
improves. The modality gap makes the alternative, fixing the vector
post-hoc, an expensive synthesis problem (Liang et al. 2022).

</details>

## Next

Back to [stage 33](../). The
[modality-mismatch detour](../when-the-modality-mismatch/) shows the
retrieval side of the same gap: how a text query biases ranking toward
text-rich items even when the vectors are clean.
