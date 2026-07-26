---
status: draft
---

# 01 — Foundations

Every later track in this curriculum treats a transformer as a given — you
import it, or you read someone else's implementation of it. This track exists
so that isn't true here. By the end of it you will have built, from tensors
up, the exact mechanism (attention), the exact training signal (autograd),
and the exact block (norm → attention → norm → FFN, residual around each)
that every model in `03-pretraining` onward is an instance of. Nothing here
is a toy for its own sake — it's the vocabulary the rest of the repo assumes
you already have.

This is also the one track with no dedicated row in
[`research/synthesis.md`](../../research/synthesis.md)'s toy↔production anchor
table: it's prerequisite mechanics, not a taught tool pairing. Its
[`LANDSCAPE.md`](LANDSCAPE.md) points forward instead — to the production
libraries (PyTorch autograd, fused attention kernels) these mechanics become
once you leave from-scratch code.

## What you'll build

- A reverse-mode autodiff engine over scalars and small tensors — the
  mechanics `torch.autograd` automates, made inspectable.
- Scaled dot-product attention derived from a numeric example, then a causal
  mask, then split across multiple heads.
- A from-scratch RoPE implementation (rotation via complex multiplication)
  and a from-scratch SwiGLU FFN, each checked against the naive
  reference it's optimizing.
- A full pre-norm transformer block — RMSNorm → attention → residual →
  RMSNorm → FFN → residual — wired into a forward pass that produces logits
  over a vocabulary.

None of this trains a real model yet; that's what a corpus and a training
loop are for, and neither exists in this track. What you get here is the
computation graph that [`03-pretraining`](../03-pretraining/) will fill with
data — the direct on-ramp to speedrun stage
[`02-pretrain`](../../speedrun/02-pretrain/).

## The conceptual spine

### Attention is content-based retrieval, not a lookup table

Every token projects itself into three roles: a **query** ("what am I looking
for"), a **key** ("what do I advertise"), and a **value** ("what I actually
contain"). Relevance is a dot product between a query and every key in the
sequence; those scores become a probability distribution over positions via
softmax, and the token's new representation is that distribution's weighted
average over values:

$$\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + \text{mask}\right)V$$

The $\sqrt{d_k}$ isn't cosmetic. If $Q$ and $K$'s entries are independent unit
Gaussians, their dot product is a sum of $d_k$ independent unit-variance
terms, so $Q\cdot K \sim \mathcal{N}(0, d_k)$ — at $d_k=64$, raw scores routinely
land near $\pm16$, and `softmax([16, -8, 2])` is already `[1.0, 0.0, 0.0]`
with gradient everywhere else. Dividing by $\sqrt{d_k}$ pulls the variance
back to 1 before softmax sees it. This is the kind of design decision this
track cares about: not "attention divides by root-d_k" but the failure mode
that forces it to.

The causal mask (setting future positions to $-\infty$ before softmax) is
what makes this usable for language modeling at all — it's the difference
between "attention" and "a model that has memorized the answer by looking at
it."

### Multi-head splits the retrieval, not the compute budget

A single attention head has one similarity function; it can be tuned toward
syntax, adjacency, or coreference, but not all three at once, because they'd
compete for the same score. Multi-head attention splits $d_{model}$ into $h$
independent subspaces (e.g. 768 → 12×64) and runs the identical mechanism in
each — different heads specialize on different relations without adding
parameters to any single head's competition.

The production complication is inference, not training: every head needs a
cached K and V per generated token, and that cache grows linearly with
sequence length and head count. **Grouped-query attention** (GQA) — used in
LLaMA 2/3, Mistral, Qwen — keeps the full query head count for expressiveness
but shares each KV pair across a group of query heads, cutting KV-cache size
by the group factor (typically 3-8x) for under 1% quality loss versus full
multi-head attention. This is why GQA belongs in a pretraining architecture
decision even though its payoff is entirely at serving time — track
[`06-inference`](../06-inference/) picks up the KV-cache consequences from
here.

### Positional information: rotate the query and key, don't add to the input

Attention's dot product is permutation-invariant — $Q_i \cdot K_j$ doesn't
know $i$ and $j$ are positions unless you tell it. Learned position
embeddings (GPT-2) add a per-position vector to the input, which works but
fixes a maximum length and encodes *absolute* position, which the model must
then learn to convert into the relative relationships it actually needs
("the previous token," "three tokens back").

RoPE (Rotary Position Embedding) injects position by rotating $Q$ and $K$ in
2D subspace pairs before the dot product, by an angle proportional to
position: $q_m' = q_m \cdot e^{im\theta}$. The reason this is the better
design falls out of one line of algebra — rotating both vectors and then
dotting them is the same as dotting the un-rotated vectors and applying the
*difference* in rotation:

