---
status: draft
---

# 06 — Inference

**Goal:** take a trained checkpoint and make it fast to run — and take a training
loop that fits on one GPU and understand how it scales past one. Two subjects,
taught together because they share a root cause: both are about using scarce
GPU memory and bandwidth well, not about writing more matmuls.

**Why this track exists as an exercise-driven subject, not a source-reading
assignment.** The default way this material gets "taught" in 2026 is "go read
the vLLM source" — a large, production-hardened codebase with years of
accreted scheduling logic, kernel dispatch, and distributed-serving plumbing.
That teaches vLLM's specific implementation, not the small number of ideas
that make it fast: a KV cache turns quadratic recompute into linear
generation, paging turns memory allocation into an OS problem, continuous
batching turns static batches into a per-iteration schedule, and speculative
decoding turns idle GPU compute during decode into free token throughput.
Each of those ideas fits in a few hundred lines and is worth building once,
by hand, before reading how vLLM or SGLang does it at production scale.
Training infra gets the same treatment: gradient accumulation, activation
checkpointing, and mixed precision are three single-GPU techniques you can
implement and measure directly, and FSDP2 is those same three ideas made
distributed, not a different subject.

## What you build

The seed lessons, `01-kv-cache` through `03-continuous-batching`, are speedrun
[stage 05](../../speedrun/05-serve/): a minimal engine — KV cache, paged
blocks, iteration-level batching — benchmarked against naive `generate()` on
the model your own speedrun trained. `04-speculative-decoding` and
`05-quantization` are the production-relevant serving optimizations layered on
top; `06-fsdp2-distributed-training` and `07-profiling` are the training-infra
half of the track, useful the moment you want to scale `03-pretraining` past
one GPU or explain why a training step is slow instead of guessing.

## Conceptual spine

### Why autoregressive decoding needs a KV cache

Generating token `n+1` requires attention over tokens `1..n`. Without caching,
each new token means recomputing K and V projections for every prior token —
quadratic total work across a full generation. The KV cache stores each
token's K and V vectors the first time they're computed, so decoding step `n`
only computes K/V for the *new* token and reuses everything before it: linear
total work instead of quadratic.

This is also why decoding at small batch size is **memory-bandwidth-bound,
not compute-bound**: a single-token forward pass is a thin matmul against the
full weight matrices, and the GPU spends most of its time streaming weights
and cached K/V out of HBM rather than doing arithmetic. This is the
architectural reason speculative decoding (below) works at all — there's
idle compute capacity during decode waiting to be used.

The cache isn't free. Per-token memory for one layer is
`2 (K and V) × num_kv_heads × head_dim × dtype_bytes`; multiply by
`num_layers × sequence_length × batch_size` for the total. A 7B-class model
with 32 layers, 32 heads, head_dim 128, fp16, spends roughly 512KB of cache
per token — a few gigabytes at moderate context length and batch size, on top
of the weights themselves, and the number that mostly determines the maximum
batch size (and therefore throughput) a serving system can sustain. Two
production levers reduce it directly: **grouped-query attention (GQA)**
shares K/V heads across groups of query heads (LLaMA-2 70B uses 8 KV heads
against 64 query heads), cutting cache size in proportion; **sliding-window
attention** (Mistral) bounds the cache to a fixed window regardless of how
long the context grows, trading unbounded long-range recall for a hard memory
ceiling.

### PagedAttention: KV cache as OS-style virtual memory

