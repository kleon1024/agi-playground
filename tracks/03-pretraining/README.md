---
status: draft
---

# 03 — Pretraining

This is where a cleaned corpus and a transformer's mechanics turn into an
actual trained model. `01-foundations` gave you the block; `02-data` (or the
speedrun's published shard) gives you the text; this track is everything in
between — how the text becomes integers, how the integers become an
architecture's input, and how a training loop turns gradient steps into a
model that predicts the next token better than chance. It is also where you
have to start making decisions with real trade-offs instead of implementing
a fixed spec: how big a vocabulary, how many parameters versus how many
tokens, what learning-rate schedule, and — once you're past the initial
run — how to extend context length or adapt the model to a new domain
without destroying what it already learned.

## What you'll build

- Your own byte-pair-encoding tokenizer, minbpe-style, trained on a real
  shard rather than imported from Hugging Face. This is the seed lesson for
  speedrun stage [`01-tokenizer`](../../speedrun/01-tokenizer/) — an 8-16k
  vocabulary trained on the `00-corpus` shard, with round-trip encode/decode
  verified on held-out text.
- A modern GPT-class decoder — RMSNorm, RoPE, GQA, SwiGLU — assembled from
  `01-foundations`' mechanics into the specific architecture that speedrun
  stage [`02-pretrain`](../../speedrun/02-pretrain/) trains: ~120M
  parameters, sized against a real token budget rather than picked
  arbitrarily.
- A training loop with the engineering that separates "the math is right"
  from "the run doesn't diverge at 2am": bf16 mixed precision, gradient
  accumulation, warmup + cosine decay, gradient clipping, and a published
  loss curve — the other half of speedrun stage `02-pretrain`.
- A scaling-law-informed answer to "how big should this model be, and how
  much data does it need" — and the vocabulary to read why production labs
  routinely violate the "compute-optimal" answer on purpose.

## Prerequisites

[`01-foundations`](../01-foundations/) (tensors, autograd, attention, the
transformer block) and [`02-data`](../02-data/) (a cleaned, deduplicated
shard — or use the speedrun's published corpus from
[`00-corpus`](../../speedrun/00-corpus/) directly, which is the intended
path if you're following the speedrun rather than entering this track
standalone).

## The conceptual spine

### BPE: merge upward from bytes, not downward from a dictionary

Byte-pair encoding starts with the smallest possible vocabulary — in the
byte-level form every production tokenizer now uses, that's the 256 possible
byte values — and greedily merges whichever adjacent pair occurs most often
in the training corpus into a new token, repeating until the vocabulary
reaches its target size. Trained on `"low lower lowest"`, the first few
merges are `l+o→lo`, `lo+w→low`, `low+e→lowe`; at inference, the same merge
rules apply in the order they were learned, so `"lower"` tokenizes as
`["lower"]` (all four rules fire) while `"lowest"` stops at `["lowe","st"]`
(the fourth rule doesn't match). The byte-level starting point is what
guarantees there is never an out-of-vocabulary token — any UTF-8 string
decomposes to bytes, in the worst case one token per byte, so the failure
mode of an unseen character is "expensive," never "impossible."

Vocabulary size is a real trade-off, not a hyperparameter to maximize. Too
small and common words fragment into many tokens, inflating sequence length
and therefore the $O(T^2)$ attention cost from `01-foundations`. Too large
and the embedding and output-projection matrices (each `vocab_size ×
d_model`) start to dominate parameter count, while rare tokens see too few
training examples to learn good representations. The trade-off is also
language-dependent: a 50k vocabulary trained mostly on English tokenizes
Chinese far less efficiently than English (published comparisons put GPT-2's
tokenizer at roughly 3x the token count of a Chinese-aware vocabulary like
Qwen's on equivalent text) — which is why fertility (tokens produced per unit
of source text) is a metric you should measure per-language, not assume is
uniform. SentencePiece's Unigram mode inverts the direction (start from a
large candidate vocabulary, prune the least-useful tokens via EM) and is
worth knowing exists, but BPE is what you'll actually implement, because
"greedily merge the most frequent pair" is a complete algorithm you can trace
by hand.

### Architecture choices compound because they target different failures

`01-foundations` derived each of RMSNorm, RoPE, GQA, and SwiGLU as the
answer to a specific problem — gradient flow, position extrapolation,
inference-time KV cache, feature selectivity. The GPT-2-to-LLaMA transition
is what happens when you adopt all four at once, and it's worth seeing the
diff as one architecture, not four unrelated papers:

| | GPT-2 (2019) | LLaMA-style (2023+) |
|---|---|---|
| Norm | LayerNorm | RMSNorm |
| Position | learned absolute embedding | RoPE |
| Attention | MHA | GQA |
| FFN | GELU, 2 matrices | SwiGLU, 3 matrices |
| Bias terms | yes | no |
| Weight tying | input/output embeddings shared | usually untied |

None of these are free — SwiGLU needs a third weight matrix, GQA needs a
`repeat_kv` to broadcast fewer KV heads across more query heads, and untied
embeddings cost `vocab_size × d_model` extra parameters — but each is solving
a problem that scaling makes worse, not better: normalization instability,
context-length limits, KV-cache memory, and representational bottlenecks all
compound as models and context windows grow, so decisions that look like
marginal wins at GPT-2 scale are load-bearing at LLaMA scale.

### The training loop is where "the architecture is correct" meets "does it actually converge"

Three engineering choices separate a training loop that works from one that
diverges or silently trains at the wrong step size:

**Precision.** FP16 has a 5-bit exponent, so its representable range tops out
around 65504 — gradients that exceed it become `inf`, and the standard
workaround (dynamic loss scaling) is itself a source of instability. BF16
keeps FP32's 8-bit exponent (same range, just 7 mantissa bits instead of 23),
so it never overflows and needs no loss scaling — this is why BF16 is the
default on any Ampere-or-newer GPU. It still needs an FP32 *master copy* of
the weights, though: a small gradient update like `1.0 + 0.0000001` rounds to
exactly `1.0` at BF16 precision but is representable at FP32, so the
optimizer step happens in FP32 even though the forward/backward pass runs in
BF16.

**Gradient accumulation** exists because the batch size you want and the
batch size that fits in 24GB of VRAM are different numbers. Running several
micro-batches, dividing each micro-batch's loss by the accumulation count
before calling `.backward()`, and only calling `optimizer.step()` after all
of them have accumulated gradients, is mathematically equivalent to training
at the larger batch size directly — the division is what keeps the effective
gradient magnitude (and therefore the effective learning rate) correct;
skipping it silently multiplies your learning rate by the accumulation
count.

**Warmup + cosine decay** isn't cosmetic scheduling. Adam's first and second
moment estimates start at zero, so early gradient steps are systematically
biased before the exponential moving averages have enough steps to correct
themselves — a large learning rate applied to a biased estimate can produce
a genuinely bad early update that the rest of training has to recover from.
Warmup (linear ramp from 0 to peak LR over the first few hundred steps) buys
the optimizer time to calibrate before the learning rate matters. The
subsequent cosine decay to roughly a tenth of peak LR is the "slow start,
slow finish" schedule that in practice outperforms a step schedule or
constant LR at matched compute across nearly every published pretraining
recipe. Weight decay is applied selectively too: 2D weight matrices get it
(it constrains their spectral norm), but 1D parameters — biases, norm gains —
don't, because penalizing them toward zero doesn't regularize anything
meaningful.

### Scaling laws: what they actually claim, and where they stop applying

Kaplan et al. (2020) fit power laws relating loss to parameter count,
dataset size, and compute independently, and concluded that scaling
parameters paid off faster than scaling data — the strategy GPT-3 followed
(175B parameters, 300B tokens, a ratio of about 1.7 tokens per parameter).
Chinchilla (Hoffmann et al., 2022) corrected this by holding compute fixed
and jointly optimizing model size *and* data size, using the identity that
one forward pass costs roughly $2N$ FLOPs per token and backward costs about
twice that, so a full training step costs approximately:

$$C \approx 6ND$$

where $N$ is parameter count and $D$ is training tokens. Solving for the loss-
minimizing split at fixed $C$ gives roughly $D_{opt} \approx 20N$ — a 70B
model wants about 1.4T tokens, not the 300B a Kaplan-style strategy would
have chosen. Chinchilla (70B params, 1.4T tokens) beat Gopher (280B params,
300B tokens) empirically, confirming the correction: GPT-3-scale models of
that era were substantially under-trained relative to their parameter count.

**This is where most people stop reading the scaling-laws story, and it's
the wrong place to stop.** Chinchilla optimizes *training* compute; it says
nothing about inference cost, and inference is not a one-time expense —
every deployed query pays for it, indefinitely. A smaller model trained
*past* its Chinchilla-optimal token budget can match a larger Chinchilla-
optimal model's quality while costing much less per query to serve, so it's
frequently worth spending extra training compute to shrink the model. Recent
models make how far this can go concrete:

| Model | Parameters | Training tokens | Tokens/parameter |
|---|---|---|---|
| Chinchilla-optimal | 70B | 1.4T | 20x |
| LLaMA 1 (7B) | 7B | 1T | ~143x |
| LLaMA 3 (8B) | 8B | 15T | ~1875x |
| Qwen3 (0.6B) | 0.6B | 36T | ~60000x |

"Compute-optimal" and "deployment-optimal" are different optimization
targets, and the published figures above are external, attributed numbers —
not runs verified by this repo. The gap between them is the single most
important correction to internalize about scaling laws in 2026: Chinchilla
is not "the right ratio," it's "the right ratio if you only pay for training
once and never pay for inference."

The other limit worth stating plainly: scaling laws are empirical power-law
fits over the regime they were measured in — a specific architecture family,
data distribution, and compute range. They predict pretraining loss, not
downstream task performance, and extrapolating them across architecture
changes (dense to MoE, a new data mixture, a new tokenizer) is an assumption,
not a guarantee the original fit licenses.

### Past the first run: longer context and continued domain training

Two extensions come up as soon as a base model exists and you want more from
it without retraining from scratch, and both connect directly back to RoPE
from `01-foundations`.

**Context extension** exploits the fact that RoPE degrades gracefully past
its training length rather than hitting a hard wall (see `01-foundations`'s
positional-encoding section). Position Interpolation compresses all
positions uniformly into the trained range — simple, but it uniformly
reduces resolution, including for nearby tokens that didn't need
compressing. NTK-aware scaling instead stretches the rotation's base
frequency non-uniformly, leaving high-frequency (fine, near-range) rotation
dimensions nearly untouched while compressing the low-frequency (coarse,
long-range) ones — because it's the long-range dimensions that were
undertrained past the original context length, not the short-range ones.
YaRN combines this with a third, interpolated band and needs only a few
hundred fine-tuning steps to extend a model 4x-16x past its trained length,
which is why it's the production default (DeepSeek-V3, Qwen2) over plain PI.

**Continual pretraining (CPT)** takes a general base model and continues
training it on domain-specific data (medical, legal, code) instead of
training a domain model from scratch — training a whole new base model is
usually not worth it when a domain corpus is a rounding error next to the
original pretraining set. The central risk is catastrophic forgetting: the
gradient direction from domain-only data pulls parameters away from
capabilities the general data taught, and general-benchmark performance
degrades measurably as domain performance improves. The standard mitigation,
in order of how much it alone typically buys you, is: mix general data back
into the domain stream (roughly 40-60% domain is a common empirical
sweet spot, not a law), keep the learning rate at or near the base model's
*final* pretraining LR rather than restarting at peak LR (re-warming to a
high LR is what causes the worst forgetting), and — if the domain corpus is
small — restrict updates to a LoRA adapter rather than the full parameter
set. None of these fully solve forgetting; the practical target is usually
"under 2% degradation on general benchmarks," not zero.

## Lessons planned

1. **`01-bpe-tokenizer-from-scratch`** — byte-pair encoding, minbpe-style,
   trained end-to-end on a real shard; the seed lesson for speedrun stage
   `01-tokenizer`.
2. **`02-gpt-architecture`** — assembling RMSNorm, RoPE, GQA, and SwiGLU into
   a complete GPT/LLaMA-class decoder, with the GPT-2-to-LLaMA diff table
   above implemented as two runnable model files, not just compared in prose.
3. **`03-training-loop`** — bf16 mixed precision, gradient accumulation,
   warmup + cosine decay, gradient clipping, checkpointing; an hours-scale
   run with a published loss curve. The seed lesson, with lesson 2, for
   speedrun stage `02-pretrain`.
4. **`04-scaling-laws-and-ablations`** — deriving $C\approx6ND$, reading
   Chinchilla's $D_{opt}\approx20N$ against the inference-optimal
   over-training trend, and running small ablations (vocab size, depth vs.
   width, data ratio) at single-GPU scale to see the curves move.
5. **`05-mapping-to-production-trainers`** — reading torchtitan/nanotron/
   OLMo-core configs against the from-scratch training loop in lesson 3: what
   changes at multi-GPU scale (FSDP2, activation checkpointing) and what
   doesn't (the optimizer math, the LR schedule shape).
6. **`06-long-context-extension`** — Position Interpolation, NTK-aware
   scaling, and YaRN as three points on a single spectrum of "how do you
   rewrite RoPE's frequencies for a longer context than you trained on";
   Ring Attention and context parallelism named as the production answer to
   the memory side of the same problem (detailed serving-side treatment
   lives in `06-inference`).
7. **`07-continual-pretraining`** — catastrophic forgetting as a data-mixing
   and learning-rate problem first, a regularization problem second; data
   mixture ratios, replay buffers, and when LoRA-only CPT beats full-parameter
   CPT.

## Common misconceptions

- **"A bigger vocabulary is always better."** It trades sequence length
  (attention cost) against embedding-table size and per-token training
  signal for rare tokens. The right size depends on your data's language
  mix, not on maximizing coverage.
- **"Chinchilla tells you the optimal model size."** It tells you the model
  size that minimizes *training* compute for a fixed loss target. If you
  care about inference cost — and in production you almost always do — the
  optimal ratio is a smaller model trained on far more tokens than 20x its
  parameter count, as LLaMA 3 and Qwen3 demonstrate.
- **"BF16 and FP16 are interchangeable 16-bit formats."** They allocate their
  16 bits completely differently — BF16 trades mantissa precision for FP32's
  exponent range, which is precisely why BF16 needs no loss-scaling hack and
  FP16 does.
- **"RoPE extrapolation methods (PI/NTK/YaRN) are alternatives to picking a
  longer max length upfront."** They're a repair for a model already trained
  at a shorter length; a model trained natively at the target length with
  matching long-range training data will generally outperform one stretched
  to that length after the fact. Extension methods are for extending an
  existing model cheaply, not a substitute for training long in the first
  place.
- **"CPT is just more pretraining."** The optimization target is different —
  you are explicitly trying to gain domain capability *without* losing
  general capability, which is a two-objective problem pretraining from
  scratch never had to solve. Learning rate and data-mixture choices that are
  fine for pretraining actively cause forgetting in CPT.

## Key papers

- **Sennrich et al., 2016 — "Neural Machine Translation of Rare Words with
  Subword Units."** The paper that introduced BPE for NLP tokenization.
- **Kaplan et al., 2020 — "Scaling Laws for Neural Language Models."** The
  original power-law fits, and the (later corrected) large-model/less-data
  conclusion drawn from them.
- **Hoffmann et al., 2022 — "Training Compute-Optimal Large Language Models"
  (Chinchilla).** The $D_{opt}\approx20N$ correction and the Chinchilla-vs-
  Gopher result confirming it.
- **Touvron et al., 2023 — "LLaMA: Open and Efficient Foundation Language
  Models."** The architecture this track's GPT-2 comparison is measured
  against — RMSNorm, RoPE, SwiGLU adopted together.
- **Su et al., 2021 — "RoFormer" (RoPE)**, and **Peng et al., 2023 —
  "YaRN: Efficient Context Window Extension of Large Language Models."** RoPE
  itself, and the current best-practice extension method built on it.
- **Gururangan et al., 2020 — "Don't Stop Pretraining."** The original case
  for continued domain-adaptive pretraining as a distinct, cheaper alternative
  to training a domain model from scratch.
- **Ibrahim et al., 2024 — "Simple and Scalable Strategies to Continually
  Pre-train Large Language Models."** The data-mixture and re-warming
  guidance this track's CPT section draws its practical numbers from.

## Speedrun note

`01-bpe-tokenizer-from-scratch` is the seed lesson for speedrun stage
[`01-tokenizer`](../../speedrun/01-tokenizer/). `02-gpt-architecture` and
`03-training-loop` are the seed lessons for speedrun stage
[`02-pretrain`](../../speedrun/02-pretrain/). Both stages currently have no
verified run — the only verified run in this repo so far is the corpus
pipeline in [`speedrun/00-corpus/`](../../speedrun/00-corpus/).
