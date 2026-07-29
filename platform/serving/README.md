---
status: draft
level: foundation
---

# How does a checkpoint become a responsive service?

Every request arrives with a different prompt length, output length, and memory
footprint, and they all share one card.

[Stage 05 of the language-model system](../../missions/01-language-model-agent/05-serve/)
sends you here for the cost model of a single request. Take that back; the
measured numbers, and what batching is worth against a fused kernel, are
already there.

Follow one request:

```text
admit -> tokenize -> prefill -> allocate KV state
      -> decode one token at a time -> stop -> release memory
```

Model math determines the work. The serving system determines when that work
runs, where intermediate state lives, and whether another request can share the
device.

**Before this:** [what a block costs](../../foundations/00-attention/what-it-costs/),
for the key-value cache arithmetic every decision on this page is made against.

## Why one latency number hides two different bottlenecks

During **prefill**, the model processes all prompt tokens in parallel and
creates keys and values for every layer. During **decode**, it produces one new
token per step and attends to all cached keys and values.

These phases stress different resources:

| Phase | Work shape | Common bottleneck |
|---|---|---|
| Prefill | many prompt tokens in parallel | matrix compute |
| Decode | one token per active request | memory bandwidth and KV reads |

A single average latency hides both. Report time to first token separately from
inter-token latency and total completion time.

## What does keeping the past cost?

Without a KV cache, generating token `t+1` recomputes keys and values for all
tokens `1..t`. Caching makes each decode step reuse that state.

The memory cost grows with batch, sequence length, layers, KV heads, head
dimension, and bytes per element:

$$
\text{KV bytes}
=
2BLTH_{\text{kv}}d_hb
$$

The factor of two is for keys and values.

**Worked, on the 88M model served here** — 12 layers, 4 key-value heads,
`d_head` 64, bf16 — one token costs
$2 \times 12 \times 4 \times 64 \times 2 = 12{,}288$ bytes, so one 1,024-token
request holds **12.0 MiB** of cache. The weights are 88,197,888 parameters at
2 bytes, or 176.4 MB. Divide: cache overtakes weights at 14,355 live tokens —
**14 concurrent full-context requests**. Past that point the model is the small
object in memory and the conversations are the large one, which inverts the
intuition most people bring to a serving box.

Change context and batch below and find that crossover yourself.

<!-- interactive: KVCacheGrowth -->

This is why grouped-query attention chosen during model design changes serving
economics: fewer KV heads reduce cache memory for every live token.

## Why reserving the cache up front wastes most of it

Requests do not know their final length when admitted. Reserving each request's
maximum possible contiguous cache wastes memory; waiting for a large contiguous
region causes fragmentation.

PagedAttention divides cache memory into fixed-size blocks and maps logical
token positions to physical blocks. The invariant is unchanged: each token's
key and value must be retrievable. The allocation boundary changes from one
contiguous request buffer to a block table.

Add and finish requests below. Compare reserved contiguous memory with blocks
actually used.

<!-- interactive: PagedAttention -->

Paging improves utilization but introduces metadata and block-management work.
Block size trades fragmentation against table overhead. The scheduler and cache
manager must agree on allocation and release; a leaked block becomes a
long-lived capacity defect.

## When should a waiting request be let in?

Static batching waits for every request in a batch to finish before replacing
it. Output lengths vary, so completed slots sit idle. Continuous batching
reforms the active batch at each decode iteration.

<!-- interactive: ContinuousBatching -->

The unit of scheduling is now one token step:

```text
select active requests
ensure each has KV capacity
run one decode step
append tokens and KV state
finish or return each request to the queue
admit waiting work
```

Higher throughput can increase queueing latency. The scheduler therefore needs
an explicit objective: throughput under time-to-first-token and inter-token
SLOs, not tokens per second alone.

## When is guessing ahead worth the check?

Speculative decoding lets a smaller draft model propose several tokens. The
target model verifies them in one pass and accepts the longest matching prefix.