Naive KV cache allocation reserves a contiguous buffer sized for each
request's maximum possible sequence length up front. That wastes memory two
ways: **internal fragmentation** (a request that stops early never uses the
memory reserved for the tokens it didn't generate) and **external
fragmentation** (different requests' pre-sized buffers can't be reused for
each other even when memory is technically free between them). Production
systems reported 60–80% of KV cache memory wasted this way before
PagedAttention.

PagedAttention (Kwon et al., 2023 — vLLM's foundational idea) applies the
fix operating systems solved decades ago: allocate KV cache in small
fixed-size **blocks** (e.g. 16 tokens), keep them non-contiguous in physical
memory, and maintain a per-sequence **block table** mapping logical token
position to physical block — exactly a page table mapping virtual to physical
addresses. Blocks are allocated on demand as generation proceeds and freed
immediately when a sequence finishes, which is what makes waste drop to a few
percent instead of most of the allocation.

The same block-table indirection buys two more things for free:
**copy-on-write** lets multiple sequences (e.g. parallel samples or
beam-search branches) that share a common prefix point at the same physical
blocks until they diverge, only then copying; and **prefix caching** hashes
blocks by content so that a repeated system prompt or few-shot prefix across
many requests reuses already-computed KV blocks instead of recomputing them.

### Continuous (iteration-level) batching

Static batching waits for a fixed group of requests, runs the whole batch
until every sequence in it finishes, and only then admits new requests — so a
short sequence that finishes early sits idle, holding its batch slot, while
the batch waits on the longest sequence. Continuous batching (the term comes
from Orca's "iteration-level scheduling", which vLLM and SGLang both
implement) makes the scheduling decision every forward pass instead of every
batch: the instant a sequence finishes, its slot is freed and a new request is
admitted into the *next* iteration, so the GPU's batch composition is nearly
always full. This — not a bigger batch size — is the mechanical reason
continuous batching drives large throughput gains over static batching; Orca
reported up to 36x throughput improvement over contemporary dynamic-batching
systems from this scheduling change alone.

### Speculative decoding: draft, verify, and why acceptance rate is everything

Decode is memory-bandwidth-bound, which means verifying several candidate
tokens in one forward pass costs barely more than verifying one — the
bottleneck is streaming weights, not the arithmetic. Speculative decoding
exploits this: a small, fast **draft model** proposes `K` tokens
autoregressively, then the large **target model** verifies all `K+1`
positions (the `K` proposed plus one genuinely new token) in a single parallel
forward pass.

Verification uses **modified rejection sampling**, not a naive accept/reject
on quality: each drafted token `x` is accepted with probability
`min(1, p_target(x) / p_draft(x))`; if rejected, a token is instead sampled
from the residual distribution `max(0, p_target(x) − p_draft(x))`, renormalized.
This is the detail that makes speculative decoding an exact optimization, not
an approximation — the resulting output distribution is provably identical to
sampling from the target model alone, just produced faster. There is no
quality trade-off to weigh; the only variable is speed.

Speed is governed almost entirely by the **acceptance rate** `α` — the
probability a drafted token survives verification. Expected accepted tokens
per round scale roughly as `(1 − α^(K+1)) / (1 − α)`; a high-quality draft
model with `α` near 0.8–0.9 can net several tokens per target-model forward
pass, while a poor draft model with low `α` mostly wastes the extra draft
compute for little gain. This is why the field moved from "borrow an
independent small model as the draft" toward drafting mechanisms with much
higher acceptance rates: **Medusa** attaches multiple parallel prediction
heads to the target model itself and verifies a tree of candidate
continuations in one pass; **EAGLE** (now EAGLE-3, reported default-on in
production serving as of 2026) drafts from the target model's own hidden
features rather than an independent model's token distribution, pushing
acceptance rates meaningfully higher than either independent-draft-model or
Medusa approaches; **lookahead decoding** drops the draft model entirely and
generates candidate n-grams via a Jacobi-iteration-style parallel guess.
Reported gains across these approaches range roughly 2–6.5x at low
concurrency — and shrink as batch size grows, because the idle compute
speculative decoding exploits is exactly what large batches already consume.

### Quantization: what's traded for what

Quantization reduces the bit-width of weights (and sometimes activations and
the KV cache itself) after — or during — training. **Post-training
quantization (PTQ)** quantizes a fully trained model using a small calibration
set (a few hundred examples), fast but with a larger accuracy hit at
aggressive bit-widths; **quantization-aware training (QAT)** simulates
quantization during training or fine-tuning so the model adapts to the
rounding error, better accuracy at 4-bit and below at the cost of real
training compute. Within PTQ, **GPTQ** quantizes layer by layer using an
approximate-Hessian error-compensation scheme (quantize one weight, adjust the
remaining unquantized weights in that layer to compensate for the error just
introduced), while **AWQ** observes that a small fraction of weight channels —
the ones multiplied by large-magnitude activations — matter disproportionately
for output quality, and protects exactly those channels instead of computing
a full Hessian, typically faster and competitive with or better than GPTQ at
aggressive compression. **GGUF** (llama.cpp's on-disk format) and
**bitsandbytes' NF4** (the QLoRA quantization, an information-theoretically
tuned 4-bit format for roughly-Gaussian weight distributions) target
consumer/single-GPU inference specifically — NF4 alone turns a ~14GB fp16 7B
model into roughly 4.5GB. **FP8**, natively supported by Hopper-class GPUs,
sits apart from the INT formats: its floating-point exponent preserves a wide
dynamic range that INT8 lacks, which is why it typically needs little or no
calibration to avoid outlier-channel accuracy collapse. The practical 2026
sweet spot is 4-bit: below it, quality degrades sharply without QAT-level
effort, which is exactly the accuracy/compression frontier this track's
quantization lesson is built to make visible rather than assert.

### Prefill/decode disaggregation: the dominant production serving pattern

Prefill (processing the full prompt) and decode (generating one token at a
time) have opposite performance profiles: prefill is **compute-bound** — large
matmuls over the whole prompt at once, high GPU utilization — while decode is
**memory-bandwidth-bound**, as established above. Running both phases on the
same GPU in the same batch means they compete: a long prefill request
arriving mid-stream stalls decode steps already in flight for other requests
(hurting time-per-output-token for everyone else), or scheduling decode ahead
of prefill hurts time-to-first-token instead. Neither priority order is free.

The dominant 2025–2026 fix is **disaggregated serving**: run prefill on one
pool of GPUs tuned for compute throughput and decode on a separate pool tuned
for cache capacity and bandwidth, transferring the computed KV cache between
them after prefill completes (over NVLink or RDMA, with pipelining to hide
transfer latency behind the next request's prefill). Splitwise (Patel et al.,
2024) and DistServe (Zhong et al., 2024) are the two foundational published
architectures; Mooncake describes Moonshot AI's production KV-cache-centric
take on the same idea; NVIDIA Dynamo and TensorRT-LLM now ship disaggregation
as a first-class prefill-worker → router → decode-worker topology. The
lighter-weight alternative, **chunked prefill** (Sarathi-Serve), doesn't
disaggregate at all — it splits a long prefill into chunks interleaved with
ongoing decode steps on the *same* GPU, trading some prefill latency for
avoiding the operational complexity, KV-transfer cost, and minimum-scale
requirements that full disaggregation needs to pay off. This track teaches
disaggregation conceptually (`03-continuous-batching`'s and
`04-speculative-decoding`'s production notes both touch it): it is out of
reach to build hands-on on a single 24GB card, but is the architecture every
serving engine you'll actually deploy against uses.

### Training infra: three single-GPU fundamentals, then FSDP2

Three techniques compose to fit larger effective training runs on one GPU,
and matter individually before they matter distributed. **Gradient
accumulation** decouples effective batch size from the largest micro-batch
that fits in memory: run several micro-batches, sum gradients, step the
optimizer once. **Activation checkpointing** trades compute for memory —
store only a subset of forward-pass activations (e.g. at transformer-block
boundaries) and recompute the rest during backward, typically ~20–30% extra
compute for memory savings that let a much larger batch or model fit.
**Mixed precision** (bf16/fp16 compute with an fp32 master copy of weights and
optimizer state for numerical stability) roughly doubles both throughput and
feasible batch size on modern GPUs.

**FSDP2**, PyTorch's current default for 2–8 GPU training, is these same
ideas made distributed via the DTensor abstraction: each parameter is
independently sharded across the process group (per-parameter sharding,
replacing FSDP1's flattened-parameter approach), which composes more cleanly
with `torch.compile` and tensor parallelism. It's reported to reach
meaningfully higher throughput than DeepSpeed ZeRO-3 in overlapping-memory
regimes, largely from that cleaner compile integration — though DeepSpeed
remains the better fit for MoE training and heavy CPU/NVMe offload above
roughly 10B parameters. One interaction worth knowing before it surprises you:
gradient accumulation under FSDP2 only needs to all-reduce gradients at the
accumulation boundary, not every micro-batch — get this wrong and sharded
training either wastes bandwidth or silently accumulates stale gradients.

### Profiling: PyTorch Profiler → Nsight

The right order is coarse to fine, not "reach for the deepest tool first."
**PyTorch Profiler** gives step- and op-level timing plus a memory timeline —
the fast first look that tells you roughly where time goes. **Nsight
Systems** gives a system-wide timeline correlating CPU launches, GPU kernels,
and memory transfers, which is what actually reveals *gaps* — a data-loading
stall, an all-reduce your training loop is silently waiting on — that
per-kernel numbers can't show. Only once Nsight Systems has pointed at a
specific kernel is **Nsight Compute**'s per-kernel view (occupancy, memory
bandwidth utilization, warp stalls) worth reaching for. Profiling has its own
honesty rule worth internalizing early: the profiler itself has overhead, and
a profiled run's absolute numbers are not the same as an unprofiled run's —
what transfers is the *shape* of the bottleneck, not the exact wall-clock.

## Where this breaks in production, honestly

- **Low acceptance rate makes speculative decoding a net loss, not a neutral
  no-op.** Running a draft model costs real compute; if `α` is low enough
  (mismatched draft/target pair, an out-of-distribution prompt), the extra
  draft forward passes can leave you slower than plain decoding, not merely
  less accelerated.
- **Aggressive quantization degrades unevenly, not uniformly.** A model can
  post nearly unchanged perplexity at 4-bit while specific capabilities (long
  arithmetic, rare-token recall) degrade first and disproportionately —
  perplexity is a weak proxy for what a specific downstream use case will
  notice.
- **Disaggregation adds a failure mode that colocated serving doesn't have:**
  KV-transfer latency and network reliability between prefill and decode
  pools become part of the critical path, and it only pays for itself past a
  request-rate threshold that makes keeping both pools' utilization high
  achievable — below that threshold, chunked prefill on a single pool is
  simpler and can be equally effective.
- **Paging eliminates KV-cache fragmentation specifically; it does not
  eliminate memory pressure.** Total KV cache still has to fit, block size
  choice still trades internal fragmentation against block-table overhead,
  and prefix caching's benefit disappears the moment requests stop sharing
  real prefixes.

## Common misconceptions

1. **"Continuous batching just means bigger batches."** It's a scheduling
   change — the batch's *composition* changes every iteration as sequences
   enter and exit — not a change to any single batch's size.
2. **"Quantization always costs meaningful accuracy."** At 8-bit, and often
   at 4-bit with good calibration (GPTQ/AWQ), degradation is within noise for
   most tasks; the real accuracy cliff sits below 4-bit without QAT-level
   effort, not at "any quantization at all."
3. **"Speculative decoding is a lossy speed/quality trade-off."** With correct
   modified rejection sampling it's mathematically exact — same output
   distribution as the target model alone, just produced faster. There's
   nothing to trade off.
4. **"More attention heads always means more KV cache to store."** GQA and
   MQA decouple these: how many *query* heads a model uses for representation
   capacity is independent of how many *KV* heads get cached, which is a
   deliberate memory/quality knob, not a fixed consequence of model size.
5. **"FSDP2 replaces the need for tensor/pipeline parallelism."** It replaces
   ZeRO-style sharding for the 2–8 GPU regime; genuinely large models and
   latency-critical serving still need TP/PP, and FSDP2 composes with them
   rather than making them obsolete.

## Prerequisites

`03-pretraining` (this track needs a trained checkpoint to serve, or a
training loop to profile and scale). Can be entered independently with any
small open HF checkpoint if you're not running the full track sequence.

## Key papers and reference implementations

- Kwon et al., *Efficient Memory Management for Large Language Model Serving
  with PagedAttention* (SOSP 2023) — the paging idea this track's `02` lesson
  implements from scratch.
- vLLM team, *Inside vLLM: Anatomy of a High-Throughput LLM Inference System*
  (2025 blog) — the production-scale map for everything this track builds
  small.
- Orca (OSDI 2022) — iteration-level scheduling, the origin of continuous
  batching.
- Leviathan et al., *Fast Inference from Transformers via Speculative
  Decoding* (2023) — the original draft/verify/rejection-sampling formulation.
- Li et al., EAGLE / EAGLE-3 — feature-level drafting, the current
  default-on production speculative-decoding approach.
- Cai et al., *Medusa: Simple LLM Inference Acceleration with Multiple
  Decoding Heads* — tree-attention verification without a separate draft
  model.
- Frantar et al., *GPTQ* (2023) and Lin et al., *AWQ* (2023) — the two
  dominant one-shot weight-quantization approaches this track's `05` lesson
  compares.
- Dettmers et al., *QLoRA* (2023) — NF4 quantization's derivation and the
  bitsandbytes implementation.
- Patel et al., *Splitwise* (2024); Zhong et al., *DistServe* (2024); Agrawal
  et al., *Sarathi-Serve* — the disaggregation and chunked-prefill literature
  this track's production notes draw on.
- PyTorch, *FSDP2 / DTensor documentation* — the sharding abstraction this
  track's `06` lesson maps single-GPU technique to.

## Hardware reality

`01-kv-cache` through `04-speculative-decoding` run comfortably on a single 24GB card:
nano-vLLM-scale engines and 1–8B checkpoints (including a small
draft/target pair for speculative decoding) fit in 24GB with room to spare.
`05-quantization` is inference-only across formats and needs nothing beyond
that either. `06-fsdp2-distributed-training`'s single-GPU-teachable half
(gradient accumulation, activation checkpointing, mixed precision) runs
locally; the multi-GPU sharding behavior FSDP2 actually exists for, and any
hands-on prefill/decode disaggregation lab, need 2+ GPUs and move to the
Modal lane, with dollar cost printed in `runs/`. `07-profiling` runs entirely
on the local lane — Nsight Systems and Nsight Compute both work against a local
CUDA install, no cloud dependency required.

## Planned lessons

1. `01-kv-cache` — why autoregressive decoding is memory-bound, KV cache
   memory math, from scratch.
2. `02-paged-attention` — paged KV blocks, block tables, prefix caching and
   copy-on-write — the memory-management idea behind vLLM's core innovation.
3. `03-continuous-batching` — iteration-level scheduling across in-flight
   requests, benchmarked against naive `generate()`; production notes cover
   prefill/decode disaggregation as the pattern this pairs with at scale.
4. `04-speculative-decoding` — draft-and-verify decoding with modified
   rejection sampling, EAGLE/Medusa-style variants, acceptance-rate analysis.
5. `05-quantization` — PTQ vs QAT, GPTQ/AWQ/GGUF/NF4/FP8 compared on
   identical checkpoints, for serving.
6. `06-fsdp2-distributed-training` — the three single-GPU fundamentals, then
   FSDP2/DTensor sharding across GPUs.
7. `07-profiling` — PyTorch Profiler → Nsight Systems → Nsight Compute,
   finding a real bottleneck rather than guessing at one.

## Next

[Track 07 — Evals](../07-evals/): once you can serve and profile, you need an
honest way to measure what you built — perplexity and task-suite scoring
against the checkpoints and engines from this track, and the harness-disclosed
methodology this track's disaggregation and speculative-decoding numbers
already depend on being reported honestly.
