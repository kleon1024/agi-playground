---
status: draft
base: scratch
---

# What makes generation fast enough to use?

**Goal:** take the checkpoint the earlier stages produced and make it fast to
talk to — built by hand, in three layers, so each layer's win is something you
can measure rather than take on faith.

Training spends compute once. Serving spends it every single time someone
sends a prompt, for as long as the model is deployed — which is why a serving
engine that is 3x slower than it needs to be is a permanent 3x tax, not a
one-time cost. The three ideas in this lesson — a KV cache, paged memory for
that cache, and a scheduler that rebalances it every step — are the entire
reason a modern serving stack looks nothing like `model.generate()` in a loop.

## What you build

`core/engine.py` — three engines, each built directly on the one before, so
each can be benchmarked against its predecessor:

1. **Naive generation** (`generate_naive`) — feed the whole sequence so far
   through the model at every step. Correct, and it recomputes every prior
   token's key/value projections on every new token.
2. **KV cache** (`KVCacheEngine`) — one sequence, one preallocated buffer per
   layer. Compute K/V for the prompt once, then for each new token only.
3. **Paged blocks + continuous batching** (`ContinuousBatchingEngine`) — the
   cache lives in fixed-size physical blocks addressed through a per-sequence
   block table, allocated on demand and freed on completion, wrapped in a
   scheduler that admits and evicts requests between every forward pass.

None of this touches [`02-pretrain/core/model.py`](../02-pretrain/core/model.py).
Its `forward()` has no cache argument and never gets one — that would mean
threading `past_kv` through every training call site for a capability
training never uses. Instead `engine.py` re-implements the block loop and the
attention math with a cache, calling straight into the trained model's own
`nn.Linear`/`RMSNorm`/`SwiGLU` submodules for every weight, and never calling
`Transformer.forward()` once a cache is in play. Comments in the file mark
exactly where and why.

`prod/vllm_serve.py` — converts the same checkpoint into a HuggingFace
`LlamaForCausalLM` checkpoint (our architecture is, module for module, a
Llama decoder — see the file's docstring for why the RoPE convention needs no
permutation trick) and serves it with vLLM, with comments on everything vLLM
adds beyond the toy engine.

## Why decode is memory-bandwidth-bound, not compute-bound

A single decode step is a matrix-vector product against every weight matrix
in the model: one query, projected through a `(d_in, d_out)` weight, once per
layer. For a linear layer, generating `B` tokens' worth of output from the
same weights costs `2 * B * d_in * d_out` FLOPs, but moving the weight matrix
from HBM to the chip costs `d_in * d_out * bytes_per_element` regardless of
`B` — the weights get read once and reused across whatever batch is in
flight. The ratio of those two, **arithmetic intensity**, is what a roofline
model uses to predict whether a workload is compute-bound or memory-bound:

```
AI = FLOPs / bytes ≈ (2 * B * d_in * d_out) / (d_in * d_out * bytes_per_element)
   = 2B / bytes_per_element
```

The `d_in`/`d_out` terms cancel — the result depends only on batch size and
precision. At bf16 (2 bytes/element), `AI ≈ B`. A GPU has its own ridge
point — the AI at which compute and bandwidth finish at the same time — set
by its own FLOPs-per-second-to-bytes-per-second ratio: an A100 (2020), for
instance, offers roughly 312 TFLOP/s bf16 against roughly 2 TB/s of HBM2e
bandwidth, a ridge point near **156 FLOPs/byte**. Decoding one token for one
request (`B=1`) sits at `AI≈1` — two orders of magnitude below that ridge.
The GPU spends nearly all of its time streaming weights out of HBM and almost
none of it computing; **prefill**, by contrast, processes the whole prompt as
one large matmul (`B` = prompt length), pushing `AI` up near or past the
ridge, which is why prefill is compute-bound while decode is not.

This is the architectural reason continuous batching (below) is the single
biggest throughput lever available: it does not reduce the bytes moved per
weight read, but it multiplies how much compute is extracted per byte moved,
by increasing the effective `B` the GPU sees on every forward pass. A batch
of 64 concurrent decode steps has `AI≈64` — still memory-bound on most
accelerators, but 64x further from idle than one request decoding alone.

## The KV cache: linear work instead of quadratic, and what it costs

