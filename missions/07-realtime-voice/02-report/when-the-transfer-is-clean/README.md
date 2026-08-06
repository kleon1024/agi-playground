---
status: verified
level: applied
base: scratch
label: When the transfer is clean
verified: 2026-08-06
---

# The transfer that needed no new serving code

**Question:** [mission 07's report](../) returned MET — the KV-cache serving
mechanism built for text transferred to audio tokens unchanged. This
chapter reads the committed stage 00/01 JSONs and lays out what the verdict
actually rests on.

**Before this:** [mission 07's outcome report](../) and its recorded verdict.

## The five lines, read

The run ([record](runs/2026-08-06-transfer-read.md)) reads the committed
JSONs:

| line | number |
|---|---|
| codec beats both naive baselines | MSE 0.0111 vs silence 0.3251 / mean-signal 0.3001 |
| offline-vs-streaming quality gap | max logit gap 1.19e-05 across 30 clips (zero) |
| latency at native length | invisible (48 steps) |
| latency at 500 steps | naive tail grows 6.9x, cached 1.3x |
| change to reused serving code | zero lines |

## Two readings

**The transfer is clean because the mechanism was already the same.** The
cache preserves output exactly — logit-level gap 1.19e-05 across all 30
clips — and buys latency only at length: 6.9x naive tail growth versus 1.3x
cached at 500 steps, invisible at the native 48-token clip. The two results
are one claim: the KV cache is a length-conditional optimization that never
changes what the model outputs.

**Zero changed serving code is the sharpest line.** Mission 07's question
was whether a mechanism built and measured for text transfers to a new
discrete-token modality. The answer is in the diff count: `engine.py`'s
Config/Transformer/KVCache were imported unmodified. A transfer that needed
no rewrite is evidence the mechanism was modality-neutral, which is the
claim the mission exists to test.

## Evidence boundary

The committed stage 00/01 JSONs (one seed each, synthetic tone-sequence
clips, CPU lane); it reads those artifacts and does not re-run. The latency
numbers are CPU wall-clock, a real deviation from `mission.yaml`'s GPU-lane
framing, stated in the stage's own report.

## Check your mental model

Answer each before opening it.

**1. The cache shows no latency benefit at 48 steps. Why is the verdict
still MET?**

<details>
<summary>Answer</summary>

Because the acceptance line is "latency reported at two scales," not
"cache is always faster." At the mission's native clip length the cache is
invisible; at 500 steps it prevents the 6.9x naive tail growth. Reporting
both is the honest version of the claim — the cache is a length-conditional
optimization, and MET follows from measuring it at the scale where it
matters, not from a single flattering number.

</details>

**2. Why does the zero quality gap matter more than the latency win?**

<details>
<summary>Answer</summary>

Because a cache that changed output would make the latency win worthless —
speeding up a decode that produces different tokens is not a serving
improvement, it is a different model. The logit-level gap (1.19e-05) is
what lets the latency numbers be read as a pure win, and it is checked at
logit level rather than token-id level so identical tokens cannot hide a
confidence shift.

</details>

## Next

Back to [mission 07's report](../), or to
[the cache-pays detour](../../01-streaming-decode/when-the-cache-pays/)
which reads the same divergence from stage 01's side.
