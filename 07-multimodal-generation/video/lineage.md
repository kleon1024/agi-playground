---
level: reference
---

# The open-source line behind video generation

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission asks the cost question before the quality question
— is generated video even affordable on one GPU, and what does a few seconds
of synthetic footage cost? Every architecture in the line answers that
question differently, and the answer changed twice.

## Tokenizing video

**VQ-VAE** (van den Oord et al., 2017), inherited from audio, turned video
frames into discrete tokens a decoder can condition on — the line's first
answer, and the one this mission builds from scratch. Its tradeoff is the
codebook's: compression is what makes long sequences affordable, and
compression is what loses detail.

## Diffusion transformers

**DiT** (Peebles & Xie, 2022) scaled diffusion from convolutional U-Nets to
transformers over latent patches, and **W.A.L.T** (2023) applied a causal
masked DiT to video. **Sora** (OpenAI, 2024) is the line's landmark: a
spacetime latent-patch DiT that generates coherent minutes, establishing
that diffusion over video latents — not autoregressive over video tokens —
is where quality lives. **VideoPoet** (2023) took the opposite route, a
language model over video tokens, and **Genie** (2024) pushed autoregressive
world-model generation. The tradeoff between the two routes is the one this
mission's report quantifies at toy scale: autoregressive over tokens is
simple and expensive per step; diffusion over latents is parallel and
expensive to train.

## The cost line

The open line since Sora is compute: a minute of video is hundreds of
latent-patch tokens per frame times dozens of frames, so cost scales
quadratically with resolution and duration. **CogVideoX** (2024) and
**Wan** (2025) are the open-weight answers, trading quality for feasibility
at progressively larger but still finite budgets. The repo's measured point
is the discipline the line makes necessary: stage 02's generation model
trains in 140.9s, the full stage in 152.5s, a single generation 0.05s — the
cost number reported beside every quality number, because a cost without a
quality number and a quality without a cost number are both incomplete.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the 140.9s/152.5s
training wall-clock, the 0.05s generation, the length-and-multi-object
feasibility verdicts — cite their runs. The line does not settle whether
autoregressive or diffusion "wins"; it says the cost ceiling decides first,
which is exactly why the mission asks it first.
