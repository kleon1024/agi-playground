---
status: verified
level: applied
base: scratch
verified: 2026-07-31
label: Audio codec
---

# How does a waveform become a discrete token sequence at all?

**Question:** before this mission can ask whether a text-token serving
mechanism transfers to audio, something has to turn a waveform into a
discrete token sequence in the first place. This stage builds the smallest
thing that could do that -- a convolutional encoder, a vector-quantization
bottleneck, and a decoder -- and measures whether the round trip is worth
anything at all.

**The artifact this stage produces** is one held-out clip, turned into
tokens and back:

```
clip 2: notes=[277Hz, 523Hz, 277Hz]  ->  64 discrete tokens  ->  reconstructed waveform
per-clip reconstruction MSE: 0.0162 (naive silence baseline: 0.325)
```

**Before this:** nothing -- this is the mission's first stage, per
[`mission.yaml`](../mission.yaml)'s declared order.

## Why synthetic tones, not real speech

Real speech needs a dataset license and a much larger codec before the
result would mean anything about speech specifically. This mission's actual
question is about the *serving mechanism*, not audio fidelity -- so
`core/audio_data.py` generates short clips procedurally: 1-3 sine tones from
a small fixed 6-frequency vocabulary, with attack/decay envelopes and a
little noise, real waveforms with a checkable "which notes played, in what
order" identity, and trivial provenance since nothing is scraped.

## The codec

`core/codec.py`: a 6-layer stride-2 `Conv1d` encoder downsamples a
4096-sample (0.512s at 8kHz) clip by 64x into 64 latent frames, a 64-entry
vector-quantization codebook (straight-through gradient) snaps each frame to
its nearest codebook entry, and a mirrored `ConvTranspose1d` decoder
reconstructs the waveform. 64 tokens per clip is deliberately close to a
short text prompt's length -- stage 01 needs to hand this sequence to the
same KV-cache decode loop mission 01 built for text tokens.

## A real failure, and what fixed it

The first training attempt (`lr=3e-4`) plateaued immediately: reconstruction
loss matched the silence baseline exactly, and the codebook collapsed to 1-2
codes out of 64. A single-clip overfitting check explained why: the decoder
sits in a genuine local minimum where near-silence is locally optimal against
a zero-mean signal for the first 60-90 steps, and only escapes it once
gradient noise pushes it toward the waveform's actual shape. Raising the
learning rate to `1e-3` and training for 600 steps crossed that threshold at
around step 150 and kept improving through step 550. Full trace in
[`runs/2026-07-31-codec-training.md`](runs/2026-07-31-codec-training.md).

Why does matching silence look locally optimal? Training minimizes
`L = mean((x_hat - x)^2)` over waveforms `x` that are zero-mean by
construction. If the decoder outputs a constant near zero regardless of
input, the gradient of `L` with respect to that constant depends only on the
mean of the target, already near zero -- the easiest early gradient step is
"output less," not "output the right shape." The real training log shows
this exactly: `recon_loss` is flat at 0.325-0.349 for the first 100 steps,
then falls to 0.0145 by step 550. The escape is visible in `vq_loss`, which
jumps from ~5e-6 (a converged codebook) to 4.18 at step 150 -- the encoder
has started producing latents no longer clustered near the codebook's
initial center -- then falls again as the codebook re-converges around real
structure (0.06 by step 550).

<!-- interactive: CodecCollapseEscape -->

VQ-VAE training getting stuck in this kind of near-silence local minimum,
needing a codebook-reset technique to escape it, is documented in VQ-VAE
training generally (van den Oord et al., 2017); EnCodec's recipe (Défossez
et al., 2022) applies periodic codebook re-initialization for exactly this
reason -- the same technique mission 08's video codec needed for its own,
more severe collapse.

## Result

```
eval MSE:  codec=0.01114   silence=0.32510   mean_signal=0.30013
codebook usage: 34/64 codes used, entropy_ratio=0.733
```

The codec beats both required naive baselines by more than 27x, with healthy
(non-collapsed) codebook usage -- the acceptance bar this stage needs to
clear before its token sequence is worth anything to stage 01. Real
reference and reconstructed `.wav` files for 3 held-out clips are in
`runs/example_clips/`.

## Run it

```bash
cd 07-multimodal-generation/voice/00-audio-codec/core
uv run --group torch python train_codec.py --steps 600 --lr 1e-3 --n-train 512 --n-eval 100 --seed 0
```

CPU only, ~2 minutes wall-clock. No hosted-API spend, matching
`mission.yaml`'s `cost_budget`.

## What this stage does not establish

Nothing about streaming or per-chunk latency -- this stage reconstructs
whole clips at once; stage 01 builds the streaming decode loop and measures
what that costs. Nothing about real speech, multi-speaker audio, or
production codec quality, per `mission.yaml`'s own `does_not_prove`.

**Next:** stage 01 hands this codec's token sequences to the KV-cache and
continuous-batching decode loop imported from
[`05-serve/graph-execution`](../../../01-language-model/05-serve/graph-execution/),
and measures whether it works unchanged for audio tokens.

A detour from here: [why does a VQ codebook collapse — and can you watch it
happen?](why-codebooks-collapse/) measures codebook usage at 25-step
intervals on a fresh seed — the whole batch on one code at step 0, a slow
non-monotonic recovery, and the seed-dependence the mission's later stages
investigate.

Another detour: [the collapse that looked like success](when-silence-is-a-local-minimum/) — the recorded pilot read: silence is locally optimal against a zero-mean signal (MSE 0.325, 1-2/64 codes), and the escape (0.32 -> 0.03) is why the recipe matters.
