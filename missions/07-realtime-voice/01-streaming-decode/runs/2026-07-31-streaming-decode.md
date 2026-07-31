# Streaming decode over audio tokens, reusing engine.py's KV cache unmodified

## Command

```bash
cd missions/07-realtime-voice/01-streaming-decode/core
uv run --group torch python streaming_decode.py \
  --codec-steps 600 --lm-steps 800 --n-eval-clips 30 --prompt-len 16 \
  --latency-stress-len 500 --seed 0
```

Apple silicon laptop, macOS 15.6.1, CPU only (`torch.cuda.is_available()` is
`False` in this environment -- no CUDA GPU lane was available to run this on,
a real deviation from `mission.yaml`'s "local GPU lane" framing for
`latency_budget`, stated plainly rather than assumed away). Repository HEAD
at time of run: `c5b6f15`. Wall-clock: 189.1s (codec retrain + LM training +
30-clip eval + 500-step stress test).

## What ran

Retrained stage 00's exact codec recipe in-process (600 steps, same
architecture/hyperparameters/seed, converging to the same eval MSE stage 00
recorded). Encoded all 512 train and 100 eval clips into their real 64-token
sequences, prefixed each with a `BOS` token (id 64, one past the codec's own
64-entry codebook), and trained a 4-layer causal Transformer -- `Config`/
`Transformer` imported directly from
[`engine.py`](../../../01-language-model-agent/05-serve/core/engine.py),
unmodified -- for 800 steps of next-token cross-entropy (loss 4.14 -> 0.087).

For 30 held-out eval clips: primed the LM with the first 16 of 64 real
codec tokens, generated the remaining 48 two ways -- `generate_naive`
(engine.py's own full-recompute reference) and a cache-based generator built
directly from `KVCache`/`_forward_with_cache`/`build_rope_cache` (the same
building blocks `KVCacheEngine.generate()` itself calls; called directly
here since the wrapper doesn't expose per-step timing or logits). **No line
of `engine.py` was changed.**

## Correctness: identical, not just similar

Following the exact methodology in this repository's own
`tests/test_decode_correctness.py` -- compare **logits**, not generated
token ids, since an id-level match can pass trivially on a degenerate model
that only ever repeats its input:

```
max logit gap across all 30 clips: 1.19e-05
mean logit gap:                    5.27e-06
token sequences matched: 30/30 clips
```

The gap is the same order of magnitude as the repo's own established
tolerance for this exact comparison on text (`TOL = 2e-5` in
`tests/test_decode_correctness.py`). The KV-cache decode path produces the
same result as full recomputation for this audio-token vocabulary, to the
same numerical precision it does for text -- unmodified.

## Latency: no visible gap at the clip's native 48-token length, a clear one at 500

```
native scale (48 completion steps):
  naive:  early p50=1.46ms  late p50=1.57ms   (barely grows)
  cached: early p50=1.15ms  late p50=1.04ms   (flat, roughly matches naive)

stress test (500 arbitrary-token steps, timing only -- not a quality claim):
  naive:  first-10 p50=1.43ms   last-10 p50=9.81ms   (6.9x slower)
  cached: first-10 p50=1.15ms   last-10 p50=1.50ms   (roughly flat)
```

At this mission's actual clip length (48 tokens), fixed per-step
Python/tensor overhead dominates and the cache's real advantage does not
show up -- naive and cached are statistically indistinguishable. Stretched
to 500 steps (arbitrary token ids, matching how `engine.py`'s own
`_bench_naive`/`_bench_kvcache` benchmark uses `list(range(n))` rather than
real content), the same flat-vs-growing divergence this repository's own
[`05-serve/README.md`](../../../01-language-model-agent/05-serve/README.md)
documents for text tokens reappears for audio tokens: naive grows roughly
linearly with position, cached stays flat. The mechanism transfers; its
benefit is real but only visible once sequences are long enough for it to
matter, exactly as expected from the O(t) vs O(1) per-step cost argument
`engine.py`'s own docstring makes.

## Quality: the LM's completion beats both naive baselines, well short of oracle

```
LM completion (16 real tokens -> 48 generated):  MSE 0.2581
oracle (all 64 real tokens, sanity check):        MSE 0.0113
silence baseline:                                 MSE 0.3251
mean-signal baseline:                             MSE 0.3001
```

Given only the first quarter of a clip's real tokens (0.25s of 0.512s), the
trained audio-token LM's greedy completion decodes to a waveform closer to
the true continuation than either naive baseline -- a real, if modest,
capability. The oracle row is a sanity check, not a target: decoding the
clip's own real remaining tokens (no LM involved) reproduces stage 00's
already-established reconstruction quality almost exactly (0.0113 here vs
0.0111 in stage 00, the small difference from a fresh codec retrain under
an identical but re-run seed), confirming the retrained codec matches stage
00's original within noise.

## What this run establishes

The KV-cache decode loop mission 01 built for text transfers to a discrete
audio-token vocabulary with **zero code changes** and **zero measured
correctness cost** (logits match to float32 precision) -- a clean, real
answer to this mission's central question. Its latency benefit is real but
scale-dependent: invisible at this mission's native 48-token clip length,
clearly present (6.9x slower naive tail) once sequences reach 500 steps.
The audio-token LM itself has learned a real, partial completion capability
(beats both naive reconstruction baselines) well short of oracle quality.

## What this run does not establish

No CUDA GPU was available in this environment to run the "local GPU lane"
mission.yaml's `latency_budget` names; every number above is CPU wall-clock.
Nothing about the paged/continuous-batching layer specifically (`ContinuousBatchingEngine`)
-- only the single-sequence `KVCache` path was exercised here. Nothing about
real speech, longer utterances beyond 64 tokens, or multi-speaker audio.
