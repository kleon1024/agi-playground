---
status: draft
level: reference
---

# Foundations: Landscape

`reference/research/synthesis.md`'s anchor table doesn't carry a dedicated row for this
track — it's prerequisite math/mechanics, not a toy-vs-production pairing tied
to a specific tool lineage. The mappings below are the general-purpose
libraries the from-scratch mechanics correspond to once you leave this track;
treat them as forward pointers, not synthesis-sourced anchors.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| The from-scratch scalar autodiff engine in [backpropagation](03-backpropagation/) | PyTorch `autograd` engine, JAX `grad`/`vjp` | Both trace a computation graph and reverse it; ours is one Python object per scalar operation so every line is inspectable, and it is checked to agree with torch's own `.backward()` to float64 precision (`1.11e-16`) on an identical graph. Once the mechanics click, read PyTorch's `autograd` source — it's the same idea with dispatch, device placement, and fused kernels layered on. |
| Naive O(n²) attention in [the decoder block](README.md) | PyTorch `scaled_dot_product_attention` (fused kernels), FlashAttention, xFormers | The naive version is correct but memory-bound; production kernels fuse and tile the same math to avoid materializing the full attention matrix. [The serving landscape](../01-language-model/05-serve/LANDSCAPE.md) covers the implications on the other side — paged KV, batching — once a model is trained. |
| The from-scratch SGD/momentum/Adam in [optimization](02-optimization/) | PyTorch `torch.optim.AdamW`, `torch.optim.SGD`; JAX `optax` | Same update rules; production implementations add fused CUDA kernels (all parameters updated in one kernel launch instead of one per-tensor Python-loop step), weight decay decoupled correctly (AdamW vs. plain L2 penalty added to the gradient), and gradient clipping. The mechanism this chapter isolates (per-parameter adaptive normalization) is unchanged between the toy and the library call. |

Neither row above is a single-vendor dependency: PyTorch/JAX for autograd, and
at least two distinct attention-kernel projects (FlashAttention, xFormers)
plus PyTorch's built-in fused path for attention. The optimizer row similarly
names two distinct production implementations (PyTorch, JAX/optax), not one.
