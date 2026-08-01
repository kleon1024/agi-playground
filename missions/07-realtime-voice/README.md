---
status: draft
level: applied
label: Real-time voice
---

# Does the KV cache care whether the tokens are words or sound?

**Question:** every other mission in this repository moves text tokens
through a served transformer with a KV cache, paged allocation, and
continuous batching. A voice interface needs the same thing — turn input
into output fast enough to feel live — but the tokens are chunks of sound.
Does the serving mechanism already built for text just work, or does audio's
chunk structure demand something new?

**The artifact this mission follows** is one short audio clip: a waveform in,
a discrete token sequence through a from-scratch codec, and a reconstructed
waveform out, decoded one chunk at a time instead of all at once.

## Why this mission exists

[Platform / serving](../../platform/serving/) built and measured a KV cache,
paged allocation, and continuous batching against text — the currency of
every other mission here. Those mechanisms are described in terms general
enough to sound modality-free: a cache of past keys and values, indexed by
position, freed when a request finishes. Nothing in that description
mentions text specifically.

This mission is the check on that claim. Building a small audio codec and
pointing the existing decode loop at its token stream is cheap compared to
building a new serving engine from scratch — and if it does not just work,
finding out exactly where it breaks is more useful than assuming it would.

## What gets measured

Two things that trade against each other, same shape as every other
mission's baseline pair:

**Offline vs. streaming**, holding the model and codec fixed. The offline
pass sees the whole clip before producing anything; the streaming pass
commits to one chunk at a time. The gap between them — in reconstruction
quality and in wall-clock — is what streaming actually costs, isolated from
everything else.

**This pipeline vs. a hosted API**, named and dated rather than assumed. A
toy codec trained here is not expected to win on quality; the point of
naming a real hosted baseline is to be honest about the size of that gap
rather than let a bare percentage stand in for it.

**Reconstruction quality** (a computable distance between the reconstructed
and reference waveform) is reported beside **per-chunk decode latency**, p50
and p95 — never a single average, matching
[platform/serving](../../platform/serving/)'s own latency-distribution rule,
since a good median with a bad tail still breaks a real-time contract.

## What is genuinely new here

The KV-cache, paged-allocation, and continuous-batching code is imported
directly from
[`platform/serving/01-graph-execution/core/`](../../platform/serving/01-graph-execution/),
not reimplemented — the same cross-mission import pattern mission 01 stage 06
uses for its harness. The only new code this mission needs is at the boundary
that code has never seen: a codec that turns a waveform into the discrete
token sequence the serving loop already knows how to schedule, and back
again.

<!-- interactive: RealtimeVoicePipeline -->

Neural audio codecs that turn waveforms into a discrete token vocabulary a
language model can be trained over trace to SoundStream (Zeghidour et al.,
2021) and were popularized for real-time use by EnCodec (Défossez et al.,
2022) -- both use a residual/vector-quantization bottleneck conceptually
identical to this stage's single-codebook VQ, at a far larger scale.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Audio codec](00-audio-codec/) | how does a waveform become a discrete token sequence, and what does that cost in quality? | verified |
| [01 — Streaming decode](01-streaming-decode/) | does the existing KV-cache mechanism work unchanged for audio tokens? | verified |
| [02 — Report](02-report/) | what does streaming cost in latency, and what does it buy or lose against the offline pass? | verified — MET |
| [03 — Real speech and network](03-real-speech-and-network/) | does the same codec architecture and the same KV cache hold on real speech, over a real network? | verified |
| [04 — Multi-speaker](04-multi-speaker/) | does the fix that escaped collapse for 1-2 speakers still work at 10? | verified |

[Stage 00](00-audio-codec/) built a small conv encoder / vector-quantization
/ conv decoder codec, trained on synthetic tone-sequence clips (no real
speech, no license needed, trivial provenance). Its first training attempt
collapsed to a silence-matching local minimum with the codebook stuck on 1-2
codes; raising the learning rate and training longer escaped it. The result
decisively beats both required naive baselines — reconstruction MSE 0.0111
against 0.325 (silence) and 0.300 (mean-signal) — with healthy, non-collapsed
codebook usage (34 of 64 codes used). Full trace in
[its run record](00-audio-codec/runs/2026-07-31-codec-training.md).

