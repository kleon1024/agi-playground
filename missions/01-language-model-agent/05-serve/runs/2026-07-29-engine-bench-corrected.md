# Serving engine benchmark, re-measured after the causal-masking fix

This supersedes [`2026-07-28-engine-bench.md`](2026-07-28-engine-bench.md). The
engine that produced those numbers had a correctness bug in its cached
attention, so both cached engines were doing less work than they should have
been and the throughput columns were optimistic. Same commands, same hardware,
same checkpoint, corrected engine.

## Why the earlier numbers were wrong

`_cached_attention` called
`scaled_dot_product_attention(..., is_causal=True)`. PyTorch builds that mask
top-left — `tril` of a `(T_q, T_k)` matrix. Prefill has `T_q == T_k`, so it was
correct. A decode step has `T_q == 1` against `T_k == pos + 1`, where top-left
alignment leaves exactly one key unmasked: **position 0**. Every decode step in
both cached engines attended to the first token of the prompt and nothing else.

Two consequences, and the second is why this record exists:

1. Generated text was wrong. Greedy decoding with attention pinned to one key
   produces the same token forever. The earlier record's own caveat — "greedy
   decoding of `range(64)` as a prompt produces token sequences, not answers" —
   is what let this pass unnoticed, because nobody was reading the output.
2. **It was also faster.** A causal mask over one query and N keys lets the
   kernel skip almost all of the attention work, so the bug flattered exactly
   the column the chapter draws its conclusion from, and flattered it more at
   longer sequences where there was more work to skip.

The fix is `causal_lower_right(T, start_pos + T)`, which is the bottom-right
alignment a decode step needs and reduces to `is_causal` when the shapes are
square. `tests/test_decode_correctness.py` now compares both cached paths
against a full recompute, on logits rather than on generated ids.

## Command

```bash
cd missions/01-language-model-agent/05-serve/core
python engine.py bench --checkpoint <ckpt.pt> \
    --prompt-len 64 --max-new-tokens <N> --num-requests <R>
```

Swept twice: `N` over 32/64/128/256/512 at `R=8`, then `R` over 1/2/4/8/16 at
`N=128`. Greedy decoding, no `torch.compile`, no CUDA graphs.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Windows, reached over Tailscale |
| torch | 2.13.0+cu130 |
| Checkpoint | the 88,197,888-parameter stage 03 chat model |
| Cost | $0 (local lane) |

## Result 1: generation length

Single request for the first two engines; `paged + continuous` ran 8.

| New tokens | naive tok/s | KV cache tok/s | speedup | naive peak | KV cache peak | paged tok/s |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 104.7 | 126.6 | 1.21x | 375.1MB | 392.0MB | 121.7 |
| 64 | 112.3 | 126.3 | 1.12x | 380.5MB | 393.0MB | 112.8 |
| 128 | 117.5 | 123.8 | 1.05x | 391.9MB | 395.6MB | 110.4 |
| 256 | 119.7 | 120.6 | 1.01x | 418.0MB | 404.0MB | 108.0 |
| 512 | 132.8 | 122.2 | **0.92x** | 483.5MB | 433.5MB | 104.2 |

**The KV cache's advantage shrinks as generation gets longer, and by 512 tokens
the cache is slower than recomputing everything.** That is the opposite of what
the asymptotics predict and a sharper version of the earlier record's finding,
which had the speedup merely failing to grow.

The naive column is the control. It never touches `_cached_attention`, so the
fix could not move it — and it did not: 99.6/120.3/123.7/123.1/130.8 before
against 104.7/112.3/117.5/119.7/132.8 now, run-to-run noise. The KV-cache
column moved a lot, and moved most where the bug was skipping most work:
140.7 to 122.2 at 512 new tokens.

Why the cache can lose. Each decode step it runs is one token wide, so it issues
several hundred tiny kernel launches over weights it must read regardless. The
naive path issues a similar number of launches per step but each covers the
whole sequence, so it gets more arithmetic out of every launch — and the longer
the sequence, the better that trade gets for it. Notice the naive column *rises*
from 104.7 to 132.8 as sequences lengthen, which is the signature: it is not
being limited by the quadratic work it is redoing.

That is a launch-rate problem rather than an arithmetic problem, and
[`platform/serving/01-graph-execution/`](../../../../platform/serving/01-graph-execution/)
profiles it directly: 513 launches per decode step, host time 6.87x device time.

Memory behaves as designed. Past 256 new tokens the naive path's peak exceeds
the cached one, because it re-materialises activations for the whole sequence
every step while the cache holds only keys and values.

## Result 2: concurrency

`paged + continuous`, 128 new tokens per request, 64-token prompts.

| Concurrent requests | aggregate tok/s | wall-clock | peak memory |
|---:|---:|---:|---:|
| 1 | 110.6 | 1.157s | 376.9MB |
| 2 | 117.6 | 2.177s | 387.0MB |
| 4 | 111.9 | 4.576s | 396.6MB |
| 8 | 111.6 | 9.172s | 417.3MB |
| 16 | 114.1 | 17.949s | 459.1MB |

**Unchanged in kind: aggregate throughput is flat and wall-clock is linear.**
Sixteen concurrent requests take 15.5x as long as one. Concurrency buys nothing
here, for the reason the earlier record gave and this one does not repeat:
`ContinuousBatchingEngine.step()` loops over running requests in Python and
issues one forward pass each, so there is no single kernel across sequences for
the fixed per-step cost to amortise against. The scheduling policy is real; the
fused kernel that makes it pay is what `prod/vllm_serve.py` has.

Peak memory grows about 5MB per additional concurrent sequence, because pages
are handed out on demand rather than reserved per request at maximum length.

## What this run does not establish

- **That the KV cache is not worth it.** It establishes that at batch 1 on this
  hardware, below 512 generated tokens, its arithmetic saving is smaller than
  what it costs in launches. The asymptotics are real and this scale does not
  reach them.
- **That the 512-token inversion holds past 512.** One point beyond the
  crossover is a crossover, not a trend. Longer sweeps were not run.
- **Anything about latency percentiles.** Every number is aggregate throughput
  on a synthetic `range(prompt_len)` prompt: no time-to-first-token, no
  inter-token distribution, no queueing.
- **Anything about quality.** The outputs are now correct in the sense of
  matching a full recompute exactly, which is what
  `tests/test_decode_correctness.py` asserts. That is not the same as being
  good text, and nothing here evaluates the text.
