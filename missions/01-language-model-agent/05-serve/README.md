---
status: verified
verified: 2026-07-28
base: scratch
label: Serving
---

# What is the model actually doing between tokens?

**Question:** you have a trained checkpoint and a loop that calls it. Generating
one token takes a few milliseconds and the model is 88M parameters, which is
nothing. So where is the time going, and which of the things you could change
would actually move it?

Training spends compute once. Serving spends it on every prompt for as long as
the model is deployed, so an engine that is 3x slower than it needs to be is a
permanent 3x tax rather than a one-time cost. This chapter follows one decode
step down to the hardware and rebuilds it twice: once to stop recomputing what
it already knows, and once to stop reserving memory it will not use. The next
chapter asks the question those two cannot answer — why serving sixteen
requests should not cost sixteen times as much as serving one.

The running example is `core/engine.py`, which contains the same model served
three ways so each can be timed against the one before it: `generate_naive`
feeds the whole sequence through the model every step, `KVCacheEngine` keeps
what it already computed, and `ContinuousBatchingEngine` holds that cache in
pages. None of them touches
[`02-pretrain/core/model.py`](../02-pretrain/core/model.py) — its `forward()`
has no cache argument and never gets one, because that would thread `past_kv`
through every training call site for a capability training never uses. The
engine reimplements the block loop against the trained model's own
`nn.Linear`, `RMSNorm`, and `SwiGLU` submodules instead.

## Why is a decode step slow when the arithmetic is trivial?

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

The `d_in`/`d_out` terms cancel: the answer depends only on batch size and
precision. At bf16 that is `AI ≈ B`. Every accelerator has a **ridge point**,
the intensity at which compute and bandwidth finish together, set by its own
FLOPs-to-bytes ratio — for a datacentre card of the last few years, on the
order of 150 FLOPs per byte. Decoding one token for one request sits at
`AI ≈ 1`, two orders of magnitude below it. **Prefill** is the opposite: it
processes the whole prompt as one large matmul, so `B` is the prompt length and
the intensity lands near the ridge. Prefill is compute-bound; decode is not,
and no amount of faster arithmetic will change that.

So the card is not computing; it is streaming weights. Two consequences follow,
and the rest of this chapter is the first one. **Do less streaming per token**
— which is what a cache and then paging are for. The second consequence,
**share each stream across more requests**, is what the next chapter is about:
a batch of 64 concurrent decode steps has `AI≈64`, still memory-bound but 64x
further from idle than one request alone.

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
fitting alongside the weights on one card and turning requests away. GQA is a
pretraining-time decision that exists entirely to buy inference-time headroom.

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

The same indirection buys two things this lesson does not implement:
**copy-on-write**, where sequences sharing a prefix point at the same physical
blocks until they diverge, and **prefix caching**, where blocks are hashed by
content so a repeated system prompt skips recomputing its KV entirely.
`PagedKVCache.read` also gathers a sequence's blocks into a contiguous tensor
for readability, where a production kernel fuses that gather into the attention
computation — real performance traded for a much shorter implementation.

Add several requests below and compare contiguous reservation with block
allocation. The important observation is not only higher utilization: freed
blocks become reusable by an unrelated request immediately.

<!-- interactive: PagedAttention -->

## What these two mechanisms bought

Measured on the stage-03 chat checkpoint, one request, greedy decoding:

| New tokens | 32 | 64 | 128 | 256 | 512 |
|---|---:|---:|---:|---:|---:|
| Naive, tok/s | 104.7 | 112.3 | 117.5 | 119.7 | 132.8 |
| KV cache, tok/s | 126.6 | 126.3 | 123.8 | 120.6 | 122.2 |
| Speedup | 1.21x | 1.12x | 1.05x | 1.01x | **0.92x** |

**The speedup shrinks as generation gets longer, and by 512 tokens the cache
loses.** That is backwards. Recomputing the whole prefix every step is
quadratic work, so the gap should widen with length — instead it closes and
then inverts.

Read the naive row again, though, because it is the one that explains this. It
*rises* from 104.7 to 132.8 as sequences get longer. An engine limited by the
quadratic work it redoes cannot speed up when you give it more of that work to
redo. So neither engine is limited by arithmetic, and something else is setting
the pace for both.

That something is the rate at which decode steps can be *issued*. Each cached
step is one token wide: a few hundred tiny kernel launches over weights that
must be read whatever the sequence length. The naive path issues launches at a
similar rate, but each one covers the entire sequence, so it extracts more
arithmetic per launch — and that trade improves the longer the sequence gets,
until it overtakes the cache. Stage 02 saw the same effect from the training
side, where `torch.compile` bought 1.76x by fusing memory-bound work and
removing launch overhead.

Memory does behave as predicted: past 256 new tokens the naive path's peak
exceeds the cached one, because it re-materialises activations for the whole
sequence every step while the cache holds only keys and values. Full sweep in
[`runs/2026-07-29-engine-bench-corrected.md`](runs/2026-07-29-engine-bench-corrected.md).

Hold on to that diagnosis. It is the premise of the next chapter, and
[`platform/serving/01-graph-execution/`](../../../platform/serving/01-graph-execution/)
puts a profiler on it rather than leaving it as the best available story: 513
kernel launches per decode step, host time 6.87x device time, and a 3.06x
speedup from removing the launches without touching the arithmetic.

## What this chapter does not establish

- **That the KV cache is not worth it.** It establishes that its benefit is
  invisible below roughly 512 generated tokens at batch 1 on this hardware. The
  asymptotics are real; this scale does not reach them.
- **Anything about latency percentiles.** Every measurement here is aggregate
  throughput on a synthetic prompt. No time-to-first-token, no inter-token
  distribution, no behaviour under load.
- **Anything about quality.** Greedy decoding of `range(64)` produces token
  sequences, not answers. Both cached engines are now verified to reproduce a
  full recompute's logits exactly
  (`tests/test_decode_correctness.py`), which is correctness, not quality.
  They were not always: the first version of this chapter benchmarked an engine
  whose every decode step attended to position 0 alone, and it went unnoticed
  precisely because a throughput sweep never reads its own output. The numbers
  above are the re-measured ones, and the earlier record is kept and marked
  rather than quietly replaced.

## Reproduce it

```bash
cd missions/01-language-model-agent/05-serve/core
python engine.py bench --checkpoint ../../03-sft/ckpt/ckpt.pt \
    --device cuda --prompt-len 64 --max-new-tokens 128
```

Omitting `--checkpoint` falls back to a random-init model of the same shape, so
the code path runs with no GPU and no trained weights at all.

## Check your mental model

1. A decode step is a matrix-vector product against every weight in the model.
   Why does that make it memory-bound rather than compute-bound, and what
   changes when the batch grows?
2. The KV cache turns quadratic work into linear work, and bought 1.08x at 512
   tokens. Reconcile those two statements.
3. Dropping from 12 KV heads to 4 divides the cache by three. Why is that
   decided during training rather than at serving time?
4. Paging fixes two distinct kinds of waste. Name both, and say which one a
   larger block size makes worse.

## Next

**Continue the mission at [stage 06 — agent](../06-agent/)**, which wraps this
serving layer in a tool loop.

First, though: [why concurrency should be free](why-concurrency-pays/) takes
the flat 105-135 tokens/second above and asks what happens when sixteen people
send a prompt at the same time. The answer this engine gives is wrong, in a way
that is worth 89x — and stage 06 issues one request per step, so the cost model
it inherits comes from that chapter rather than this one.

