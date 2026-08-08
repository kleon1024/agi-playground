---
status: verified
level: foundation
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

The running example is `core/engine.py`, which serves the same model three ways
so each can be timed against the one before it: `generate_naive` feeds the whole
sequence through the model every step, `KVCacheEngine` keeps what it already
computed, and `ContinuousBatchingEngine` holds that cache in pages. None of them
touches [`02-pretrain/core/model.py`](../02-pretrain/core/model.py), whose
`forward()` has no cache argument and never gets one — the engine reimplements
the block loop against the trained model's own submodules instead.

## Why is a decode step slow when the arithmetic is trivial?

Follow one weight matrix through a decode step. Generating `B` tokens' worth
of output from one linear layer costs `2 * B * d_in * d_out` FLOPs, but moving
that weight matrix from HBM to the chip costs `d_in * d_out * bytes_per_element`
regardless of `B` — the weights are read once and reused across whatever batch
is in flight. Take the ratio of those two costs and you get **arithmetic
intensity**, the number a roofline model uses to predict whether a workload is
compute-bound or memory-bound:

```
AI = FLOPs / bytes ≈ (2 * B * d_in * d_out) / (d_in * d_out * bytes_per_element)
   = 2B / bytes_per_element
```

The `d_in`/`d_out` terms cancel: the answer depends only on batch size and
precision. At bf16 that is `AI ≈ B`. Every accelerator has a **ridge point**,
the intensity at which compute and bandwidth finish together — for a datacentre
card of the last few years, on the order of 150 FLOPs per byte. Decoding one
token for one request sits at `AI ≈ 1`, two orders of magnitude below it.
**Prefill** is the opposite: it processes the whole prompt as one large matmul,
so `B` is the prompt length and the intensity lands near the ridge. Prefill is
compute-bound; decode is not, and faster arithmetic will not change that.

So the card is not computing; it is streaming weights. Two consequences follow.
**Do less streaming per token** — a cache, then paging — is the rest of this
chapter. **Share each stream across more requests** is the next one: 64
concurrent decode steps reach `AI≈64`, still memory-bound but 64x further from
idle than one request alone.

## The KV cache: linear work instead of quadratic, and what it costs

Generating token `n+1` needs attention over tokens `1..n`. Once a token's key
and value vectors are computed, they never change — recomputing them on every
later step (what `generate_naive` does) is pure waste. The KV cache stores
each token's K/V the first time it's produced; a decode step then computes
K/V for only the new token and reuses the cache for everything before it,
turning a generation's total work from quadratic in sequence length to
linear.

The cache is not free. For this model
([`Config`](../02-pretrain/core/model.py): `n_layer=12`, `n_kv_head=4`,
`d_head=64`, `block_size=1024`) at bf16, it costs **12,288 bytes per token** —
12 KiB, or 12.0 MiB for one full-context sequence — which is exactly what
`model.py`'s `param_report()` prints. The derivation is in
[what a block costs](../../foundations/00-attention/what-it-costs/); what
matters here is that this, not the weights, decides how many concurrent
sequences a card can hold. The 88M weights are fixed and under 200MB even in
fp32. The cache grows with every request and every token.

Change batch size and context length below before reading the architectural
fixes. This is the memory pressure GQA, paging, and scheduling must absorb.

<!-- interactive: KVCacheGrowth -->

Three of those twelve KiB are a pretraining decision you are now collecting on.
`n_head=12` but `n_kv_head=4`, so the cache scales with the key-value heads and
not the query heads — full multi-head attention would cost 36 KiB per token and
36.0 MiB per full-context sequence instead.
[What a block costs](../../foundations/00-attention/what-it-costs/) derives
both figures from the architecture. At 64 concurrent sequences the difference is
768 MiB against 2.25 GiB: the cache fitting beside the weights on one card, or
requests being turned away.

## The cache you reserve is not the cache you use

Knowing what a sequence's cache costs does not tell you how to allocate it,
because a request does not know its own final length when it is admitted.
Reserve `max_len` for each one — which is exactly what `KVCacheEngine` does —
and a sequence that stops after 20 tokens sits on 1,004 unusable slots for as
long as it is alive. Production serving systems reported 60–80% of KV cache
memory wasted this way before PagedAttention.

`ContinuousBatchingEngine` fixes it with a page table, and
[paging the cache](paging-the-cache/) is that mechanism: the two distinct kinds
of fragmentation, why fixed-size blocks kill one of them outright, what block
size actually trades against, and the prefix sharing that only becomes
expressible once the cache has a unit smaller than a request.

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

