---
status: draft
level: applied
label: Real-time voice
---

# Does the KV cache care whether the tokens are words or sound?

**Question:** every other path in this repository moves text tokens
through a served transformer with a KV cache, paged allocation, and
continuous batching. A voice interface needs the same thing — turn input
into output fast enough to feel live — but the tokens are chunks of sound.
Does the serving mechanism already built for text just work, or does audio's
chunk structure demand something new?

**The artifact this path follows** is one short audio clip: a waveform in,
a discrete token sequence through a from-scratch codec, and a reconstructed
waveform out, decoded one chunk at a time instead of all at once.

This is the voice path of
[the multimodal-generation topic](../README.md). It covers the three
capabilities a voice interface needs — recognition, generation, and
interaction — as one token stream, and the section below maps each
capability onto the stages that build its shared machinery.

## Three capabilities, one token stream

A voice interface is three capabilities sharing one discrete-token spine.
Recognition turns a waveform into tokens and then into text; generation
turns text into tokens and then into a waveform; interaction runs the loop
fast enough to feel live. The stages below do not train an ASR head or a TTS
head — those are declared scope in the topic's
[`mission.yaml`](../mission.yaml), deliberately not faked. What the stages
do build and measure is the shared spine all three heads would sit on, and
each capability's mapping is stated so the boundary is never blurred:

| Capability | What it needs | Where this path builds it |
|---|---|---|
| Recognition (speech to text) | a waveform → discrete token codec; a decoder over those tokens; real-speech robustness | [stage 00](00-audio-codec/), [stage 01](01-streaming-decode/), [stage 03](03-real-speech-and-network/) |
| Generation (text to speech) | the same codec reversed; a token decoder; streaming output | [stage 00](00-audio-codec/), [stage 01](01-streaming-decode/) |
| Interaction (dialogue) | a streaming loop with bounded per-chunk latency; multi-speaker stability | [stage 01](01-streaming-decode/), [stage 04](04-multi-speaker/) |

The recognition and generation heads themselves live in topic 01's
language-model stages — [the serving stage](../../01-language-model/05-serve/)
and [the agent stage](../../01-language-model/06-agent/) — which consume
whatever discrete token stream this path produces. What this path measures is
the token stream's cost and stability, which is the part every head shares.

## Why this path exists

[Topic 01's serving stage](../../01-language-model/05-serve/) built and measured a KV cache,
paged allocation, and continuous batching against text — the currency of
every other path here. Those mechanisms are described in terms general
enough to sound modality-free: a cache of past keys and values, indexed by
position, freed when a request finishes. Nothing in that description
mentions text specifically.

This path is the check on that claim. Building a small audio codec and
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
[the serving stage](../../01-language-model/05-serve/why-concurrency-pays/)'s own latency-distribution rule,
since a good median with a bad tail still breaks a real-time contract.

## What is genuinely new here

The KV-cache, paged-allocation, and continuous-batching code is imported
directly from
[`05-serve/graph-execution/core/`](../../01-language-model/05-serve/graph-execution/),
not reimplemented — the same cross-topic import pattern topic 01's agent
stage uses for its harness. The only new code this path needs is at the boundary
that code has never seen: a codec that turns a waveform into the discrete
token sequence the serving loop already knows how to schedule, and back
again.

<!-- interactive: RealtimeVoicePipeline -->

Neural audio codecs that turn waveforms into a discrete token vocabulary a
language model can be trained over trace to SoundStream (Zeghidour et al.,
2021) and were popularized for real-time use by EnCodec (Défossez et al.,
2022) -- both use a residual/vector-quantization bottleneck conceptually
identical to this stage's single-codebook VQ, at a far larger scale.

## Model lineage

The codec is a point on the neural-audio line — VQ-VAE, SoundStream, EnCodec,
DAC, and the codebook-collapse fixes. The
[open-source line behind realtime voice](lineage.md)
traces it.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Audio codec](00-audio-codec/) | how does a waveform become a discrete token sequence, and what does that cost in quality? | verified |
| [01 — Streaming decode](01-streaming-decode/) | does the existing KV-cache mechanism work unchanged for audio tokens? | verified |
| [02 — Report](02-report/) | what does streaming cost in latency, and what does it buy or lose against the offline pass? | verified — MET |
| [03 — Real speech and network](03-real-speech-and-network/) | does the same codec architecture and the same KV cache hold on real speech, over a real network? | verified |
| [04 — Multi-speaker](04-multi-speaker/) | does the fix that escaped collapse for 1-2 speakers still work at 10? | verified |
| [05 — Codebook reset](05-codebook-reset/) | does a standard dead-code reset fix the seed-dependent codebook health stage 04 found? | verified |
| [06 — Which mechanism did it](06-which-mechanism-did-it/) | reset, EMA, or the two together — which half of VQ-VAE-2's fix actually did the work? | verified |

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
directly from topic 01's serving engine — no line of that file changed.
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
acceptance bar and printed `MET` — this path's first `MET` verdict among
the fully-built topics this session (the vision path under topic 01 and
topic 05, game AI, both closed `NOT MET`). The codec and the LM-completion
pathway both beat both required naive
baselines, the KV-cache decode path is provably identical to full recompute
rather than merely similar, and the latency gap is reported at two scales
rather than assumed from one. The report is explicit that this is an easier
bar than the vision path under topic 01 or topic 05 (game AI) set out to
clear — "does a proven mechanism
transfer unchanged" is a different, lower bar than "does training produce a
policy that beats a strong baseline" — not evidence this topic was more
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
([`reference/local-4090.md`](../../reference/local-4090.md)), independently
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

