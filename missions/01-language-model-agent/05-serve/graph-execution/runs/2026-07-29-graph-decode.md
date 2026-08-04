# Profiling a decode step, and replacing it with a CUDA graph

Two measurements on the same checkpoint and card: a profile that says what the
decode step is actually waiting on, and a benchmark of what removing that wait
is worth.

## Command

```bash
cd missions/01-language-model-agent/05-serve/graph-execution/core
python graph_decode.py profile --checkpoint <ckpt.pt> --steps 50
python graph_decode.py bench   --checkpoint <ckpt.pt> --max-new-tokens 128 --repeat 15
```

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Ubuntu 22.04.3, reached over Tailscale |
| torch | 2.13.0+cu130 |
| Checkpoint | the 88,197,888-parameter stage 03 chat model, fp32 weights and cache |
| Shape | 64-token prompt, batch 1, cache sized 1024, greedy decoding |
| Total GPU time | under 10 minutes |
| Cost | \$0 (local lane) |

Both engines are correct: `bench` refuses to report a speedup until the graphed
decoder has reproduced the eager decoder's tokens exactly, and it printed
`identity check: 64/64 tokens match eager` on the run recorded here.

## Result 1: the step is launch-bound

50 decode steps, prefill excluded from the profiler window so every figure is
per decode step and nothing else.

| | eager | CUDA graph replay |
|---|---:|---:|
| host time per step | 9.103 ms | 2.954 ms |
| device time per step | 1.324 ms | 2.807 ms |
| host / device | **6.87x** | 1.05x |
| `cudaLaunchKernel` per step | 513, at 7.36us each | none — one replay |
| host time spent in launches | 188.9 ms of 455.1 ms (41.5%) | — |
| verdict | launch-bound | balanced |

**The GPU was busy 15% of the time.** Every decode step asked the host to issue
513 kernel launches, at 7.36 microseconds each, to run 1.324 milliseconds of
arithmetic. Launch calls alone account for 41.5% of host time; the rest is the
Python and dispatch that gets to them.

This is what [stage 05](../../)
inferred from a flat throughput curve and called "a fixed per-step cost". The
cost is real and now has a name and a number: it is the rate at which work can
be *issued*, not the rate at which it can be done.

## Result 2: what a graph is worth

128 new tokens per round, 15 rounds, median with the round-to-round spread.
Prefill is inside the timed region — a caller wants tokens from a prompt, not
tokens from a warm cache.

| configuration | tok/s | ms/token | round spread | vs eager |
|---|---:|---:|---|---:|
| eager (`engine.py`) | 121.7 | 8.216 | 110.3-128.7 | 1.00x |
| eager, device-side argmax | 130.2 | 7.681 | 115.0-136.0 | 1.07x |
| CUDA graph replay | 372.8 | 2.683 | 367.4-374.6 | **3.06x** |

Re-run three times over the session, the graph speedup came out at 2.92x, 3.05x
and 3.06x, against eager medians of 128.2, 122.7 and 121.7. The baseline itself
drifts about 5% between runs, so the honest headline is **roughly 3x**.

**The middle row is not a result.** Removing the `int(argmax)` host round-trip
looks like a 1.07x win, but its 115.0-136.0 spread overlaps eager's
110.3-128.7 almost entirely. That one synchronisation is not what was costing
the time; it had to go for the graph to be capturable, not because it was
expensive.

**The graph replay is 15x more stable than eager**: a 1.9% spread against 17%.
Taking the host out of the inner loop takes the host's scheduling jitter with
it, which matters more for tail latency than the median does.

## The trade this measures

A captured graph needs fixed shapes, so the graphed step attends over the
**whole** 1024-entry cache every time and masks what generation has not reached
yet. At position 70 it does the arithmetic for 1,024 keys instead of 70.

That shows up exactly where it should: device time per step went **up**, 1.324
to 2.807 ms, 2.12x more work on the GPU. Wall-clock still fell by 3x. On a step
that was idle 85% of the time, buying fewer launches with more arithmetic was a
good trade — and the profile after the change says why it stops there. At 1.05x
host to device the step is balanced, so the next win has to come from the
kernels themselves rather than from how they are issued.

## Result 3: the compiler, asked for the same thing

```bash
cd missions/01-language-model-agent/05-serve/graph-execution/prod
python compile_decode.py --checkpoint <ckpt.pt> --max-new-tokens 128 --repeat 15
```

Same fixed-shape step, same identity check, one `torch.compile` call instead of
the hand-written capture. Measured in its own process, so the eager baseline
differs from Result 2 by the usual few percent.

| configuration | tok/s | round spread | vs eager |
|---|---:|---|---:|
| eager | 130.8 | 110.4-134.9 | 1.00x |
| hand-rolled CUDA graph | 373.6 | 296.3-374.3 | 2.86x |
| `torch.compile(mode="reduce-overhead")` | 322.4 | 315.7-324.4 | 2.47x |

First compiled call, including tracing and codegen: 12.9 seconds.

**`reduce-overhead` did not use CUDA graphs at all here**, and said so:

```
[__cudagraphs] skipping cudagraphs due to mutated inputs (5 instances). Found from :
  File ".../core/graph_decode.py", line 131, in _step
    self.tok.copy_(nxt.view(1, 1))
```

The five static buffers the step mutates in place — token, position, step
index, generated ids, and the KV cache — are precisely what Inductor's
cudagraph pass refuses to capture, since a caller holding a reference to any of
them would observe silent corruption. So its 2.47x is kernel fusion alone:
fewer and larger kernels, attacking the same launch bottleneck by a different
route, and landing within 14% of the explicit capture without being told
anything about the algorithm.

## What this run does not establish

- **That 3x transfers to other shapes.** Batch 1, an 88M model, a 1024-entry
  cache. The fixed-shape mask costs more as the cache grows and less as the
  batch grows; a larger model does more arithmetic per launch and has less to
  gain. This is the launch-bound corner of the space, which is where graphs
  help most.
- **That the fixed-shape cost is acceptable in production.** Sizing capture for
  the maximum is why real engines bucket batch sizes and capture several graphs,
  and it is in direct tension with paged attention's dynamic block tables.
  Neither was measured here.
- **Anything about quality.** The identity check proves the graphed decoder
  emits the same tokens as the eager one. Both were checked against a full
  recompute at the logit level in `tests/test_decode_correctness.py`. Neither
  fact says the text is good.
- **That the compiler cannot close the gap.** Result 3 shows it declining to
  capture *this* code, whose in-place buffer mutation is exactly what its safety
  check rejects. A step written to avoid that mutation might well get captured
  and match. That variant was not written or measured.