<!-- interactive: SpeculativeDecoding -->

Speedup depends on three quantities:

- draft cost;
- target verification cost;
- acceptance length.

A fast draft with poor acceptance can be slower than ordinary decoding. Measure
acceptance by request slice, because domain, temperature, and prompt style can
change it substantially.

The target distribution remains authoritative. Speculation changes execution,
not the model's intended output distribution.

## How much precision can you give up?

Quantization reduces weight memory and bandwidth by representing values with
fewer bits. The decision is not “which format is smallest.” It is which
combination preserves required quality on the deployed workload.

Keep the axes separate:

- weight-only versus weight-and-activation quantization;
- post-training quantization versus quantization-aware training;
- calibration corpus coverage;
- kernel support on the target hardware;
- model footprint, throughput, and latency;
- accuracy and outlier slices.

A smaller checkpoint that falls back to a slow kernel is not a serving win.
Benchmark the complete runtime.

## What should the server do when it is full?

Before accepting a request, estimate:

```text
prompt tokens
maximum generation tokens
KV blocks required
current active batch
queue delay
deadline or priority
```

Rejecting or queueing early is safer than admitting work that will force
mid-generation eviction. Capacity policies should state which requests may be
preempted and whether partial output is valid.

For mixed workloads, prefill and decode can be separated onto different
workers. This improves specialization but adds transfer, routing, and failure
boundaries. Use disaggregation only after phase-specific measurements show a
real imbalance.

## Which number tells you the service is healthy?

The minimum serving dashboard reports distributions, not averages:

- time to first token;
- inter-token latency;
- end-to-end latency;
- output tokens per second;
- queue delay;
- active requests and KV utilization;
- prefix-cache hit rate, if used;
- OOM, eviction, cancellation, and error rates.

Slice by prompt length, output length, model, and priority. A good median with a
bad long-context tail violates the user contract even if aggregate throughput
improves.

The request trace should join admission, scheduling, model execution, and
finish reason. Otherwise the owner of a latency spike cannot be identified.

## Sub-lessons that measure instead of naming

The sections above name the techniques and give the arithmetic behind them.
Each sub-lesson takes one and runs it, which is the difference between knowing
a technique exists and knowing what it is worth on a specific card.

| Read this | When you need to decide | It returns |
|---|---|---|
| [graph execution](01-graph-execution/) | whether the card is working or waiting between tokens | a profile that says which of three bottlenecks you have, and roughly 3x from removing launch overhead |

Techniques named above and not yet measured — quantization, speculative
decoding, latency under load — stay named until a run record exists for them.

## Run the working path

[Mission 01, serving](../../missions/01-language-model-agent/05-serve/) joins a
checkpoint to a minimal paged-KV engine and records the runtime behavior.
Readable components explain the mechanisms; a run must still name model,
runtime, hardware, load shape, and measurements.

This chapter can establish correct allocation and scheduling on a bounded
workload. It does not establish production capacity, multi-tenant isolation, or
a latency SLO without a representative load test.

## Check your mental model

1. Why is decode often memory-bound while prefill is compute-heavy?
2. Which architecture parameter directly changes KV-cache size?
3. What invariant does paged allocation preserve?
4. Why can continuous batching improve throughput but hurt one request's
   latency?
5. When does speculative decoding become slower than ordinary decoding?

## Next

The output is a service with traces and SLO candidates. Continue to
[evaluation](../evaluation-observability/) to decide whether the served system,
including its harness and decoding configuration, is actually better.

Primary references: vLLM and PagedAttention, continuous batching work,
speculative decoding, FlashAttention, and modern inference runtimes such as
vLLM, SGLang, TensorRT-LLM, and llama.cpp.

Which of those to reach for, and what each is actually good at, is in
[the serving landscape](LANDSCAPE.md) — the readable engine you learn the
mechanisms from, mapped against the production engines that implement them.