[Stage 05](05-codebook-reset/) tested the standard fix for exactly the
seed-dependent codebook problem stage 04 found — periodic dead-code reset
(VQ-VAE-2, Razavi et al., 2019), reinitializing codebook entries whose EMA
usage count falls near zero. Retrained on the identical 10-speaker balanced
mix, same step count, learning rate, and seeds as stage 04, with only the
vector quantizer changed: all three seeds reached 64 of 64 codes used (vs.
18-63/64 without reset), and the reconstruction-quality margin over the
silence baseline tightened from a 4.3%-38.2% spread to a narrow 33.8%-37.6%
band. Full numbers in
[its run record](05-codebook-reset/runs/2026-08-01-codebook-reset.md).

[Stage 06](06-which-mechanism-did-it/) answered the question stage 05
deliberately left open — whether VQ-VAE-2's other half, the EMA-updated
codebook, adds anything on top of reset — by running all four cells of the
reset-by-EMA grid instead of a second two-arm comparison. EMA alone collapses
the codebook to 1 of 64 codes on every seed and is the only arm in this mission
that fails `mission.yaml`'s own "beats a naive baseline" bar; EMA on top of
reset raises the entropy ratio on every seed (0.933/0.872/0.875 against
`reset-only`'s 0.826/0.814/0.791). The same mechanism, measured twice, changes
sign — which is why the two-arm study stage 05 declined to run could not have
answered this either way. Reconstruction quality is a separate matter and stays
inconclusive: EMA's effect on top of reset spans −0.00065 to +0.00318 in MSE
across three seeds and contains zero. Both previously published corners
reproduce their own stages to the full float, so the two new corners are
measured against this mission's real baselines. Full numbers in
[its run record](06-which-mechanism-did-it/runs/2026-08-05-factorial-vq.md).

Per [the mission contract](../../reference/standards/mission-contract.md), this
contract is declared before any stage is built, so the baseline and metric
above cannot be chosen after seeing which ones flatter a result.



## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-audio-codec` | The collapse that looked like success | [when-silence-is-a-local-minimum](00-audio-codec/when-silence-is-a-local-minimum/) |
| `00-audio-codec` | Why does a VQ codebook collapse — and can you watch it happen? | [why-codebooks-collapse](00-audio-codec/why-codebooks-collapse/) |
| `01-streaming-decode` | The KV cache on audio tokens: same answer, flat latency | [when-the-cache-pays](01-streaming-decode/when-the-cache-pays/) |
| `01-streaming-decode` | The zero gap is checked at logit level, not token level | [when-the-logits-match](01-streaming-decode/when-the-logits-match/) |
| `02-report` | MET rests on five lines, each independently | [the-five-acceptance-lines](02-report/the-five-acceptance-lines/) |
| `02-report` | The transfer that needed no new serving code | [when-the-transfer-is-clean](02-report/when-the-transfer-is-clean/) |
| `03-real-speech-and-network` | The realtime margin is the network's tail | [when-the-network-is-the-tail](03-real-speech-and-network/when-the-network-is-the-tail/) |
| `04-multi-speaker` | No collapse — and a seed-dependent codebook | [when-codebook-health-is-seed-dependent](04-multi-speaker/when-codebook-health-is-seed-dependent/) |
| `04-multi-speaker` | The fix that did not generalize | [when-the-fix-did-not-generalize](04-multi-speaker/when-the-fix-did-not-generalize/) |
| `05-codebook-reset` | The mechanism that fixed utilization in every seed | [when-reset-reaches-64-64](05-codebook-reset/when-reset-reaches-64-64/) |
| `05-codebook-reset` | Is a dead-code reset a cure, or a maintenance loop? | [when-the-reset-never-stops](05-codebook-reset/when-the-reset-never-stops/) |
| `06-which-mechanism-did-it` | Which half of the fix did the work? | [the-half-that-did-the-work](06-which-mechanism-did-it/the-half-that-did-the-work/) |
| `06-which-mechanism-did-it` | The 2x2 is trustworthy because its corners are already published | [when-the-corners-reproduce](06-which-mechanism-did-it/when-the-corners-reproduce/) |

## What this will not prove

The codec and dataset are toy-scale by construction, so nothing here says
anything about production speech quality or true full-duplex operation — the
loop runs one direction at a time. Multi-speaker robustness is only
partially tested: stage 03 uses 1-2 speakers, stage 04 extends this to 10 of
the corpus's 40+ dev-clean speakers, and neither is the full corpus. Nothing
here diagnoses *why* stage 04's escape became seed-dependent, only that it
did. Stage 05 shows dead-code reset closes that specific gap at 10 speakers,
and stage 06 crosses reset with the EMA codebook update to establish that
EMA's contribution is real for codebook uniformity, catastrophic on its own,
and inconclusive for reconstruction quality — but both stages hold
`reset_every`, `dead_threshold`, `ema_decay`, and `epsilon` at one value each,
on 10 of the corpus's 40+ speakers, so neither is a parameter sweep and neither
covers the full corpus. Stage 03 adds a real network round
trip, but only over this repository's own home Tailscale link — a
DERP-relayed hop on this sandbox's network path — which does not generalize
to arbitrary internet paths or a direct (non-relayed) connection. Full
boundary in [`mission.yaml`](mission.yaml) under `does_not_prove`.