Generating token `n+1` needs attention over tokens `1..n`. Once a token's key
and value vectors are computed, they never change — recomputing them on every
later step (what `generate_naive` does) is pure waste. The KV cache stores
each token's K/V the first time it's produced; a decode step then computes
K/V for only the new token and reuses the cache for everything before it,
turning a generation's total work from quadratic in sequence length to
linear.

The cache is not free. Per token, per layer, the memory needed is:

```
2 (K and V) x num_kv_heads x head_dim x bytes_per_element
```

multiplied by `num_layers x sequence_length x batch_size` for the total.
Plugged into this speedrun's own model
([`Config`](../02-pretrain/core/model.py), `n_layer=12`, `n_kv_head=4`,
`d_head=64`, `block_size=1024`), at bf16:

```
per token, per layer:  2 x 4 x 64 x 2 bytes        =  1,024 bytes  (1 KiB)
per token, all layers: 1,024 bytes x 12             = 12,288 bytes  (12 KiB)
full context (1024):  12,288 bytes x 1,024          ≈ 12.0 MiB per sequence
```

That number is exactly what `model.py`'s `param_report()` prints as `KV cache
per token`, and it is the number that mostly determines how many concurrent
sequences a serving system can hold at once — the weights are fixed and
comparatively small (this model is ~88M parameters, well under 200MB even in
fp32); the cache is what grows with every request and every token.

Change batch size and context length below before reading the architectural
fixes. This is the memory pressure GQA, paging, and scheduling must absorb.

<!-- interactive: KVCacheGrowth -->

### Why GQA shrinks it 3x

`n_head=12` but `n_kv_head=4` — this model was built with grouped-query
attention specifically to buy this. Full multi-head attention gives every
query head its own KV head; GQA shares one KV head across a group of query
heads (here, groups of `12/4 = 3`), so the cache scales with `n_kv_head`, not
`n_head`. Recomputing the numbers above under full MHA (`n_kv_head=12`):

```
per token, all layers: (2 x 12 x 64 x 2) x 12       = 36,864 bytes (36 KiB)
full context (1024):   36,864 x 1,024                ≈ 36.0 MiB per sequence
```

Exactly 3x, matching `n_head / n_kv_head`. At 64 concurrent full-context
sequences that is 768 MiB versus 2.25 GiB — the difference between the cache
fitting comfortably alongside the weights on a single card and needing to
turn requests away sooner. GQA is a pretraining-time architecture decision
that exists entirely to buy inference-time headroom; see `model.py`'s own
docstring for the training-side half of that story.

## Paging: KV cache as OS-style virtual memory

`KVCacheEngine` reserves one buffer of `max_len` tokens per sequence,
up front, before knowing how many tokens the sequence will actually generate.
That wastes memory two distinct ways: a sequence that finishes after 20
tokens but was sized for 1024 leaves 1004 slots reserved and unusable for as
long as it's alive (**internal fragmentation**); two sequences reserved at
different sizes can't lend each other unused space even when memory sits
free between them (**external fragmentation**). Production serving systems
reported 60–80% of KV cache memory wasted this way before PagedAttention.

The fix is the fix operating systems already found for exactly this problem:
stop reserving contiguous ranges, and allocate **fixed-size blocks** instead
(`BlockAllocator`, 16 tokens each here — vLLM's original default), tracked
per sequence by a **block table** mapping logical position to physical
block — a page table, precisely. Blocks come from a shared free list on
demand as generation proceeds, and go back to that free list the instant a
sequence finishes (`ContinuousBatchingEngine.step`, right where a sequence is
marked `done`). Waste drops from most of the reservation to a few percent —
at most one partially-used block per sequence, not one entire
maximum-length reservation.

The same indirection buys two things this lesson doesn't implement but is
worth knowing: **copy-on-write**, where two sequences sharing a prefix (e.g.
parallel samples, beam search) point at the same physical blocks until they
diverge; and **prefix caching**, where blocks are hashed by content so a
repeated system prompt across many requests skips recomputing its KV
entirely. `PagedKVCache.read` in `core/engine.py` gathers a sequence's blocks
into a contiguous tensor for readability — production kernels fuse that
gather directly into the attention computation instead of materializing a
copy, which is real performance left on the table here in exchange for a much
shorter implementation.

Add several requests below and compare contiguous reservation with block
allocation. The important observation is not only higher utilization: freed
blocks become reusable by an unrelated request immediately.

<!-- interactive: PagedAttention -->

## Continuous batching: a scheduling change, not a bigger batch

Static batching waits for a fixed group of requests, runs the whole batch
until every sequence in it finishes, and only then admits new ones — so a
short request that finishes early sits idle, holding its slot, while the
batch waits on whatever request is longest. **Continuous batching**
(Orca's "iteration-level scheduling") instead makes the admit/evict decision
*every forward pass*: the moment a sequence finishes, its slot and its blocks
free up, and a waiting request can be admitted into the very next iteration.
`ContinuousBatchingEngine.step()` is exactly this: `_admit()` pulls in
whatever waiting requests current free blocks allow, one step runs for every
currently running request, and anything that just finished is evicted and
its blocks returned before the function returns. The batch's *composition* —
not any fixed size parameter — is what changes on every call.

Watch the same requests under static and iteration-level scheduling. No model
or batch-capacity parameter changes; only the admission decision moves from the
end of a batch to every forward pass.

<!-- interactive: ContinuousBatching -->

The engine here loops over admitted requests one at a time in Python; a
production engine fuses that loop into one batched kernel call over ragged
sequence lengths (the fused paged-attention kernels `prod/vllm_serve.py`
gets access to by switching engines). The scheduling logic — what gets
admitted, what gets evicted, when — is identical either way; only how the
resulting batch is executed on the GPU differs.

## Reproducing

```bash
# from missions/01-language-model-agent/05-serve/core

