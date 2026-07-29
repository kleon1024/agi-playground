---
status: verified
base: scratch
verified: 2026-07-29
label: Graph execution
---

# Is the card working, or waiting?

**Question:** an 88M model generates about 120 tokens per second at batch 1, and
that number barely moves whatever you do to the algorithm. The
[serving chapter](../../../missions/01-language-model-agent/05-serve/) measured
it, found the KV cache buying almost nothing, and named the culprit "a fixed
per-step cost". That is a hypothesis wearing a finding's clothes. This chapter
puts a profiler on one decode step, and then acts on what it says.

**Prerequisite:** that chapter's KV-cache engine, which is the code being
profiled here.

You will finish able to tell three bottlenecks apart from a profile — the host
cannot issue work fast enough, the device cannot read memory fast enough, the
device cannot compute fast enough — and to say why the standard fix for the
first one costs you arithmetic to buy back time.

## The one comparison that settles it

A PyTorch profile reports two totals that are easy to skim past. `Self CPU time
total` is how long the host spent getting work to the GPU: Python, dispatch, and
the `cudaLaunchKernel` calls themselves. `Self CUDA time total` is how long the
GPU spent running it.

If the second is larger, the GPU is the constraint and you should be looking at
kernels. If the first is larger, **the GPU spent part of the step idle, waiting
for a host that could not issue work quickly enough.** Nothing you do to the
arithmetic will help, because the arithmetic was never what you were waiting on.

Run it over 50 decode steps, prefill excluded so the numbers are per step:

```
eager (engine.py)
  self CPU time total       455.1 ms   ( 9.103 ms/step)
  self CUDA time total       66.2 ms   ( 1.324 ms/step)
  host / device              6.87x
  cudaLaunchKernel         25,650 calls (513/step, 7.36us each)
  time in launches          188.9 ms  (41.5% of host time)
  verdict: LAUNCH-BOUND — the host cannot feed the device
```

**The card was busy 15% of the time.** Each step asked the host for 513 kernel
launches to run 1.324 milliseconds of arithmetic, and the launch calls alone ate
41.5% of the host's time.

That is the "fixed per-step cost", identified. It is fixed because it depends on
the number of operations in a decode step — twelve layers times a handful of
projections, norms, and elementwise ops — and not on how much data each one
touches. At batch 1 with a small model, each kernel finishes in microseconds
while the launch that started it costs 7.36 microseconds. You are paying
courier fees on postcards.

This also explains a result the serving chapter could not: why its naive engine
*sped up* on longer sequences, from 104.7 to 132.8 tokens per second, and
eventually overtook the KV cache. The naive path issues launches at a similar
rate, but each covers the whole sequence rather than one token, so it gets more
arithmetic per launch — and that trade improves as sequences grow.

## Send the whole step at once

A CUDA graph records a sequence of launches once and replays the entire thing
with a single call. Five hundred and thirteen launches become one.

The catch is what "recordable" requires. A replay re-executes fixed kernels
against fixed memory addresses, so anything the host decides per step has to
stop being decided per step. A decode step breaks that three ways, and each fix
is a real constraint rather than a formality:

1. **`int(logits.argmax())` copies to the host** to build a Python integer, so
   the step stops dead mid-flight waiting for the device. The chosen token has
   to stay a device tensor.
2. **The position is a Python integer**, so `cache[..., pos:pos+1] = k` bakes a
   different destination into every step. It becomes a device tensor, written
   with `index_copy_`.
3. **The attention window grows every token**, and a graph records one shape.

Fix 3 is the one worth slowing down for, because it is not free. If the shape
cannot change, the step must attend over the *entire* preallocated cache every
time and mask the positions generation has not reached yet. At position 70 it
does the arithmetic for 1,024 keys instead of 70.

So the technique buys fewer launches by doing **more** arithmetic. On a step
that was idle 85% of the time, that should be a good trade. Whether it actually
is, is a measurement.

## What it bought

128 new tokens per round, 15 rounds, median and spread:

| configuration | tok/s | ms/token | round spread | vs eager |
|---|---:|---:|---|---:|
| eager | 121.7 | 8.216 | 110.3-128.7 | 1.00x |
| eager, device-side argmax | 130.2 | 7.681 | 115.0-136.0 | 1.07x |
| CUDA graph replay | 372.8 | 2.683 | 367.4-374.6 | **3.06x** |

Three things in that table, in order of how easy they are to get wrong.

**The middle row is not a result.** Removing the host round-trip looks like a
7% win, but its spread overlaps eager's almost entirely. That synchronisation
had to go for the step to be capturable — not because it was expensive.

**The speedup is about 3x, not 3.06x.** Re-run three times, it came out at
2.92x, 3.05x and 3.06x against eager medians that themselves drifted 5%. The
extra digit belongs to one run, not to the technique.

**The graph replay is 15x more stable than eager**: a 1.9% spread against 17%.
Removing the host from the inner loop removes its scheduling jitter too, which
matters more for tail latency than the median ever does.

