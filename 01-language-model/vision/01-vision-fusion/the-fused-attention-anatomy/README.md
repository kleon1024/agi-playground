---
status: verified
level: applied
base: scratch
label: The fused-attention anatomy
verified: 2026-08-06
---

# There is no cross-attention module

**Question:** [stage 01's vision fusion](../) grafts a vision pathway onto
mission 01's decoder. The structure this chapter dissects is the surprise
the stage's code makes obvious: there is no separate cross-attention
module anywhere in the model.

**Before this:** [stage 01's vision fusion](../) and its recorded
vision-vs-text-only run.

## The structure, computed

The run ([record](runs/2026-08-06-fusion-anatomy.md)) computes the mask
and parameters from the measured stage-01 config:

| quadrant | vision -> vision | vision -> text | text -> vision | text -> text |
|---|---|---|---|---|
| mask | bidirectional | blocked | full | causal |

A 32x32 image becomes 64 patch tokens (`VisionPatchEmbed`); those tokens
are concatenated in front of the text tokens into one sequence; a single
shared `FusedAttention` block reads the whole thing.

<!-- interactive: FusedAttentionAnatomy -->

## The structure, named

The pathway is two pieces, and both are small:

1. **Patch embedding** — 32x32x3 -> 64 tokens via a 48-wide projection
   (a 4x4 patch with 3 channels) plus a 64-row position table.
2. **The fused mask** — one attention block whose mask has four quadrants:
   vision attends to vision bidirectionally, vision is blocked from text,
   every text position sees the entire image, and text attends to itself
   causally.

The parameter delta is the anatomy's headline: 732,928 (vision) vs
718,464 (text-only), a +14,464 difference. Everything else — RoPE, RMSNorm,
SwiGLU, the training loop — is mission 01's decoder imported unmodified.
That is why mission 05 claims *reuse, not rewrite*: the vision pathway is
the patch embedding plus the mask, and nothing else changed.

## Comparison: the alternative the anatomy rules out

The natural "VLM structure" a reader expects is a separate cross-attention
module — query text against image keys/values in its own block. Mission
05's fused design replaces that with a prefix: the image is just more
tokens at the front of the sequence, and one shared attention computes
everything. The trade is structural: fused prefix attention is simpler and
reuses the decoder unchanged, at the cost of bidirectionality confined to
the vision block and text never writing into vision. The anatomy's purpose
is to make that choice visible before the mission's NOT MET verdict is
read — the verdict is about build-vs-buy, not about the pathway's shape.

## Evidence boundary

The measured stage-01 config and recorded parameter totals; the mask
quadrants follow `build_mask` in the stage's model. It computes the
structure; it does not re-train and does not claim the fused choice is
optimal — the mission's own ablation (`use_vision` on/off) is the evidence
for what the pathway contributes.

## Check your mental model

Answer each before opening it.

**1. How can text attend to the image if there is no cross-attention?**

<details>
<summary>Answer</summary>

Because the image is a prefix, not a separate stream. The 64 vision tokens
are concatenated in front of the text tokens into one sequence, and the
mask's text->vision quadrant lets every text position attend to all of
them. Cross-attention "with a separate module" is one way to do this; a
fused prefix mask is another, and mission 05 chose the second because it
lets the decoder's own attention do the work unchanged.

</details>

**2. Why is +14,464 parameters the right number to read?**

<details>
<summary>Answer</summary>

Because it is the *entire* cost of adding sight to the decoder. If the
pathway required a new cross-attention block, the delta would include a
new q/k/v projection stack per layer. The recorded 14,464 — the patch
projection plus the position table — is the measured proof that the fused
design adds only the embedding and the mask, which is the reuse claim the
mission exists to test.

</details>

## Next

Back to [stage 01's vision fusion](../), or to
[the report](../../02-report/) where the pathway's build-vs-buy verdict
is decided.
