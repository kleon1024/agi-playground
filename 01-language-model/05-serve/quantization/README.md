---
status: verified
level: applied
base: scratch
verified: 2026-07-30
label: Quantization
---

# Does a smaller model decode faster?

**Question:** [graph execution](../graph-execution/) balanced the decode step at 1.05x
host-to-device and pointed at what comes next: "decode streams every weight once per token, so
halving the bytes should halve the time. The reason it usually does not is a kernel boundary
rather than a bandwidth one." This chapter tests that prediction directly, on the same model, the
same card.

**Before this:** [graph execution](../graph-execution/), for the profiling method this chapter
reuses and the balanced step this chapter starts from.

You will finish able to quantize a model's weights to INT8 by hand, verify the result with a check
that actually tells you something (greedy exact match does not), and read a profile that explains
why a 2.79x smaller model can still decode slower.

The decision quantization presents is never "which format is smallest". It is which combination of
these axes preserves the quality the deployed workload needs, and these axes move independently:

- weight-only versus weight-and-activation quantization;
- post-training quantization versus quantization-aware training;
- how well the calibration corpus covers the real input distribution;
- kernel support on the target hardware;
- model footprint, throughput, and latency;
- accuracy on the outlier slices, not only the average.

This chapter fixes five of those and varies one — weight-only INT8, post-training, on one card —
because the last axis is the one that decides the answer here, and a smaller checkpoint that falls
back to a slow kernel is not a serving win. Benchmark the complete runtime, never the file size.

## Shrink the weight, not the activation

`core/quantize.py` quantizes every attention and SwiGLU `nn.Linear` per output channel: for row `i`
of a weight matrix, `scale[i] = max(|w_i|) / 127`, and the stored value is
`round(w_i / scale[i])` clamped to an int8. Per-channel, not per-tensor — a single outlier row
would otherwise force every row's scale down to keep that one row representable, quietly clipping
the rest. The tied token embedding and output head stay fp32; quantizing a matrix used for both
input lookup and output projection is a separate technique this chapter does not take on, and
those two layers are 14.4% of the model's parameters, so this measures most of it, not all.

Run the footprint command and watch what quantizing the other 85.6% actually buys:

```
quantized-layer bytes:  fp32 301,989,888  ->  int8 75,829,248  (3.98x)
whole-model bytes:      before 352,791,552  ->  after 126,554,112  (2.79x)
```

`forward` dequantizes on every call — `weight_i8.float() * scale[:, None]`, then an ordinary
`F.linear` — the honest, naive path, and the one the prediction above is about.

## Check correctness, then find out the check was wrong

Run `verify` before trusting anything downstream. The first result is alarming:

```
fp32 vs int8 greedy tokens over a full generation: 1/64 match
```

Read the second line before concluding the quantizer is broken:

```
first-position logits: KL(fp32||int8)=0.0027 nats, cosine similarity=0.99975, top-1 token agrees: False
```

The two distributions sit at cosine similarity 0.9997 — nearly identical — and the single argmax
token still flips on the very first position. It flips because the top two logits there are close
(measured separately: 7.72% versus 6.44% probability), and 8-bit rounding error, about 3.2% mean
relative per weight, is large enough to cross a gap that size. Once one token differs,
autoregressive decoding conditions every later position on a different prefix than the reference
did, so the divergence compounds into near-total disagreement by token 64 — from a quantizer that
barely perturbed the distribution it started from.

**Greedy exact match is therefore the wrong correctness gate for quantization.** `bench` and
`verify` both check the distributional agreement at the first position instead — cosine similarity
above 0.99 and KL below 0.05 nats — and only report a speed number if that gate passes. It did.

## Bench it: the naive path is slower

```
configuration                    tok/s   vs eager fp32
eager, fp32                      129.1            1.00x
eager, int8 weight-only           97.8            0.76x
CUDA graph, fp32                 373.8            2.90x
CUDA graph, int8                 322.8            2.50x
```

A model 2.79x smaller decodes slower in both regimes: 0.76x eager, 0.86x under CUDA-graph replay
(322.8 / 373.8). The prediction from the previous chapter held.

## Profile it: where the extra time actually goes

```
                        self CPU/step   self CUDA/step
eager, fp32                  8.920 ms        1.312 ms
eager, int8 weight-only     11.455 ms        1.771 ms
```

Device time went **up** 35%, not down. Dequantizing materializes a full-width fp32 tensor before
the matmul reads it, so the kernel that reads weights from HBM now runs *in addition to* an
elementwise multiply-and-cast the fp32 path never pays — smaller bytes on disk, more work at
runtime. Host time rose too, because that dequant is one more distinct kernel launch per `Linear`,
and [graph execution](../graph-execution/) already established that launches, not arithmetic,
set the pace of this decode step. Quantization did not touch the actual bottleneck; it added to
it.

Both paths through one `Linear`, side by side — the shorter column is the larger
model:

<!-- interactive: QuantizedDecodePath -->

## Does a real library kernel do better?

`prod/torchao_quantize.py` applies the identical INT8 weight-only scheme through torchao's
`Int8WeightOnlyConfig`, which dispatches to a real int8 GEMM (`torch.ops.aten._int_mm`) instead of
dequantizing to fp32 first:

```
configuration                    tok/s   vs eager fp32
eager, fp32                      130.5            1.00x
eager, torchao int8               88.6            0.68x
```

