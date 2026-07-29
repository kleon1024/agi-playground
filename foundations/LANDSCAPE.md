---
status: draft
level: reference
---

# Foundations: Landscape

`research/synthesis.md`'s anchor table doesn't carry a dedicated row for this
track — it's prerequisite math/mechanics, not a toy-vs-production pairing tied
to a specific tool lineage. The mappings below are the general-purpose
libraries the from-scratch mechanics correspond to once you leave this track;
treat them as forward pointers, not synthesis-sourced anchors.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| Scalar/small-tensor autograd built by hand in `02-autograd-from-scratch` | PyTorch `autograd` engine, JAX `grad`/`vjp` | Both trace a computation graph and reverse it; ours is unbatched and CPU-only so every line is inspectable. Once the mechanics click, read PyTorch's `autograd` source — it's the same idea with dispatch, device placement, and fused kernels layered on. |
| Naive O(n²) attention in `03-attention-mechanics` | PyTorch `scaled_dot_product_attention` (fused kernels), FlashAttention, xFormers | The naive version is correct but memory-bound; production kernels fuse and tile the same math to avoid materializing the full attention matrix. `06-inference`'s `LANDSCAPE.md` covers the serving-side implications (paged KV, batching) once a model is trained. |

Neither row above is a single-vendor dependency: PyTorch/JAX for autograd, and
at least two distinct attention-kernel projects (FlashAttention, xFormers)
plus PyTorch's built-in fused path for attention.