That diagnosis is a story until someone profiles it.
[Graph execution](graph-execution/) does: 513 kernel launches per decode step,
host time 6.87x device time, and 3.06x from removing the launches without
touching the arithmetic.

## Three more things you could change, and what each is worth

The cache and the page table are two of the levers this stage owns. Three
others each get their own chapter, because each one is a claim that only a run
can settle — and two of the three come out against the technique on this
hardware, which is the reason they are worth reading rather than listing.

**[Graph execution](graph-execution/)** — *is the card working, or waiting?*
Profiles one decode step and names which of three bottlenecks you actually
have. Roughly 3x from removing launch overhead alone, arithmetic untouched.

**[Quantization](quantization/)** — *does a smaller model decode faster?* A
measured no at this batch size: INT8 shrinks the model 2.79x and is slower,
both by hand and through a real int8 kernel.

**[Speculative decoding](speculative-decoding/)** — *is a cheap draft's guess
worth the target's check?* A measured crossover. The identical draft
architecture flips from 1.58x speedup to 0.94x slowdown on training steps
alone, and both regimes stay byte-identical to plain greedy decoding.

**[When the cascade loses](when-the-cascade-loses/)** — *does a confidence
gate ever get slower than the expensive model it protects?* Yes, three ways,
measured: a low threshold accepts confident-but-wrong tokens (60% accepted,
18% right), a high threshold escalates everything and pays cheap plus
expensive per step (0.89-0.98x), and a hard expensive-call budget collapses
quality the moment the request outlasts it (13% match after the budget is
spent).

Techniques this stage names and has not measured — latency under sustained
load, prefill/decode disaggregation — stay named until a run record exists for
them.

## The fix and its trade

The fix is the sequence this chapter builds, and each step is a named trade.
The KV cache turns a generation's work from quadratic to linear — and at this
scale the benefit is invisible below roughly 512 generated tokens at batch 1,
where the cached engine actually *loses* (0.92x) because the bottleneck is
decode-step issue rate, not arithmetic: the naive path extracts more
arithmetic per launch as sequences grow, which is why its throughput *rises*
with length (104.7 to 132.8 tok/s). The page table stops reserving `max_len`
per request, which is what lets a card hold 64 sequences at all — 768 MiB of
cache beside the weights with GQA's 4 KV heads, against 2.25 GiB if the
pretraining had kept 12. And the three levers each get their own measured
verdict because each is a claim only a run can settle: graph execution buys
~3x by attacking launch count, quantization buys nothing at batch 1 because
decode here is not bandwidth-bound, speculative decoding crosses from a win
to a loss somewhere between 15.9% and 37.9% acceptance.

The trade is that every lever is aimed at one bottleneck and fails against
another. A technique that shrinks bytes (quantization) cannot fix a step
whose limit is how many kernels the host can launch; a technique that buys
more arithmetic per launch (CUDA graphs) pays 2.12x the device work to
remove the launch cost; and the memory fixes buy capacity at the price of
indirection (a block table per step) that the next chapter measures. The
deepest trade is architectural and decided in pretraining, not serving:
`n_kv_head=4` divides the cache by three because the model was trained that
way, and serving collects the bill on every request for the life of the
deployment — a decision made once, paid forever.

## Who owns the loop

- **The serving-infrastructure team** owns the engine and the levers: the
  cache, the page table, graph capture, batching — and the benchmark that
  refuses to report a speedup until the fast path reproduces the slow path's
  tokens exactly.
- **The model team** owns the decisions that fix cache cost at training time:
  `n_kv_head` and the block size are baked into the weights, so the 12-versus-
  36 KiB per token choice belongs to pretraining, not to serving.
- **The capacity and product team** owns the latency and cost budget the
  stage serves — time-to-first-token, tail latency, and the quality-versus-
  latency price of every lever, none of which a throughput number can decide.

## What this chapter does not establish

- **That the KV cache is not worth it.** It establishes that its benefit is
  invisible below roughly 512 generated tokens at batch 1 on this hardware. The
  asymptotics are real; this scale does not reach them.
- **Anything about latency percentiles.** Every measurement here is aggregate
  throughput on a synthetic prompt. No time-to-first-token, no inter-token
  distribution, no behaviour under load.
