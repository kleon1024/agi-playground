---
status: verified
level: applied
base: scratch
label: When the modality mismatch
verified: 2026-08-07
---

# The modality mismatch biases recall toward text-rich items

**Question:** [stage 33's multimodal recall](../) matches queries to
items across modalities. This chapter reads the executed cross-modal
comparison and asks what a text query costs an image-only item.

**Before this:** [stage 33 — multimodal recall](../) and its executed
reachability model.

## The mismatch, executed

The run ([record](runs/2026-08-07-modality-mismatch-read.md)) scores a
text query against two items:

| item | text-text score | text-image score |
|---|---:|---:|
| item_x (has text vector) | 0.82 | 0.55 |
| item_y (image only) | 0.00 | 0.60 |

## The reading

The image-only item competes through the cross-modal gap — its
text-image score (0.60) sits below the text-text score of the item with
text (0.82), even when the image is relevant. Same-modality matching is
stronger than cross-modal matching, so text queries systematically
favor items that have text. Modality mismatch is a recall bias toward
text-rich items: the index can find the image-only item, but it ranks
it below a text item of equal relevance.

## The fix and its trade

The fix is to report image and text coverage separately and to de-bias
the ranking for the cross-modal gap, or to give the visual-only item
the missing modality so it competes on equal terms. The executed read
prices the failure — the image-only item's best text-query score is
0.60, below the text item's same-modality 0.82, so the ranking pushes
the relevant image-only answer below a text item of equal relevance.
Same-modality matching is stronger than cross-modal matching, and the
bridge costs discriminative power.

The trade is that de-biasing risks ranking text items below their true
relevance, and giving the item the missing modality costs generation
and risks the low-quality-vector failure. The bias is structural for
visual-only content — the exact population stage 33 was meant to
rescue — so the metrics have to report image and text separately, not
one blended recall number, because the blended number is what hides the
systematic rank disadvantage of image-only items.

## Who owns the loop

- **The content-embedding team** owns the alignment quality of the
  cross-modal bridge and the synthesized-modality path.
- **The ranking and serving team** owns the de-bias rule that keeps the
  cross-modal gap from ranking relevant image-only items below text
  ones.
- **The evaluation team** owns the per-modality coverage and recall
  numbers, reported separately so the bias is visible instead of
  blended.

## Evidence boundary

The executed comparison over one declared query and two items
(illustrative, deterministic, assumed scores). It demonstrates the
mechanism; real cross-modal recall needs the embedding models and a
measured ranking over held-out queries, where the bias would show as
systematically lower rank for image-only items.

## Check your mental model

Answer each before opening it.

**1. Why is the cross-modal score lower than the same-modality
score?**

<details>
<summary>Answer</summary>

Because the embedding spaces are only partially aligned. A text query
embedding and an image embedding were trained to be comparable, but the
alignment is weaker than matching within one modality — the text-text
score (0.82) beats the text-image score (0.60) for comparable
relevance. The model has to bridge the gap, and the bridge costs
discriminative power.

</details>

**2. What is the practical bias this creates?**

<details>
<summary>Answer</summary>

Text-rich items win text queries. The image-only item's best score is
0.60, below the text item's 0.82, so the ranking pushes it down even
when it is the relevant answer. Over a catalogue, that biases recall
and ranking toward items that carry text, which is a structural
disadvantage for visual-only content — the exact population stage 33
was meant to rescue.

</details>

## Next

Back to [stage 33](../). The
[cold-image detour](../when-the-image-is-cold/) shows the reachability
side of the same problem: which query types can find the item at all.
