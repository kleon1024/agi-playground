---
status: draft
level: frontier
label: Video generation
---

# Before the video is good, is it even affordable to make?

**Question:** every other mission in this repository trains something inside
one GPU's reach in minutes or hours. A video clip is dozens of frames, each
frame is hundreds of patch tokens, and a temporal model multiplies the two.
Before asking whether generated video looks right, this mission has to answer
a cheaper, prior question: does this repository's real-run, declared-compute
discipline survive contact with video at all — and if it does, what does a
few seconds of synthetic footage actually cost?

**The artifact this mission follows** is one short synthetic clip: a
generated sequence of frames (for example, a colored shape moving on a plain
background) produced from a seed condition, alongside the exact GPU-hours or
dollars it took to train the model that produced it.


## Why this mission exists

Missions 01 through 07 each pick a domain where an honest, from-scratch,
single-GPU version of the real system is buildable in a session or two.
Video is the domain where that is not obviously true, and this repository's
own rule — "if you cannot run it, do not write the number" — means the
compute question has to be asked and answered before any quality claim is
attempted, not discovered halfway through a training run that quietly never
finishes.

That is also why this mission is sequenced last among the new AI-system
tracks in this curriculum's build order. Missions 05 (vision-language) and 06
(game AI) reuse existing training-loop and reinforcement-learning code
almost directly; mission 07 (real-time voice) needs one new component, an
audio codec. This mission needs a new tokenizer *and* a materially larger
compute budget, and may need this repository's Modal serverless lane (see
[infra/](../../infra/)) rather than the single local 4090 lane every other
mission has used so far.

## What gets measured, and why cost comes first

Two baselines, because "better than nothing" and "better than a known
number" are different claims.

**Frame-repeat / linear extrapolation** is the no-learning control: repeat
the last real frame, or extrapolate the motion already visible in the
conditioning frames, with no model at all. Any learned model that cannot
beat this has not learned anything about motion — it has only learned to
copy.

**A named public toy baseline** — a published reconstruction-loss number on a
problem in this class, such as Moving MNIST — cited and dated, never
reproduced. It exists so a reader has one external point of reference, not
so this mission's number can be directly compared to it; the dataset,
tokenizer, and compute ceiling here are all this mission's own.

The primary metric is a held-out reconstruction or next-frame prediction
error, but it is reported beside training wall-clock and real dollar cost on
whichever lane actually ran it — for this mission specifically, a quality
number with no cost number next to it is an incomplete result, because the
entire premise of building this mission at all was to find out whether the
cost is tolerable.

## The outcome this mission treats as a real result, not a failure

If a training run would cross the declared compute ceiling in
[`mission.yaml`](mission.yaml) before producing a usable checkpoint, the run
stops there and that is reported as a finding — video generation is not
feasible inside this repository's compute discipline at the scale attempted —
rather than silently shrinking the dataset or the model until something fits
and presenting that as the plan all along. Per
[the mission contract](../../standards/mission-contract.md), the baseline and
metric were declared before any run, specifically so a result cannot be
picked after the fact to flatter whichever outcome actually happened.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Synthetic video dataset](00-synthetic-video-dataset/) | what makes a scoreable short sequence, generated rather than scraped? | verified |
| [01 — Video tokenizer](01-video-tokenizer/) | how do frames become a token sequence a decoder can condition on? | verified |
| 02 — Generation model | can an autoregressive or small diffusion model over those tokens beat frame-repeat? | not started |
| 03 — Report | what did this cost, and did it clear the declared ceiling? | not started |

[Stage 00](00-synthetic-video-dataset/) extends [mission 05](../05-vision-language-model/)'s
synthetic image generator along a time axis, reusing its drawing primitives
unmodified and adding only the temporal part: a shape moving in one of 8
fixed directions at constant speed, bounded so it stays on-canvas for all 8
frames of a clip. 800 train / 150 eval clips generated in 2.7s CPU, $0, with
the same train/eval collision guardrail mission 05 stage 00 established —
this time rejecting a single eval candidate out of 150, since a per-clip
render space multiplying shape, color, size, direction, and start position
across 8 frames is far larger than a single static image's. Full trace in
[its run record](00-synthetic-video-dataset/runs/2026-07-31-dataset-gen.md).

[Stage 01](01-video-tokenizer/) reuses mission 07's `VectorQuantizer`
unmodified for a per-frame VQ-VAE codec (new 2D `Encoder`/`Decoder`,
one 64-way token per frame). Three real training failures preceded the
working result, each with its own diagnostic: codebook collapse (fixed by
data-dependent codebook init), dead codes never recovering (fixed by
periodic revival), and a decoder `Tanh` that saturated to background white
within the first ~50 steps and permanently blocked gradient regardless of
which code the decoder received (the real bug — confirmed directly by
feeding two different codes into the decoder and measuring a 0.001 max
output difference; fixed by removing the bounded final activation). The
resulting codec beats both naive baselines (16.6% and 8.2% lower MSE), and a
shape-pixel-vs-background-pixel split confirms the gain is real shape
signal (24.6% better than background baseline on shape pixels
specifically), not merely exploiting the 94%-background pixel imbalance —
though the reconstruction itself is a faint, low-fidelity blur at this
one-token-per-frame bit rate, shown and reported as what it is. Full trace
in [its run record](01-video-tokenizer/runs/2026-07-31-codec-training.md).

Stage 01 is the genuinely new code in this mission: no lesson anywhere in
this repository yet turns a sequence of frames into tokens a decoder can
attend over. Stage 02 is where the feasibility decision in
[`mission.yaml`](mission.yaml) actually gets made, on real hardware, against
a real ceiling.

## What this will not prove

Nothing about real-world video realism, coherence beyond a handful of frames,
or competitiveness with any production video-generation system. Nothing about
audio or sound-video synchrony. And if this mission closes on a compute
infeasibility finding rather than a trained model, that finding is scoped to
the compute lanes available at the time of the run — it says nothing about
what a larger GPU or a longer budget would make possible. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
