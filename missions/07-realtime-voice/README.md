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

## Stages

| Stage | Question | Status |
|---|---|---|
| 00 — Audio codec | how does a waveform become a discrete token sequence, and what does that cost in quality? | not started |
| 01 — Streaming decode | does the existing KV-cache and continuous-batching mechanism work unchanged for audio tokens? | not started |
| 02 — Report | what does streaming cost in latency, and what does it buy or lose against the offline pass? | not started |

Per [the mission contract](../../standards/mission-contract.md), this
contract is declared before any stage is built, so the baseline and metric
above cannot be chosen after seeing which ones flatter a result. No stage
below has run yet; none of the numbers this mission will report exist until
they do.

## What this will not prove

The codec and dataset are toy-scale by construction, so nothing here says
anything about production speech quality, multi-speaker or multilingual
robustness, or true full-duplex operation — the loop runs one direction at a
time. Measured latency is local compute time, not round-trip time to a real
client over a real network. Full boundary in [`mission.yaml`](mission.yaml)
under `does_not_prove`.