$$Q_m' \cdot K_n'^\top = (Q_m e^{im\theta})(K_n e^{in\theta})^\top = (Q_m K_n^\top)\, e^{i(m-n)\theta}$$

The attention score depends only on $m-n$ — relative position falls out of
the mechanism itself, with zero added parameters, rather than being
something the model has to learn to reconstruct from two absolute-position
embeddings. Different dimension pairs rotate at different frequencies (like a
clock's second/minute/hour hands), so low dimensions carry fine-grained
position and high dimensions carry coarse-grained position. This is also
*why* RoPE extrapolates better than learned embeddings: nothing is
categorically undefined past the training length, the rotation angle is
simply larger — degradation is graceful (and further correctable — see
NTK-aware scaling and YaRN in `03-pretraining`) rather than a hard wall at
the trained context length.

### The residual stream and why pre-norm trains stably

A transformer block writes `x = x + Sublayer(Norm(x))` twice (once for
attention, once for FFN). The `x +` part matters more than it looks: it means
every block's contribution is *added* to a running residual stream rather
than replacing it, so gradients have a direct, unimpeded path back to the
input — $\partial x_1/\partial x_{12}$ includes a term that is exactly 1,
independent of depth. Put normalization *inside* that path instead
(post-norm: `x = Norm(x + Sublayer(x))`, the original Transformer's choice)
and every layer's gradient has to pass back through a normalization
Jacobian, which can shrink it. At 12 layers this is a nuisance; at 80+ it's
why post-norm transformers are hard to train past a certain depth without
extra tricks. Pre-norm is now universal in decoder-only LLMs for exactly this
reason.

### RMSNorm: the load-bearing property is rescaling, not centering

LayerNorm subtracts the mean and divides by the standard deviation:
$(x-\mu)/\sigma \cdot \gamma + \beta$. RMSNorm drops the mean-subtraction and
the bias, dividing only by the root-mean-square:

$$\text{RMSNorm}(x) = \gamma \cdot \frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2 + \epsilon}}$$

Zhang & Sennrich (2019) showed empirically that centering contributes almost
nothing to what normalization buys a network — the property that matters is
*re-scaling invariance* (the output doesn't depend on the input's overall
magnitude), and RMSNorm delivers that with one pass over the vector instead
of two, no bias term, and measurably faster wall-clock. It is not a precision
trick or an approximation of LayerNorm; it's evidence that half of what
LayerNorm computes wasn't needed.

### The FFN is where the model's knowledge actually lives

Attention moves information between token positions; the FFN is what a token
does with the information once it has it, applied identically and
independently to every position. It's easy to undersell its size: in a
standard block, attention's four projection matrices ($W_Q,W_K,W_V,W_O$,
each $d\times d$) cost $4d^2$, while a 4x-expansion FFN costs $2d\cdot4d =
8d^2$ — the FFN is roughly two-thirds of a block's parameters. Geva et al.
(2021) and follow-up work frame this concretely: the FFN's first matrix acts
as a bank of keys (each row a pattern of hidden activation that "fires" on
some input context), and the second matrix's corresponding columns are the
values that get written back into the residual stream when that key fires —
a key-value memory, trained by gradient descent instead of hand-built.

SwiGLU (LLaMA, Mistral, Qwen, DeepSeek) replaces the single up-projection
with a *gated* pair: a value path and a gate path multiplied together
element-wise before the down-projection,
$W_{down}\big[\text{SiLU}(W_{gate}x)\odot W_{up}x\big]$. The gate lets the
network decide, per input, which of the up-projection's features are
relevant right now — closer to an LSTM's forget gate than to a fixed
nonlinearity. To keep the parameter count matched to a plain 4x FFN (which
now needs three matrices instead of two), $d_{ff}$ shrinks to roughly
$\frac{2}{3}$ of the plain expansion. PaLM's ablations found SwiGLU beats
GeGLU, ReGLU, and plain GELU FFNs at matched compute, which is why it's now
the default in every architecture the pretraining track builds toward.

### The bottleneck that motivates everything past this track

Computing $QK^\top$ costs $O(T^2 d)$ and produces a $T\times T$ matrix that
standard attention materializes in full. Quadratic-in-sequence-length is the
central constraint of transformer architecture: doubling context quadruples
the attention compute, and at $T=128\text{K}$ the intermediate matrix alone
is tens of gigabytes per head, per layer. FlashAttention doesn't change this
complexity — it changes *where the time goes*. Standard attention is
memory-bound: it round-trips the full $T\times T$ score and probability
matrices through slow HBM. FlashAttention tiles the computation into blocks
that fit in on-chip SRAM and uses an online-softmax recurrence (track down
the running max and running sum incrementally, correcting earlier partial
sums as new blocks arrive) so the full matrix is never written to HBM at
all — same math, exact same numerical result, 2-10x faster in practice
because the bottleneck was data movement, not arithmetic. This mechanism (not
its full derivation) is worth internalizing here because it's the reason
`06-inference` and long-context work in `03-pretraining` are tractable
subjects rather than "buy more GPUs."