Slower still — 0.68x against the hand-rolled version's 0.76x. No root cause was profiled for
torchao specifically; the most likely explanation, stated as a hypothesis and not measured here,
is per-call tensor-subclass dispatch overhead that does not amortize at this model's small
per-layer matmul sizes and batch-1 decode. A real fused kernel is not a substitute for the
question this chapter actually answers: is the bottleneck bandwidth. It is not, at this scale, and
no implementation of the same technique fixes a bottleneck it was never aimed at.

## What this does not establish

- **That INT8 weight-only quantization never helps.** It helps when decode is genuinely
  bandwidth-bound — a larger model, a larger batch, where AI = B (arithmetic intensity, from the
  [serving chapter](../)) sits closer to the
  ridge point and bytes moved actually gates the step. This model at batch 1 is nowhere near that
  regime.
- **That activation quantization, or a fused int8 kernel written for this exact architecture,
  would fail the same way.** Only weight-only quantization through two dequant-based paths was
  measured.
- **Anything about output quality beyond one KL/cosine snapshot.** The correctness gate proves the
  distributions are close at one position; it says nothing about long-generation quality or a
  downstream task score.

## Reproduce it

```bash
cd 01-language-model/05-serve/quantization/core
python quantize.py footprint --checkpoint <ckpt.pt>
python quantize.py verify    --checkpoint <ckpt.pt>
python quantize.py bench     --checkpoint <ckpt.pt> --max-new-tokens 128
python quantize.py profile   --checkpoint <ckpt.pt> --steps 50
cd ../prod && PYTHONPATH=../core python torchao_quantize.py bench --checkpoint <ckpt.pt>
```

Commands, hardware, and every number above:
[`runs/2026-07-30-quantization-bench.md`](runs/2026-07-30-quantization-bench.md).

## Check your mental model

**1. The int8 model's logits sit at cosine similarity 0.9997 to fp32, and greedy decoding still
   disagrees on 63 of 64 tokens. Reconcile those two numbers.**

<details>
<summary>Answer</summary>

Both numbers are true at the same time because they're measuring different
things. Cosine similarity 0.9997 says the *entire distribution* barely
moved — quantization perturbed it only slightly. But greedy decoding only
cares about which single logit is largest, and at the very first position the
top two logits were already close (7.72% vs. 6.44% probability). The
roughly 3.2% mean relative rounding error from 8-bit weights is small in an
absolute sense, but it's large enough to cross a gap that size and flip the
argmax. Once that first token differs, autoregressive decoding conditions
every later step on a different prefix than the reference — so a barely-moved
distribution at each step compounds into near-total disagreement by token 64.
The quantizer isn't broken; greedy exact match is measuring compounding
argmax flips, not distributional closeness.

</details>

**2. Device time went up after quantization, not down. What operation is responsible, and why does
   it run on every forward call instead of once?**

<details>
<summary>Answer</summary>

Dequantization — `weight_i8.float() * scale[:, None]` — materializes a
full-width fp32 tensor before the matmul can read it, on every `Linear` call.
That's a whole elementwise multiply-and-cast kernel that the original fp32
path never had to pay for, plus its own separate kernel-launch overhead in a
decode step that graph execution already proved is launch-bound, not
bandwidth-bound. It runs every call rather than once because the weights are
stored as int8 permanently between calls — the entire point of quantizing was
to keep the smaller footprint at rest, so dequantizing once and caching an
fp32 copy would just recreate the original memory cost this technique was
supposed to avoid.

</details>

**3. Under what condition would this exact technique actually deliver a speedup?**

<details>
<summary>Answer</summary>

When decode is genuinely bandwidth-bound rather than launch-bound — a larger
model, a larger batch, where arithmetic intensity (AI = B, from the serving
chapter) sits closer to the ridge point and the bytes moved through memory
actually gate the step's time. This model at batch 1 is nowhere near that
regime: its bottleneck is kernel-launch count, and shrinking the bytes on
disk does nothing to that bottleneck — it can only help once bytes moved is
the thing actually limiting the step.

</details>

**4. torchao's real int8 kernel was slower than the hand-rolled dequant version. What does that rule
   out as this model's bottleneck, and what does it not rule out?**

<details>
<summary>Answer</summary>

It rules out memory bandwidth as this model's bottleneck at this scale — even
a real fused int8 GEMM (`torch.ops.aten._int_mm`, no dequant-to-fp32 step)
came in slower than eager fp32, so the problem clearly isn't "too many bytes
moved," confirming the launch-bound diagnosis from the previous chapter. It
does *not* rule out that torchao's specific dispatch mechanism has its own
unmeasured per-call overhead (tensor-subclass dispatch that may not amortize
at this model's small per-layer matmul sizes and batch-1 decode) — the
chapter states that explicitly as an unmeasured hypothesis, not a
conclusion. It also doesn't rule out that a kernel purpose-built and fused
for this exact architecture could behave differently; only two
existing dequant-based paths were actually measured here.

</details>

## Next

The step is now proven launch-bound at this scale, and a technique aimed at bandwidth cannot fix
that — the remaining lever is [why concurrency
pays](../why-concurrency-pays/): batching multiple
requests raises arithmetic intensity directly, which is the axis this chapter's bottleneck actually
lives on.

Primary references: Dettmers et al., *LLM.int8()* (2022), for per-channel weight quantization at
scale; the torchao project documentation for `Int8WeightOnlyConfig` and its int8 GEMM dispatch.
