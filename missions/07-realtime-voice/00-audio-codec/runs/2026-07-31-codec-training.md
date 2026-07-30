# Training the from-scratch audio codec

## Command

```bash
cd missions/07-realtime-voice/00-audio-codec/core
uv run --group torch python train_codec.py --steps 600 --lr 1e-3 --n-train 512 --n-eval 100 --seed 0
```

Apple silicon laptop, macOS 15.6.1, CPU only. Repository HEAD at time of run:
`e496ec3`. Wall-clock: 126.0s for 600 steps.

## What ran

512 synthetic training clips, 100 held-out eval clips (disjoint, drawn from
the same `random.Random(seed)` stream immediately after the training clips --
see `core/audio_data.py`). Each clip: 4096 samples at 8kHz (0.512s), 1-3 sine
tones from a 6-frequency vocabulary with attack/decay envelopes and a little
noise. The codec: a 6-layer stride-2 Conv1d encoder (4096 samples -> 64
latent frames, downsample 64x), a 64-entry vector-quantization codebook
(straight-through gradient, embedding dim 32), and a mirrored 6-layer
ConvTranspose1d decoder. Trained with AdamW, reconstruction MSE plus a 0.25x
weighted VQ commitment loss.

## A real first attempt did not work, and why

The first pilot (`lr=3e-4`, 150 steps) plateaued at recon MSE 0.325 --
statistically identical to the silence baseline -- while the VQ commitment
loss collapsed toward 0 and codebook usage collapsed to 1-2 of 64 codes. A
single-clip overfitting sanity check (`lr=1e-3`, no batching) showed why:
the decoder sits in a genuine local minimum for the first 60-90 steps where
outputting near-silence is a locally optimal way to minimize MSE against a
zero-mean signal, and only escapes it once gradient noise pushes the decoder
toward actually reproducing the waveform's shape -- after which loss drops
sharply (0.32 -> 0.03 over the next 150 steps in the single-clip check).
Raising the learning rate to `1e-3` and increasing steps to 600 let the full
512-clip run cross that same threshold at roughly step 150 (recon_loss
0.296, vq_loss jumps to 4.18 as the codebook starts actually partitioning the
latent space) and continue improving through step 550.

## Result

```
eval MSE:  codec=0.01114   silence=0.32510   mean_signal=0.30013
codebook usage: 34/64 codes used, entropy_ratio=0.733 (max would be 1.0)
```

The codec's reconstruction MSE is **29x smaller** than the silence baseline
and **27x smaller** than the mean-signal baseline -- a decisive win on the
acceptance bar's first requirement ("reconstruction-quality proxy beats a
naive baseline... on held-out clips"). Codebook usage is healthy: 34 of 64
codes are actually used across the eval set, with an entropy ratio of 0.73
(1.0 would be perfectly uniform usage) -- no collapse to a handful of codes,
unlike the failed first pilot.

## Concrete artifact: 3 held-out clips, waveform through tokens and back

```
clip 0: notes=[220Hz, 392Hz]        per-clip MSE=0.0083   64 tokens
clip 1: notes=[440Hz, 277Hz]        per-clip MSE=0.0083   64 tokens
clip 2: notes=[277Hz, 523Hz, 277Hz] per-clip MSE=0.0162   64 tokens
```

Clip 2's token sequence is the clearest qualitative evidence the tokens carry
real content: it repeats the 277Hz note (first and third), and its token
sequence visibly repeats too -- the run of tokens
`11, 26, 49, 36, 8, 11, 26` appears once around the clip-2/clip-3 boundary
and again near the end, matching the note that plays twice. Real reference
and reconstructed `.wav` files for all 3 clips are in `example_clips/`.

## What this run establishes

A from-scratch codec, trained from nothing in about 2 minutes of CPU time,
turns a 4096-sample waveform into a 64-token discrete sequence and
reconstructs it well enough to decisively beat both required naive
baselines, with healthy (non-collapsed) codebook usage. This is the
prerequisite stage 01 needs: a real discrete-token stream to hand to the
reused KV-cache decode loop.

## What this run does not establish

Nothing about streaming or per-chunk latency -- this run reconstructs the
whole clip at once, the offline baseline stage 02 will compare streaming
against. Nothing about real speech; the codec has only ever seen synthetic
sine tones. Whether 34/64 codes is enough diversity for a harder or longer
utterance is untested at this scale.
