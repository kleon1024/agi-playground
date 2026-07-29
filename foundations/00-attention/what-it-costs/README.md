---
status: draft
level: foundation
label: What a block costs
---

# Where does a transformer actually spend its parameters and its memory?

[The decoder block](../README.md) explained what each part computes. This
chapter prices them, and the answer contradicts the intuition most readers
arrive with.

**Before this:** the decoder block, through section 7. You need SwiGLU's three
matrices, grouped-query attention's split, and the shapes of the projections.

Every number below is for the model this repository trained: 12 layers, 12
query heads, 4 key-value heads, `d_model` 768, `d_head` 64, `d_ff` 2048, 16,512
vocabulary entries, 1,024-token context.

## The parameter budget adds up exactly

Each component's arithmetic comes straight from the chapter before this one:

| Component | Arithmetic | Parameters | Share |
|---|---|---|---|
| Feed-forward | $3 \times 768 \times 2048 \times 12$ | 56,623,104 | 64.2% |
| Attention projections | $(768^2 + 2 \times 768 \times 256 + 768^2) \times 12$ | 18,874,368 | 21.4% |
| Embedding (tied with the output head) | $16{,}512 \times 768$ | 12,681,216 | 14.4% |
| RMSNorm scales | $25 \times 768$ | 19,200 | 0.02% |
| **Total** | | **88,197,888** | |

That total is exactly the parameter count
[the model](../../../missions/01-language-model-agent/02-pretrain/) reports —
not approximately, exactly. Nothing was rounded and nothing was omitted, which
is the point of showing it: a transformer's size is fully determined by six
numbers you already chose.

Two things fall out of the table.

**Attention is not where the knowledge is.** The feed-forward network holds
three times as many parameters as every attention projection combined.
Attention decides what to read; the feed-forward network is what gets read.
A reader who pictures a transformer as "mostly attention" has the ratio
backwards, and will also mis-predict which layer type dominates a training
step's arithmetic.

**Normalization is free and the embedding is not.** RMSNorm's learned scales
are 0.02% of the model. The embedding is 14.4% at a 16,512-entry vocabulary —
and it is 14.4% *only because* the output head is tied to it. Untie them and
the model grows to 100,879,104 parameters, a 14% increase that buys, at this
scale, very little.

The asymmetric attention row is worth reading twice:
$768^2$ for queries, $2 \times 768 \times 256$ for keys and values, $768^2$
again for the output projection. Keys and values are narrow because there are
only four key-value heads. That asymmetry is grouped-query attention, and it is
visible in the parameter count before a single token is served.

## The cache is what actually constrains you

Parameters are paid once. The key-value cache is paid per token, per concurrent
request, and it is the number that decides how many users a card can hold.

$$
\text{KV bytes per token} = 2 \times n_{\text{layer}} \times n_{\text{kv}} \times d_{\text{head}} \times b
$$

The leading 2 is keys plus values; $b$ is bytes per element, 2 in bf16.

| | key-value heads | bytes/token | full 1,024-token context |
|---|---|---|---|
| this model, grouped-query | 4 | 12,288 | **12.0 MiB** |
| the same model, plain multi-head | 12 | 36,864 | 36.0 MiB |

Twelve query heads either way. Identical retrieval capacity, one third of the
cache. Divide a 24GB card by each figure and the ceiling is 2,048 concurrent
full-context sequences against 683 — an upper bound, since it ignores weights,
activation workspace and allocator padding, but the *ratio* is exact and the
ratio is what the architecture decided. At 88M the weights are a rounding error
beside the cache; at 7B the same arithmetic decides whether a deployment is
possible at all.

This is why grouped-query attention appears in essentially every model released
after 2023, and why [serving](../../../platform/serving/) treats cache
allocation as its central problem rather than a detail.

## Attention's memory is quadratic, and it is not the weights

The score matrix has shape `sequence × sequence`, and it exists only between
the matmul and the softmax.

| Context | one head | one layer, 12 heads |
|---|---|---|
| 1,024 tokens | 2 MiB | 24 MiB |
| 2,048 tokens | 8 MiB | 96 MiB |
| 4,096 tokens | 32 MiB | 384 MiB |

Four times the memory for twice the context, for a tensor discarded
immediately. FlashAttention removes this line from the budget entirely — not by
changing the result or the quadratic arithmetic, but by tiling the operation so
the full matrix is never materialized in slower memory.

That is the first instance of a pattern this curriculum uses repeatedly:
preserve the invariant, change the system boundary. The invariant is exact
attention; the boundary that moved is where intermediate state lives. Paged
attention, continuous batching and quantization are all the same move applied
to a different line of the same budget.

Notice which of the three costs on this page scales with what. Parameters are
fixed. The cache is linear in context and linear in concurrency. The score
matrix is quadratic in context and does not depend on concurrency at all.
Three different growth curves, three different mitigations, and confusing them
is how capacity estimates go wrong by an order of magnitude.

## Check your mental model

1. Which component holds the most parameters, and by roughly what factor?
2. Why are the key and value projections narrower than the query projection in
   this model, and where does that show up at serving time?
3. Untying the output head from the embedding adds how much, proportionally,
   and why is that a bad trade at this scale?
4. Context doubles. What happens to the cache, and what happens to the score
   matrix?
5. Which of the three costs does FlashAttention address, and which two does it
   leave untouched?

## Evidence boundary and next step

Every number here is arithmetic over a declared configuration, not a
measurement. It tells you what the model *must* allocate; it does not tell you
what a runtime actually allocates, which includes fragmentation, activation
workspace, optimizer state during training, and allocator padding.
[Serving](../../../platform/serving/) measures the difference, and
[throughput](../../../platform/training/03-throughput/) shows how far the same
model's real utilization can move without any of these numbers changing.
