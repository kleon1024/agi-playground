---
status: verified
level: applied
base: scratch
verified: 2026-07-31
label: Video tokenizer
---

# How do frames become a token sequence a decoder can attend over?

**Question:** stage 00 produced 8-frame clips, each frame a full 32x32 RGB
image. Before any sequence model can predict motion, those pixels need to
become a short discrete-token sequence -- the same problem mission 07 stage
00 solved for audio (waveform to token sequence via a VQ-VAE), now asked of
video frames instead.

**The artifact this stage produces** is one held-out clip's first frame,
encoded to a single 64-way discrete token and decoded back, shown against
the real frame (`@`/`#`/`:` = increasingly close to the shape's yellow;
` ` = pure white background):

```
reference                            reconstructed
                                                                     :
                                            ... .
                                            ....... . .....
                                            ...............
                                            ...............
                                           ......:...........
                                          .......:..............
              @                          .....:.:.. .  .........
            @@@@@                         ......:...   ..:.....
            @@@@@                         ...::..        .......
           @@@@@@@                       ........        ......
            @@@@@                        ....::..        ....:...
            @@@@@                         ..::...        ....:...
              @                          ...:::.:        ..:::...
                                          ....:::.        ...:....
                                          ....::.:........:::::...
                                           ...::::...  ...:::::...
                                          ....:::::::::::::::::...
                                          ....::::.:::.::::::::...
                                          .....:::.:::.::::::::...
                                          ....:::::.:.:::::::....
                                         .....:::...:::::::.:.....
                                          ......................
                                          ......................
                                            .... .   ........
                                            .....        . .
                                                                     :
```

The reconstruction is a faint, blurred, roughly rectangular smear loosely
overlapping the true shape's location -- real signal, not noise, but a low-
fidelity one. The rest of this chapter is about why it looks like this and
what a real bug cost along the way.

**Before this:** [stage 00](../00-synthetic-video-dataset/) -- the clips this
codec is trained against.

## What is reused, and what is new

`VectorQuantizer` -- the straight-through nearest-codebook-entry bottleneck
-- is imported directly, unmodified, from
[mission 07's audio codec](../../07-realtime-voice/00-audio-codec/core/codec.py).
Nothing about it is audio-specific: it already operates on generic
`(B, N, D)` sequences, so it works unchanged for a per-frame video latent
just by construction. **No line of that file was changed.** The genuinely
new code is a 2D `Encoder`/`Decoder` pair: three stride-2 `Conv2d` layers
collapse each 32x32 frame independently to a single latent vector (32 -> 16
-> 8 -> 4 -> 1), mirrored by `ConvTranspose2d` on the way back. Each clip's
8 frames are encoded independently -- no cross-frame mixing happens inside
the codec itself, the same division of labor mission 07 keeps between its
codec (per-chunk) and its sequence model (stage 02 here).

## Three real failures before this worked

The first three training attempts all plateaued at exactly the naive
"predict flat background" baseline, and each needed its own diagnostic to
find the actual cause:

1. **Codebook collapse** -- `VectorQuantizer`'s codebook initializes near the
   origin while a random encoder's outputs land far outside that ball, so
   the nearest-neighbor argmin picks one index almost arbitrarily and
   locks onto it. Fixed by seeding the codebook from real encoder outputs on
   real data before training starts.
2. **Dead codes never recover** -- even with a healthy initial codebook, an
   early, arbitrary winner keeps winning (only a selected `nn.Embedding` row
   gets gradient), so training still plateaued. Fixed with periodic dead-code
   revival: every 20 steps, unused codebook rows are reset to a perturbed
   sample of the current batch's encoder outputs -- the standard
   SoundStream/EnCodec technique.
3. **Decoder `Tanh` saturation** -- the real bug. With codebook diversity
   fixed, an 8-clip overfit control (enough codebook capacity for a
   near-injective frame-to-code mapping) *still* plateaued at the baseline.
   Direct inspection found the decoder's final `Tanh` had saturated to white
   within the first ~20-50 steps (background is over 94% of every frame's
   pixels, so saturating there is the fastest early MSE win), and once
   saturated, `tanh`'s near-zero local gradient permanently blocked any
   signal regardless of which code the decoder received -- confirmed
   directly: two very different codebook vectors fed into the decoder
   produced outputs differing by at most 0.001 across every pixel. Removing
   the bounded final activation fixed it: the same 8-clip control that had
   plateaued exactly at baseline reached 29% below it and was still falling.

Full trace of all three, in order, with the numbers at each stage:
[`runs/2026-07-31-codec-training.md`](runs/2026-07-31-codec-training.md).

## The result, and what it is actually made of

```
eval_mse_codec: 0.0788   vs background baseline 0.0944 (16.6% better)
                         vs mean-frame baseline  0.0858 (8.2% better)
codebook usage: 63/64 codes used, entropy ratio 0.91
```

Beating both baselines in aggregate MSE does not by itself say whether the
codec learned the shape or just matched background slightly better --
background is 94% of every frame's pixels by construction and can dominate
an aggregate number on its own. Splitting eval pixels into shape pixels and
background pixels: on shape pixels specifically, the codec beats the
background baseline by 24.6% (MSE 1.194 vs 1.583) -- real evidence it is
encoding something about where the shape is, not only exploiting the class
imbalance. But the absolute shape-pixel error is still large, which is
exactly what the reconstructed frame above shows: a real but low-fidelity,
blurred signal, not a sharp shape -- expected at a one-token-per-frame bit
rate, and reported as what it is rather than rounded toward either "it
works" or "it doesn't."

## Run it

```bash
cd missions/08-video-generation/01-video-tokenizer/core
uv run --group torch python train_video_codec.py --steps 800 --batch-size 16 --lr 1e-3 --seed 0 --out ../runs
```

CPU only -- no CUDA GPU was available in this environment, a real deviation
from `mission.yaml`'s "local GPU lane" framing, stated plainly rather than
assumed away. ~136s wall-clock, $0.

## What this stage does not establish

Nothing about a trained generation model -- no autoregressive or diffusion
model has touched the resulting token sequences yet; that is stage 02.
Nothing about real-world video, multi-object scenes, or camera motion, all
outside this dataset's construction by stage 00. The three failure modes
documented above are specific to this codec's architecture and this
dataset's extreme background/foreground pixel imbalance -- a different
encoder/decoder shape, loss, or a less background-dominated dataset would
need its own collapse check, not an assumption that these same fixes always
apply.

**Next:** stage 02 trains a sequence model over this codec's token
vocabulary and checks whether the compute cost of doing so clears the
ceiling `mission.yaml` declared before any of this was built.