And the cost this predicted shows up exactly where it should. Profiling the
replayed step:

| | eager | graph replay |
|---|---:|---:|
| host time per step | 9.103 ms | 2.954 ms |
| device time per step | 1.324 ms | **2.807 ms** |
| host / device | 6.87x | 1.05x |
| launches per step | 513 | one replay |

Device time went **up** by 2.12x — that is the masked-out arithmetic, paid in
full. Wall-clock still fell threefold. And at 1.05x the step is now balanced:
neither side is starving the other, so the next win has to come from the
kernels themselves rather than from how they are issued. The bottleneck did not
disappear; it moved, and the profile says where to look next.

## Does the compiler just do this?

`torch.compile(mode="reduce-overhead")` uses CUDA graphs underneath, so the
honest question is whether any of the above needed doing by hand.
`prod/compile_decode.py` runs the same fixed-shape step through it:

| configuration | tok/s | round spread | vs eager |
|---|---:|---|---:|
| eager | 130.8 | 110.4-134.9 | 1.00x |
| hand-rolled CUDA graph | 373.6 | 296.3-374.3 | 2.86x |
| `torch.compile` reduce-overhead | 322.4 | 315.7-324.4 | 2.47x |

The compiler got most of the way, for one line of code and a 12.9-second first
call. But read what it printed on the way:

```
skipping cudagraphs due to mutated inputs (5 instances)
  graph_decode.py:131 in _step: self.tok.copy_(nxt.view(1, 1))
```

**It declined to use CUDA graphs at all.** The static buffers the step mutates
in place — the token, the position, the step counter, the cache — are exactly
what its safety check refuses to capture, because a caller who reused one of
those tensors elsewhere would get silent corruption. So the 2.47x is kernel
fusion alone: fewer, larger kernels, attacking the same launch bottleneck by a
different route.

That is the useful shape of this comparison. The compiler is the right default
and gets most of the win blind. The remaining gap is available only to code
that can promise, as `core/` does by construction, that mutating those buffers
is safe.

## Run the working path

```bash
cd platform/serving/01-graph-execution/core
python graph_decode.py profile --checkpoint <ckpt.pt> --steps 50
python graph_decode.py bench   --checkpoint <ckpt.pt> --max-new-tokens 128
cd ../prod && python compile_decode.py --checkpoint <ckpt.pt>
```

`bench` refuses to print a speedup until the graphed decoder has reproduced the
eager decoder's tokens exactly. That check is not ceremony: the first working
version of this file was fast and wrong, because `capture()` rewound the
position counter after its warm-up but not the current token, so replay began
three tokens into a discarded continuation. A benchmark that never reads its
own output cannot tell you that.

Commands, hardware, and every number above:
[`runs/2026-07-29-graph-decode.md`](runs/2026-07-29-graph-decode.md).

## What this does not establish

- **That 3x transfers.** Batch 1, 88M parameters, a 1024-entry cache — the
  launch-bound corner of the space, where graphs help most. The fixed-shape
  mask costs more as the cache grows and less as the batch grows, and a larger
  model does more arithmetic per launch to begin with.
- **That capture is compatible with paged attention.** It is not, easily: a
  block table that changes per step is the dynamic addressing capture forbids.
  Production engines bucket batch sizes and capture several graphs. Neither was
  measured here.
- **Anything about quality.** The identity check proves the graphed decoder
  emits the tokens the eager one does; `tests/test_decode_correctness.py`
  proves the eager one matches a full recompute. Neither says the text is good.

## Check your mental model

1. A profile shows host time below device time. Which of the three fixes in
   this chapter is worth trying, and which are wasted effort?
2. The graphed step does 2.12x the arithmetic and finishes 3x sooner. What
   would have to be true of the eager step for that to be impossible?
3. Why is the device-side-argmax row in the benchmark not evidence that the
   host round-trip was cheap — and not evidence it was expensive either?
4. `torch.compile` refused to capture a graph over code written specifically to
   be capturable. What is its safety check protecting against?
5. The replayed step profiles at 1.05x host to device. What class of
   optimisation does that rule out next, and what class does it point to?

## Next

The step is balanced now, which means the remaining time is in kernels reading
weights. That points at quantization, and at a specific prediction to test:
decode streams every weight once per token, so halving the bytes should halve
the time. The reason it usually does not is a kernel boundary rather than a
bandwidth one — dequantising to full width and calling an ordinary matmul
materialises the wide weight anyway and adds the dequant on top. That chapter
is not written yet, and this one does not assume its result.

Two loose ends from the profile are worth naming. Batch 1 is the worst case for
launch overhead, and [why concurrency
pays](../../../missions/01-language-model-agent/05-serve/why-concurrency-pays/)
already measured what batching is worth on this engine. And nothing here
touched latency percentiles: every number above is a median over whole
generations, which is the wrong statistic for a server.

Primary references: NVIDIA, "CUDA Graphs" (2019), for the capture and replay
model; PyTorch, `torch.cuda.CUDAGraph` and `torch.compile` mode documentation.