# benchmark all three engines against a checkpoint (falls back to a random-init
# model of the same shape if --checkpoint is omitted, so this runs with no GPU
# and no trained weights at all — useful for confirming the code path works)
python engine.py bench --checkpoint ../../02-pretrain/ckpt/ckpt.pt \
    --device cuda --prompt-len 128 --max-new-tokens 128 --num-requests 16

# generate from a prompt (already-tokenized ids) with the KV cache engine alone
python engine.py generate --checkpoint ../../02-pretrain/ckpt/ckpt.pt \
    --prompt-ids 3 7 1 9 2 --max-new-tokens 32

# from ../prod: convert the checkpoint to HF Llama format, then serve with vLLM
python vllm_serve.py convert ../../02-pretrain/ckpt/ckpt.pt ./hf-checkpoint
python vllm_serve.py serve ./hf-checkpoint --prompt "Once upon a time"
# or, the real production entrypoint:
vllm serve ./hf-checkpoint --port 8000
```

All three engines were checked for exact agreement — naive, KV-cached, and
paged+continuous-batched all produce identical greedy token sequences on a
random-init model of this architecture, including under deliberately tight
block budgets that force the scheduler to admit and evict mid-run — and the
HF conversion was verified to produce bit-identical logits (`0.0` max
absolute difference) against `model.py`'s own forward pass. No throughput,
latency, or memory numbers are published here: this repo has no GPU
available, and printing numbers this lesson cannot measure would violate the
run contract (`../../../standards/lesson-and-run-contract.md`). Run the
`bench` command above on a GPU to produce them; the benchmark is built to
produce exactly the naive-vs-KV-cache-vs-paged comparison this lesson
describes.

## Exercises

1. **Watch the crossover.** At `--prompt-len 8 --max-new-tokens 8`, the KV
   cache barely matters — the quadratic term hasn't grown yet. Sweep
   `--max-new-tokens` up (64, 256, 1024) and find where naive generation's
   wall-clock stops looking linear.
2. **Break the block budget on purpose.** Pass a `num_blocks` to
   `ContinuousBatchingEngine` too small to admit every submitted request at
   once, and print `engine.waiting` each step. Confirm requests queue and
   drain rather than crash, and that finished requests' blocks are reused by
   the ones behind them.
3. **Measure the paging tax.** `PagedKVCache.read` materializes a contiguous
   copy every attention call; time how much of `paged+continuous`'s total
   wall-clock that gather accounts for versus the matmuls themselves.
4. **Recompute the GQA table for a checkpoint you actually trained**, not the
   default `Config()`, if your run changed `n_kv_head` or `n_layer` — the
   formula in this README is general; the numbers in it are this model's
   defaults specifically.
5. **Convert and diff.** Run `vllm_serve.py convert`, then load the result
   with `transformers.LlamaForCausalLM.from_pretrained` directly (no vLLM
   needed) and compare its logits against `model.py`'s own forward pass on
   the same input ids — confirm the `0.0` diff this README claims, on your
   own checkpoint.

## Next

[Stage 06 — agent](../06-agent/): once the model can be queried fast, it can
be queried repeatedly inside a loop — the next stage wraps this serving layer
in tool use and multi-step reasoning.
