---
status: verified
level: applied
base: scratch
label: When the cache pays
verified: 2026-08-06
---

# The KV cache on audio tokens: same answer, flat latency

**Question:** [stage 01](../) asks the mission's central question — does the
KV-cache serving mechanism built for text work unchanged for audio tokens?
The recorded answer has two halves: correctness (the two paths produce the
same tokens) and latency (how each degrades over a long stream). This
chapter reads both.

**Before this:** [stage 01's streaming-decode run](../) and its recorded
verdict.

## The contract, read

The analysis ([record](runs/2026-08-06-streaming-reading.md)) reads the
recorded correctness and the latency-stress table:

| path | first-10 p50 | last-10 p50 | degradation |
|---|---:|---:|---:|
| naive (recompute prefix) | 1.43ms | 9.81ms | 6.9x |
| cached (KV cache) | 1.15ms | 1.50ms | ~flat |

Correctness: naive and cached produce identical tokens on all 3 eval clips
(3/3 match).

## Two readings

**The cache is the same answer, not a different one.** Token-for-token, the
cached path reproduces the naive completion exactly — the KV cache is a
correctness-preserving speedup, which is the precondition for using it at
all. A cache that changed the answer would fail the mission's identity-check
discipline before latency ever mattered.

**The naive path's degradation is what kills real-time audio.** Over a
500-token stream, recomputing the whole prefix each step drives p50 from
1.43 to 9.81ms — 6.9x, and growing with stream length. The cached path
stays flat (1.15 to 1.50ms). An audio token is a chunk of sound, and a
voice interface generates hundreds of them; only the flat curve keeps the
stream inside the real-time budget, which is the mission's claim measured
on its own modality.

## Evidence boundary

The stage's recorded run (3 eval clips, one 500-token stress, seed 0). It
reads the correctness and latency the verdict rests on; it does not re-run
the decode, and it does not measure throughput under concurrency (the
serving stage's separate concern).

## Check your mental model

Answer each before opening it.

**1. Why must the cached path produce identical tokens to the naive one
before the latency win counts?**

<details>
<summary>Answer</summary>

Because a KV cache that changed the output would be a correctness bug that
happens to be faster — exactly the failure this mission's identity-check
discipline exists to catch. The cache stores the same keys and values the
naive path recomputes, so the tokens must match; only after that holds does
the latency comparison become a speedup rather than a different answer.

</details>

**2. The naive path is fine at 48 tokens (the eval clips) but degrades on
the 500-token stress. Why does the stress matter for audio?**

<details>
<summary>Answer</summary>

Because real audio streams are hundreds of tokens long — each token is a
chunk of sound, and a voice response is many chunks. The 48-token eval clips
never expose the naive path's quadratic recompute cost; the 500-token
stress shows it growing 6.9x, which is the regime a real-time interface
actually lives in. The stress is the honest test of whether the mechanism
scales to the modality's natural stream length.

</details>

## Next

Back to [stage 01's streaming decode](../../01-streaming-decode/), or to
[stage 02's report](../../02-report/) where the streaming-versus-offline
tradeoff is held against the mission's acceptance.
