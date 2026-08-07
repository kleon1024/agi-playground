---
status: verified
level: applied
base: none
label: Attention variants
verified: 2026-08-06
---

# Why is the KV cache the architecture's tax?

**Question:** every served transformer keeps keys and values in memory so
decoding does not recompute them. That cache grows with context length, and
every attention variant that followed the original multi-head design — GQA,
MQA, MLA — is a bet on how much of that tax to pay. Which trade did each
successor actually make, and what did it cost in the process?

**Before this:** [stage 02's decoder block](../../../foundations/00-attention/)
and the [measured 88M configuration](../) it pretrained. This chapter is a
deep-dive on one line inside that block.

## The tax, stated once

At decode time the model needs the key and value of every earlier token at
every layer. Storing them is the only way to avoid recomputing the whole
prefix per token. The bill is linear in context and has one knob per variant:
how many key/value heads the layer keeps.

For the repo's measured configuration (d_model 768, 12 layers, 12 query
heads, bf16), the arithmetic is one line — KV bytes per token equals 2 times
layers times KV heads times d_head times bytes-per-value:

| variant | KV bytes/token | KV @ 8k context | attention params/layer | vs MHA |
|---|---:|---:|---:|---:|
| MHA (12 KV heads) | 36,864 | 288 MB | 2,359,296 | 1.00x |
| GQA (4 KV heads) — this repo | 12,288 | 96 MB | 1,572,864 | 0.33x |
| MQA (1 KV head) | 3,072 | 24 MB | 1,277,952 | 0.08x |
| MLA (latent 512) | 24,576 | 192 MB | 1,572,864 | 0.67x |

Every number above is computed from the config, not typed in —
[`core/kv_cache_anatomy.py`](core/kv_cache_anatomy.py) prints the table, and
the [run record](runs/2026-08-06-kv-cache-anatomy.md) holds the output.

<!-- interactive: AttentionAnatomy -->

## The lineage, one trade at a time

**MHA** (Vaswani et al., 2017) is the original: every head holds its own K and
V, so the cache scales with the number of heads. It is the tax at full price.

**GQA** (Ainslie et al., 2023) groups the query heads: three query heads share
one KV head, cutting the cache to a third at the same width. This is the
repo's own choice — `n_kv_head=4` under 12 query heads — and the trade is
quality: sharing KV heads removes a degree of freedom the model might have
used, so the compression is only free if quality does not measurably drop.

**MQA** (Shazeer, 2019) is the extreme of the same line: one KV head for all
query heads, an eighth of the cache. It appeared first as a serving
expedient, and its quality cost is why GQA — sharing some, not all — became
the standard instead.

**MLA** (DeepSeek-V2, 2024) changes the trade's shape rather than just its
degree: K and V are compressed into one low-rank latent plus a small
per-token part, so the cache is driven by the latent width, not the head
count. Two consequences are easy to miss. First, the headline compression
ratio is baseline-relative: at latent 512 this chapter's arithmetic gives
0.67x of this repo's MHA, nowhere near the 93% the paper reports — the paper
compared against a much larger MHA with per-head RoPE copies. Second, MLA's
decode behaves as MQA with a very wide d_head, so its per-token compute is
high — bytes are only half the story. That is exactly the tension Su Jianlin
names in the K3 article (kexue.fm/archives/11848, 2026-08-04): an attention
design that beats MLA must clear four conditions at once — quality at least
MLA's, training and prefill cost at most MLA's, a smaller KV cache, and
decode compute low enough not to collide with multi-token prediction — and
nothing published yet does, which is why K3 keeps MLA inside a KDA hybrid
rather than replacing it.

The tradeoff axis running through all four is the same one the whole lineage
chapter names: effect, efficiency, stability. MHA pays the full cache for full
expressiveness; GQA and MQA sell expressiveness for cache; MLA buys back
expressiveness with a low-rank latent and pays for it in decode compute
instead. [The language-model lineage](../../lineage.md) places this line inside the whole stack.

## The measured small-model end

The arithmetic predicts the cache; the serving stage measured what that cache
is worth on this repo's model:
[`runs/2026-07-29-engine-bench-corrected.md`](../../05-serve/runs/2026-07-29-engine-bench-corrected.md)
records the KV cache buying 1.21x at 32 tokens and *losing* by 512, and
concurrency buying nothing until kernels fuse. Read together: the tax exists
at every scale, but at toy context the engine's fixed costs dwarf it — which
is exactly why long-context serving, not toy decoding, is where the variant
choice shows up. A learner who changes the context length in the widget above
is watching the tax arrive.

## Evidence boundary

This chapter computes cache bytes and attention parameters from the measured
config; it does not measure quality loss from sharing KV heads, MLA's decode
throughput, or the K3 article's four-condition claim — the first two are
training and serving measurements this repo does not run here, and the last
is an attributed external judgment. The serving-stage bench is cited, not
re-run.

## Check your mental model

Answer each before opening it.

**1. Why does GQA cut the cache to a third while keeping 12 query heads?**

<details>
<summary>Answer</summary>

Because the cache stores keys and values, not queries. Queries are produced
one token at a time at decode and never stored; K and V are kept for every
prefix token, and their size depends on how many KV heads the layer keeps.
Three query heads sharing one KV head leaves the cache one third of MHA's at
the same width.

</details>

**2. MLA's latent-512 cache is only 0.67x this repo's MHA. Why is the paper's
93% compression claim not a contradiction?**

<details>
<summary>Answer</summary>

Because a compression ratio is baseline-relative. The paper compares against
a much larger MHA with per-head RoPE copies of K and V; this table compares
against this repo's 64-wide d_head MHA. The same mechanism produces very
different ratios depending on what it is measured against — a number worth
checking before it is quoted.

</details>

**3. What does the K3 article's four-condition test have to do with this
chapter's arithmetic?**

<details>
<summary>Answer</summary>

The arithmetic shows that KV-cache bytes are only one of the costs. MLA's
cache is small, but its decode behaves as MQA with a very wide d_head, so
per-token compute is high. The four-condition test bundles cache size with
training/prefill cost, quality, and decode compute, which is exactly the
claim that bytes alone cannot settle.

</details>

## Next

Back to [stage 02's architecture decisions](../), or forward to
[the serving stage](../../05-serve/) where the cache this chapter prices is
actually paged and measured.
