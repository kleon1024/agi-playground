---
status: verified
level: applied
base: scratch
verified: 2026-07-31
label: Streaming decode
---

# Does the KV cache built for text work unchanged for audio tokens?

**Question:** stage 00 turned a waveform into a 64-token discrete sequence.
This stage hands that sequence to
[mission 01's KV-cache decode loop](../../01-language-model-agent/05-serve/core/engine.py)
-- the exact same `Config`/`Transformer`/`KVCache` classes, unmodified -- and
checks whether the mechanism that was only ever tested against text tokens
produces the same answer, and the same speed profile, for a discrete-token
stream that has never been text at all.

**The artifact this stage produces** is one held-out clip's completion,
generated two ways from the same 16 real prefix tokens:

```
naive (full recompute) and cached (KV cache) generation of the same
48 remaining tokens -- identical, to a max logit gap of 1.19e-05, the same
order of magnitude as this repo's own established tolerance for this exact
comparison on text (tests/test_decode_correctness.py, TOL=2e-5)
```

**Before this:** [stage 00](../00-audio-codec/) built the codec that turns a
waveform into the 64-token sequence this stage's language model is trained
on.

## What is reused, and what is new

`core/audio_lm.py` imports `Config` and `Transformer` directly from
`engine.py` -- the identical classes mission 01's text pretraining and
serving use, with `vocab_size` set to the codec's 65-symbol vocabulary
(64 codes plus one `BOS` marker) instead of a BPE tokenizer's. `core/streaming_decode.py`
imports `KVCache`, `_forward_with_cache`, and `build_rope_cache` directly
from `engine.py` -- the same building blocks its own `KVCacheEngine.generate()`
wraps, called directly here because per-step timing and per-step logits
(what this stage needs to measure) are not something that wrapper exposes.
**No line of `engine.py` was changed.** The only new code this stage needed:
training an LM over a different (audio) token vocabulary, and a thin
timing/logit-capturing harness around functions that already existed.

## Correctness: checked on logits, not token ids

Following the exact methodology this repository's own
`tests/test_decode_correctness.py` uses for text -- and the exact reason it
gives for using logits rather than ids: an id-level match can pass trivially
on a degenerate model that only ever repeats its input, hiding a real bug
(the attention-mask alignment bug that test itself documents). Across 30
held-out clips, naive and cached generation produced identical token
sequences, with a max logit gap of 1.19e-05.

## Latency: the cache's benefit is scale-dependent, not automatic

```
native clip length (48 steps):  naive and cached are statistically indistinguishable
500-step stress test:            naive tail 6.9x slower than its own start; cached stays flat
```

At this mission's actual clip length, fixed per-step overhead swamps the
O(t)-vs-O(1) difference the cache exists to fix -- a real, honest finding,
not a bug. Stretched to 500 steps (arbitrary token ids, matching how
`engine.py`'s own benchmark measures throughput -- timing only, not a
quality claim), the same growing-vs-flat divergence
[mission 01's own serving chapter](../../01-language-model-agent/05-serve/README.md)
documents for text reappears here for audio tokens. Full numbers in
[`runs/2026-07-31-streaming-decode.md`](runs/2026-07-31-streaming-decode.md).

Naive (full-recompute) generation reruns attention over all prior positions
at each step -- total cost across `T` tokens is `O(1+2+...+T) = O(T^2)`, each
individual step more expensive as the sequence grows. Cached generation
reuses stored keys/values and only computes attention for the one new token
against the cache -- `O(T)` total, fixed cost per step. The real numbers
confirm this: at the 500-step stress test, naive's first-10-steps p50 is
1.43ms and its last-10-steps p50 is 9.81ms, a 6.9x slowdown; cached's is
1.15ms to 1.50ms, a 1.3x change, close to flat. At the mission's native
48-token clip length, cached decode's early p50 (1.15ms) is the same order
of magnitude as naive's early p50 (1.46ms) -- the mechanism is real, but too
short a sequence for the linear term to matter.

<!-- interactive: AudioLatencyDivergence -->

KV caching for autoregressive decoding is standard practice, formalized as a
systems problem by Orca (Yu et al., 2022) and vLLM's PagedAttention (Kwon et
al., 2023, the scheme `05-serve/graph-execution` itself models).

## Quality: real, partial completion capability

```
LM completion (16 real tokens -> 48 generated):  MSE 0.2581
oracle (all 64 real tokens):                      MSE 0.0113
silence baseline:                                 MSE 0.3251
mean-signal baseline:                             MSE 0.3001
```

Given only the first quarter of a held-out clip, the trained audio-token LM's
greedy completion beats both required naive baselines, but falls well short
of decoding the clip's own real remaining tokens -- an honest, bounded
capability, not a claim of solved audio continuation.

## Run it

```bash
cd missions/07-realtime-voice/01-streaming-decode/core
uv run --group torch python streaming_decode.py --n-eval-clips 30 --prompt-len 16 --latency-stress-len 500
```

CPU only -- no CUDA GPU was available in this environment, a real deviation
from `mission.yaml`'s "local GPU lane" framing, stated plainly rather than
assumed away. ~190s wall-clock, \$0 marginal cost.

## What this stage does not establish

No GPU-lane numbers; nothing about the paged/continuous-batching layer
specifically, only the single-sequence `KVCache` path; nothing about real
speech, longer utterances, or multi-speaker audio, per `mission.yaml`'s own
`does_not_prove`.

**Next:** stage 02 holds this result against `mission.yaml`'s acceptance bar
and reports a verdict.

A detour from here: [the KV cache on audio tokens: same answer, flat
latency](when-the-cache-pays/) — the recorded correctness (3/3 token match)
and the latency stress (naive 6.9x degradation vs cached flat) read as the
two halves of the mission's central claim.