## Lessons planned

1. **`01-tensors-and-ops`** — tensors as nested arrays, broadcasting rules,
   the handful of ops (matmul, reshape, reduction) everything else composes
   from, and why frameworks vectorize instead of looping in Python.
2. **`02-autograd-from-scratch`** — a minimal reverse-mode autodiff engine
   over scalars and small tensors: build the computation graph forward, walk
   it backward, and see exactly what `loss.backward()` is doing.
3. **`03-attention-mechanics`** — scaled dot-product attention derived
   numerically, causal masking, multi-head splitting, GQA, and RoPE as the
   position-injection mechanism — the full content of this README's spine,
   implemented and tested against a naive reference.
4. **`04-transformer-block`** — RMSNorm vs LayerNorm, pre-norm residual
   wiring, SwiGLU vs GELU FFN, assembling one complete decoder block from the
   pieces in lesson 3.
5. **`05-mini-gpt-forward-pass`** — stacking blocks, token embedding, output
   projection, and a full forward pass producing logits — the direct
   prerequisite for `03-pretraining`'s training loop.

## Common misconceptions

- **"Attention is where the model's knowledge lives."** Attention routes
  information; it doesn't store much of it. The FFN holds roughly two-thirds
  of a block's parameters and functions as a trained key-value memory —
  that's where most of what a model "knows" is written down.
- **"RoPE encodes absolute position."** It doesn't encode position at all in
  any single vector — it rotates $Q$ and $K$ so that their *dot product*
  depends only on the relative offset $m-n$. There is no absolute-position
  information recoverable from $Q_m'$ alone.
- **"GQA is a training-time optimization."** It has a small effect on
  training compute, but its entire reason for existing is the inference-time
  KV cache, which grows linearly with sequence length and head count and
  dominates memory at serving time. This is a serving-cost decision made at
  architecture time.
- **"FlashAttention is an approximation — that's why it's faster."** It is
  mathematically exact, bit-for-bit equivalent to the naive computation
  (modulo floating-point summation order). The speedup comes entirely from
  reducing HBM traffic on a memory-bound operation, not from doing less
  arithmetic.
- **"RMSNorm is just a faster, slightly-worse LayerNorm."** The empirical
  finding (Zhang & Sennrich 2019) is closer to the opposite: mean-centering,
  the part RMSNorm removes, contributes little to normalization's benefit.
  RMSNorm isn't an approximation of LayerNorm's effect — it isolates the part
  that was doing the work.

## Prerequisites and reading order

None — this is the entry point. You need working Python, comfort with
matrix/vector notation, and derivatives at an undergraduate level. No prior
ML exposure is assumed. Read lessons in order; each depends on the previous
one's implementation, not just its ideas.

## Key papers

- **Vaswani et al., 2017 — "Attention Is All You Need."** The mechanism
  itself; also the source of post-norm and sinusoidal positions, both of
  which this track explains why modern models replaced.
- **Su et al., 2021 — "RoFormer" (RoPE).** Rotary position embedding; the
  derivation in this README's positional-encoding section is this paper's
  central identity.
- **Zhang & Sennrich, 2019 — "Root Mean Square Layer Normalization."** The
  ablation showing re-centering isn't the load-bearing part of LayerNorm.
- **Shazeer, 2020 — "GLU Variants Improve Transformer."** Introduces the
  GLU-family FFN gating that SwiGLU is one instance of.
- **Geva et al., 2021 — "Transformer Feed-Forward Layers Are Key-Value
  Memories."** The empirical case for reading the FFN as a memory, not a
  generic nonlinearity.
- **Dao et al., 2022 — "FlashAttention."** The tiling + online-softmax
  algorithm that makes long-context attention a memory-bandwidth problem you
  can engineer around instead of a wall you hit.
- **Ainslie et al., 2023 — "GQA: Training Generalized Multi-Query Transformer
  Models from Multi-Head Checkpoints."** The KV-cache-vs-quality trade-off
  curve that motivates grouped-query attention.

## Speedrun note

This track has no dedicated speedrun stage of its own — it's the code that
speedrun stage [`02-pretrain`](../../speedrun/02-pretrain/) (owned by
[`03-pretraining`](../03-pretraining/)) is assembled from. Get comfortable
here before starting the speedrun; everything downstream assumes you can read
this track's mechanics without translating them from a library's source.
