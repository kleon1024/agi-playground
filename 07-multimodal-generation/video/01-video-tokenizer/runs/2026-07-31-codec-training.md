# Training the per-frame video codec, and the decoder saturation bug it exposed

The interesting result here is not the final numbers -- it is that the first
three real attempts to train this codec all collapsed to a single failure
mode, and each one needed its own diagnostic to find, matching the exact
discipline mission 07 stage 00's codec training needed for a different
(local-minimum) failure. This run record keeps all of them rather than
presenting only the fix.

## Command (final, official run)

```bash
cd 07-multimodal-generation/video/01-video-tokenizer/core
uv run --group torch python train_video_codec.py --steps 800 --batch-size 16 --lr 1e-3 --seed 0 --out ../runs
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Python | 3.12.9 (uv-managed), PyTorch (`--group torch`) |
| Repository HEAD at run time | `6f7826f` |

CPU only, no CUDA GPU available in this environment -- a real deviation from
`mission.yaml`'s "local GPU lane" framing, stated plainly rather than assumed
away, matching every other mission built this session.

## Attempt 1: codebook collapse (600 steps, lr up to 3e-3)

The first runs plateaued immediately at `eval_mse_codec = 0.0944`, exactly
matching the naive "predict flat background" baseline, with
`codebook_usage.unique_codes_used = 1` out of 64 -- the codec was using a
single code for every frame of every clip, text-book VQ-VAE codebook
collapse. `VectorQuantizer`'s codebook (imported unmodified from mission 07)
initializes every entry to `uniform(-1/64, 1/64)`, a tiny ball around the
origin; a randomly-initialized encoder's outputs land far outside that ball
at an arbitrary, much larger scale, so every codebook entry is nearly
equidistant from any encoder output and the nearest-neighbor argmin locks
onto one index almost immediately. Raising `lr` (which fixed mission 07's
audio codec) did not fix this at all -- collapse is about *which* code gets
picked, not how fast the picked code's reconstruction improves.

**Fix 1**: `init_codebook_from_data()` -- seed the codebook from a real
sample of encoder outputs on real data before training starts, so every
entry begins inside the actual data distribution.

## Attempt 2: codebook diversity fixed, but no quality improvement

With data-dependent codebook init alone, codebook usage improved
(`unique_codes_used` in the 50s out of 64) but `eval_mse_codec` still did not
beat either naive baseline after 800 steps -- a healthier codebook,
identical reconstruction quality. A single-clip overfitting sanity check
(the same tool mission 07 used to diagnose its own local minimum) showed why:
even with several codes selected across a clip's 8 frames, reconstruction
loss still plateaued exactly at the background-baseline floor.

**Fix 2**: `revive_dead_codes()` -- every 20 steps, reset codebook entries
that received zero assignments in that window to a fresh, perturbed sample
of the current batch's encoder outputs (the standard SoundStream/EnCodec
dead-code-revival technique), since an `nn.Embedding` lookup only backprops
into whichever row gets selected -- an early, arbitrary winner otherwise
entrenches itself for the rest of training and every other row stays frozen
at its initial value.

## Attempt 3: the real bug -- decoder Tanh saturation

Codebook usage was now healthy (many codes used, real entropy) and the
8-clip overfit control (a case with exactly enough codebook capacity for a
near-injective frame-to-code mapping) *still* plateaued at the background
floor. Direct inspection found the actual cause: feeding two very different
codebook vectors straight into the decoder produced outputs differing by at
most 0.001 across every pixel -- the decoder's final `Tanh` had saturated to
+1 (white) within the first ~20-50 steps of training (background covers over
94% of every frame's pixels by construction, so pushing every output toward
the saturated white tail is the fastest way to reduce MSE early on), and once
saturated, `tanh`'s local gradient is near zero, permanently blocking any
signal from reaching the decoder's earlier layers regardless of which code it
receives.

**Fix 3**: remove the final `Tanh` entirely -- an unbounded linear output
head, clamped only at image-export time, not during the loss. The same
8-clip overfit control that had plateaued exactly at the baseline with
`Tanh` reached 0.059 (29% below the 0.083 baseline on that subset) and was
still falling when the check was stopped, confirming this was the real
blocker.

## Official run: all three fixes together

```
eval_mse_codec:        0.07875
baseline (background):  0.09437   (codec beats it by 16.6%)
baseline (mean-frame):  0.08580   (codec beats it by 8.2%)
codebook usage:         63 / 64 codes used, entropy ratio 0.91
dead codes revived:     158 (over 800 steps, revive_every=20)
wall-clock:              137.6s CPU, $0
```

## What the improvement is actually made of

Aggregate MSE beating both baselines does not by itself say whether the
codec learned the shape or just got slightly better at matching background.
`shape_vs_background_mse()` is now part of the training script itself (not a
one-off check) and its output is written into `video-codec-seed0.json`
directly, splitting eval pixels into "shape" (reference deviates from pure
white by more than 0.15) and "background" (everything else, 94.0% of all
pixels):

```
                    shape-pixel MSE    background-pixel MSE
codec               1.194              0.0080
background baseline 1.583              0.0000
mean-frame baseline 1.311              0.0081
```

The codec beats the background baseline by 24.6% specifically on the pixels
that carry the shape, not only by matching the (already-perfect) background
better -- real evidence it is encoding something about where the shape is,
not merely exploiting the class imbalance. But the absolute shape-pixel MSE
(1.19, against a per-channel range of 2.0) is still large: visual inspection
of the committed example frames (`example_frames/eval0_frame0_reconstructed.ppm`
vs `..._reference.ppm`) shows a faint, blurred silhouette rather than a
sharp, high-fidelity shape -- expected at this bottleneck's bit rate (one
64-way code per frame) and reported here rather than only in the number.

## What this run does not establish

Nothing about a trained generation model -- no autoregressive or diffusion
model has touched the resulting token sequences yet; that is stage 02.
Nothing about real-world video, multi-object scenes, or camera motion, all
outside this dataset's construction. The three failure modes documented
above are specific to this codec's architecture, loss, and this dataset's
extreme background/foreground pixel imbalance -- a different encoder/decoder
shape or a less background-dominated dataset would need its own collapse
check, not an assumption that these same three fixes are always necessary.