[Stage 01](01-streaming-decode/) trained a causal Transformer over the
codec's own token vocabulary, importing `Config`/`Transformer`/`KVCache`
directly from mission 01's serving engine — no line of that file changed.
Naive (full-recompute) and cache-based generation produced identical token
sequences across 30 held-out clips (max logit gap 1.19e-05, matching this
repo's own established tolerance for the same check on text). The cache's
latency benefit was invisible at this mission's native 48-token clip length
but reappeared clearly at a 500-step stress test (naive's tail ran 6.9x
slower than its start; cached stayed flat) — the same growing-vs-flat
divergence mission 01's own serving chapter documents for text, now shown
for a different discrete-token modality. No CUDA GPU was available in this
environment, so every number is CPU wall-clock, a real deviation from
`mission.yaml`'s "local GPU lane" framing. Full numbers in
[its run record](01-streaming-decode/runs/2026-07-31-streaming-decode.md).

[Stage 02](02-report/) held both results against `mission.yaml`'s
acceptance bar and printed `MET` — this mission's first `MET` verdict among
the three fully-built missions this session (05 and 06 both closed `NOT
MET`). The codec and the LM-completion pathway both beat both required naive
baselines, the KV-cache decode path is provably identical to full recompute
rather than merely similar, and the latency gap is reported at two scales
rather than assumed from one. The report is explicit that this is an easier
bar than mission 05 or 06 set out to clear — "does a proven mechanism
transfer unchanged" is a different, lower bar than "does training produce a
policy that beats a strong baseline" — not evidence this mission was more
rigorously built. Full verdict in
[its run record](02-report/runs/2026-07-31-outcome-report.md).

[Stage 03](03-real-speech-and-network/) retrained the identical codec
architecture — no change — on LibriSpeech `dev-clean` (Panayotov et al.,
2015; CC BY 4.0), 1-2 speakers. At stage 00's own step count the codec
reproduced stage 00's collapse story but did not escape it in time
(codebook stuck at 1 of 64 codes); a controlled sweep showed the fix is
specifically more steps at the same learning rate, not a higher one, and at
2000 steps all three seeds escaped cleanly, beating both naive baselines by
roughly 2x. The KV-cache mechanism held on this real-speech token
vocabulary too (max logit gap 2.8e-05, matching stage 01's own tolerance).
This stage also ran the mission's first real network measurement — a
round trip over this repository's documented Tailscale link
([`infra/local-4090.md`](../../infra/local-4090.md)), independently
confirmed live and measured at p50 9.7ms / p95 42.5ms over 200 round trips,
layered on top of, not merged with, stage 01's local decode latency. Full
numbers in
[its run record](03-real-speech-and-network/runs/2026-08-01-real-speech-and-network.md).

[Stage 04](04-multi-speaker/) reran stage 03's exact fix — 2000 steps,
`lr=1e-3`, no architecture change — on a balanced 10-speaker LibriSpeech mix
instead of 1-2. All three seeds still beat both naive baselines (no full
collapse), but the tight, consistent codebook health stage 03 found at 1-2
speakers (51-63 of 64 codes, ~52-53% margin over silence, all three seeds
within a narrow band) breaks down into strong seed-dependence at 10 speakers
(18-63 of 64 codes, 4.3%-38.2% margin) — the same fix keeps the codec from
failing outright, but no longer reliably converges to a well-utilized
codebook. The KV-cache mechanism held regardless (max logit gap 2.45e-05,
same order of magnitude as every prior stage). Full numbers in
[its run record](04-multi-speaker/runs/2026-08-01-multi-speaker.md).

Per [the mission contract](../../reference/standards/mission-contract.md), this
contract is declared before any stage is built, so the baseline and metric
above cannot be chosen after seeing which ones flatter a result.

## What this will not prove

The codec and dataset are toy-scale by construction, so nothing here says
anything about production speech quality or true full-duplex operation — the
loop runs one direction at a time. Multi-speaker robustness is only
partially tested: stage 03 uses 1-2 speakers, stage 04 extends this to 10 of
the corpus's 40+ dev-clean speakers, and neither is the full corpus. Nothing
here diagnoses *why* stage 04's escape became seed-dependent, only that it
did. Stage 03 adds a real network round trip, but only over this
repository's own home Tailscale link — a DERP-relayed hop on this sandbox's
network path — which does not generalize to arbitrary internet paths or a
direct (non-relayed) connection. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