- **Anything about quality.** Greedy decoding of `range(64)` produces token
  sequences, not answers. Both cached engines now reproduce a full recompute's
  logits exactly (`tests/test_decode_correctness.py`) — correctness, not
  quality. They did not always: the first version of this chapter benchmarked an
  engine whose every decode step attended to position 0 alone, unnoticed because
  a throughput sweep never reads its own output. The numbers above are the
  re-measured ones, and the earlier record is kept and marked rather than
  quietly replaced.

## Reproduce it

```bash
cd 01-language-model/05-serve/core
python engine.py bench --checkpoint ../../03-sft/ckpt/ckpt.pt \
    --device cuda --prompt-len 64 --max-new-tokens 128
```

Omitting `--checkpoint` falls back to a random-init model of the same shape, so
the code path runs with no GPU and no trained weights at all.

## Check your mental model

1. A decode step is a matrix-vector product against every weight in the model.
   Why does that make it memory-bound rather than compute-bound, and what
   changes when the batch grows?

<details>
<summary>Answer</summary>

Arithmetic intensity is `AI = FLOPs / bytes ≈ 2B / bytes_per_element` — the
`d_in`/`d_out` terms cancel, so it depends only on batch size and precision.
Decoding one token for one request sits at `AI ≈ 1`, two orders of magnitude
below a datacentre card's ridge point of roughly 150 FLOPs per byte, which
means the card finishes the arithmetic long before it finishes streaming the
weight matrix from HBM — it's memory-bound. Growing the batch raises `B`
directly, which raises `AI` linearly: 64 concurrent decode steps reach `AI ≈
64`, still memory-bound but 64x further from idle than a single request,
because the same weight read now serves 64 requests' worth of arithmetic
instead of one.

</details>

2. The KV cache turns quadratic work into linear work, and *lost* at 512
   tokens. Reconcile those two statements.

<details>
<summary>Answer</summary>

Both are true because they're about different bottlenecks. The complexity
claim (quadratic vs. linear) is about *arithmetic* — and the chapter shows
neither engine is actually arithmetic-bound: the naive engine's throughput
*rises* with sequence length, which an engine limited by the quadratic work
it redoes could not do. The real bottleneck for both engines is the rate at
which decode steps can be issued — kernel-launch overhead. The naive path
issues launches at a similar rate but each covers the whole sequence,
extracting more arithmetic per launch as sequences grow, until that trade
overtakes the cache's launch-bound, one-token-wide steps. The asymptotic
argument is real; it just isn't reached at this scale, and the chapter says
so directly in "what this chapter does not establish."

</details>

3. Dropping from 12 KV heads to 4 divides the cache by three. Why is that
   decided during training rather than at serving time?

<details>
<summary>Answer</summary>

The key/value head count is an architectural choice baked into the weights
during training — it's not a knob a serving deployment can retune afterward
without retraining the model. The chapter frames the cost as "three of those
twelve KiB are a pretraining decision you are now collecting on": training
paid this trade once, and serving collects the payoff (or the cost) "on
every request for the life of the model." Since the choice is fixed by the
time serving begins, serving cares about it more than training does, even
though training is where the decision was actually made.

</details>

4. What does the naive engine's *rising* throughput rule out as the bottleneck?

<details>
<summary>Answer</summary>

It rules out redone quadratic arithmetic as the limiting factor. An engine
whose bottleneck were the quadratic work it recomputes every step could not
get *faster* as sequences grow longer and there's more of that work to redo
— throughput would fall, not rise, as the redundant computation piled up.
Instead it rises from 104.7 to 132.8 tok/s as sequences lengthen, which
means something other than arithmetic is setting the pace: the rate at
which per-token kernel launches can be issued, with longer sequences letting
the naive path extract more arithmetic per launch and thereby amortize the
fixed launch cost better.

</details>

## Next

**Continue the mission at [stage 06 — agent](../06-agent/)**, which wraps this
serving layer in a tool loop.

First, though: [why concurrency should be free](why-concurrency-pays/) takes
the flat 105-135 tokens/second above and asks what happens when sixteen people
send a prompt at the same time. The answer this engine gives is wrong, in a way
that is worth 89x — and stage 06 issues one request per step, so the cost model
it inherits comes from that chapter rather than this one.

Which engine to reach for once you stop writing your own, and what each is
actually good at, is in [the serving landscape](LANDSCAPE.md) — the readable
engine you learn the mechanisms from, mapped against the production engines
that implement them.
