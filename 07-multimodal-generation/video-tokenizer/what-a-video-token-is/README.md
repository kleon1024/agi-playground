---
status: verified
level: applied
base: scratch
label: What a video token is
verified: 2026-08-06
---

# What is the discrete thing a video model conditions on?

**Question:** [stage 01](../) turns frames into a token sequence a decoder
can condition on, and its recorded run documents three real collapse
diagnostics on the way. This chapter measures the token stream itself on a
second seed: what the codes are, how healthy the codebook stays, and whether
the health the stage's fixes bought is seed-stable.

**Before this:** [stage 01's codec training](../), including its collapse and
decoder-saturation records.

## The token

The video codec compresses each frame through an encoder into a spatial grid
of latent patches, quantizes each patch to its nearest codebook entry, and
the decoder reconstructs the frame from the code indices. A clip's token
sequence is therefore frames x spatial patches — the codes carry both the
appearance of each frame and, implicitly, the order the frames come in,
because the sequence position is the temporal axis the decoder attends
over. The stage's codebook is 64 entries at this scale; a production codec
uses thousands, and the token count per clip is what makes video cost what
it does (the mission's cost-first question).

## Whether the codebook stays healthy

The stage's recorded run added two mechanisms the mission-07 codec lacked:
initializing the codebook from real encoder outputs and reviving dead codes
during training. The second seed measures what that buys
([run record](runs/2026-08-06-video-token-seed2.md)):

| | seed 0 (recorded) | seed 2 (this run) |
|---|---:|---:|
| codebook usage | 63/64 | 49/64 |
| entropy ratio | 0.912 | 0.601 |
| eval MSE | 0.0788 | 0.0885 |

Both seeds avoid the full collapse that killed mission 07's seed-7 codec
(15/64 with no revival mechanism — the
[codebook-collapse chapter](../../../voice/00-audio-codec/why-codebooks-collapse/)
measures that trajectory). The revival keeps the codebook alive, but health
is still seed-dependent: 63 versus 49 codes, and reconstruction quality
tracks it (0.0788 versus 0.0885). Seed 2's codec beats the background
baseline and roughly ties the mean-frame baseline — the margin over the
cheap baselines is thin, exactly the honest scale the mission's cost-first
frame predicts.

The mechanism behind the seed dependence is the one the codebook chapter
establishes: dead codes receive no straight-through gradient, so whether
they revive depends on the optimizer's geometric path, which depends on the
seed. Revival makes the failure recoverable, not impossible.

## Why the token structure decides the cost

The mission asks whether video is affordable before whether it is good. The
token count per clip is the arithmetic behind that question: every frame
contributes a spatial grid of tokens, and the decoder attends over the whole
sequence, so doubling clip length or resolution multiplies both the token
count and the attention cost. This chapter's token count is small by
construction; the lineage
([the video-generation line](../../lineage.md))
is where the production answer — Sora's spacetime latents, DiT patch grids —
scales the same structure up.

## Evidence boundary

Two seeds, 800 steps, the stage's synthetic clips. It shows codebook health
is seed-dependent but revival-bound (49-63/64 versus mission 07's 15/64
without revival) on this codec; it does not measure larger codebooks,
real footage, or the decoder's quality ceiling, and it does not claim the
mean-frame tie is a win — the stage's own baselines say what that means.

## Check your mental model

Answer each before opening it.

**1. Why is a video token a code index rather than a pixel value?**

<details>
<summary>Answer</summary>

Because the decoder's job is to learn the mapping from a small discrete
vocabulary back to frames, and the model's job is to predict which code
comes next — the same next-token contract every other mission uses. A pixel
value would be a continuous, high-dimensional target with no discrete
structure to attend over; a code index is one integer per patch, and the
sequence of integers is what the decoder conditions on.

</details>

**2. Seed 2 ends at 49/64 codes and still beats the background baseline.
Why does codebook health matter if the codec works anyway?**

<details>
<summary>Answer</summary>

Because the unused 15 codes are wasted capacity, and worse, a codebook that
is losing codes is a moving target for the decoder: reconstruction quality
tracks usage (0.0788 at 63/64 versus 0.0885 at 49/64 here), and a codebook
that collapses further would eat the margin over the cheap baselines
entirely. Health is a ceiling on quality, not a side detail — which is why
the revival mechanisms exist and why seed dependence still needs watching.

</details>

## The fix and its trade

The fix this detour measures is the revival mechanism from stage 01, held
against a second seed: revival is what keeps the codebook alive (49/64 on
seed 2, 63/64 on seed 0, versus mission 07's 15/64 with no revival at all).
The trade is that health remains seed-dependent — revival makes collapse
recoverable, not impossible — and reconstruction quality tracks usage
(0.0788 at 63/64 versus 0.0885 at 49/64). A team that reads only the
aggregate result sees a codec that "beats the baseline" and misses that
the margin is thin and the vocabulary shrinks seed to seed; the usage
count and entropy ratio are the numbers that show it. The seed-dependence
itself is the residual failure the mechanism does not remove, and it is
reported rather than swept away: a production codec at this scale would
need a larger codebook and a revival schedule tuned on the deployment
corpus, not inherited.

## Who owns this loop

- **The codec owner** owns codebook health as the contract: codes used and
  entropy ratio at end of training, checked per seed, not just on the
  recorded one. Seed dependence is a codec defect signal, not a random
  variation.
- **The evaluation owner** owns the two-baseline comparison (background
  and mean-frame) that keeps a thin margin from reading as a win, and the
  per-seed health read that shows the ceiling.
- **The model team** inherits the token vocabulary the codec serves; a
  codebook that shrinks seed to seed silently reduces what the generation
  model can condition on, and that loss is invisible from the downstream
  loss curve alone.

## Next

[Stage 02's generation model](../../02-generation-model/): the decoder over
these tokens, and whether it beats frame-repeat at this scale.
