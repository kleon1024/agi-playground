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
[the mission contract](../../reference/standards/mission-contract.md), the baseline and
metric were declared before any run, specifically so a result cannot be
picked after the fact to flatter whichever outcome actually happened.

## Model lineage

The tokenizer and generation model are points on the video line — VQ-VAE for
video, DiT, Sora, and the autoregressive alternative. The
[open-source line behind video generation](../../reference/research/lineages/08-video-generation.md)
traces it, including why the cost question came first.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Synthetic video dataset](00-synthetic-video-dataset/) | what makes a scoreable short sequence, generated rather than scraped? | verified |
| [01 — Video tokenizer](01-video-tokenizer/) | how do frames become a token sequence a decoder can condition on? | verified |
| [02 — Generation model](02-generation-model/) | can an autoregressive or small diffusion model over those tokens beat frame-repeat? | verified |
| [03 — Report](03-report/) | what did this cost, and did it clear the declared ceiling? | verified |
| [04 — Longer sequences](04-longer-sequences/) | does the feasibility finding survive doubling the clip length? | verified |
| [05 — Multi-object scenes](05-multi-object/) | does the feasibility finding survive two occluding objects instead of one? | verified |
| [06 — Both axes at once](06-longer-and-multi-object/) | do two hard axes add up, or does one of them dominate? | verified |

<!-- interactive: Mission08ComputePipeline -->

Stacking every stage's real wall-clock gives the pipeline's actual compute
profile: dataset generation 2.7s, codec training 137.6s (stage 01's own run,
retrained again inside stage 02 at 140.9s rather than checkpointed, per this
mission's "retrain, don't checkpoint" convention), LM training 7.4s,
generation 0.05s. Stage 02's own total (152.5s) is what matters against the
declared ceiling: 152.5s / 1800.0s = 8.5% used, an 11.8x headroom multiplier.
That headroom does not mean a harder video task stays this cheap: the
codec's cost scales roughly linearly with frame count (three stride-2
convolutions applied per frame independently) while the LM's attention cost
scales quadratically with sequence length -- at this mission's 9-token
sequences the quadratic term is negligible, but it would not stay negligible
at a much longer clip length, and nothing in this mission's real runs
measures that regime.

Token-based autoregressive video generation over a learned discrete codebook
traces to VideoGPT (Yan et al., 2021), which pairs a 3D VQ-VAE with a causal
transformer over the resulting token grid -- the same two-stage shape this
mission's stage 01 and stage 02 follow, at a scale many orders of magnitude
larger. Video Diffusion Models (Ho et al., 2022) is the alternative lineage
`mission.yaml` explicitly leaves untried -- and the one that produced the
field's sudden 2024-2026 leap, worth tracing so a reader understands why.

Early video diffusion, like the recurrent and GAN-based frame predictors
before it, still inherited a U-Net denoiser built for one fixed resolution
and one fixed clip length. Diffusion's training objective was already more
stable than a GAN's adversarial min-max game, which collapses whenever the
discriminator overpowers the generator, but the U-Net's convolutional
inductive bias kept resolution and aspect ratio locked to whatever the
architecture was built for. Peebles & Xie's Diffusion Transformers (DiT;
*Scalable Diffusion Models with Transformers*, ICCV 2023, Paris, October
2023) replaced that U-Net backbone with a plain transformer over latent
patches -- the same block family this mission's own stage 02 sequence model
uses -- and showed image-generation quality kept improving as the transformer
was simply made bigger, the same compute-scaling relationship that had
already worked for language models, with the fixed-resolution ceiling a
convolutional U-Net imposes removed along with it.

OpenAI's Sora, first previewed February 15, 2024, was the first widely-known
demonstration of that swap applied at video scale: a diffusion transformer
denoising 3D space-time patches, producing up to a minute of temporally
coherent video from a single text prompt, at a duration and coherence no
prior public system had shown. The 2024-2026 wave of production
video-generation systems -- including ByteDance's Seedance 2.0 (announced
February 2026) and Seedance 2.5 (announced June 23, 2026; native 30-second
single-pass clips, up to 50 reference inputs, 4K output -- see
[stage 03's report](03-report/) for what this mission does and does not
compare against them) -- extends the same diffusion-transformer recipe with
more compute and training data, not a new mechanism.

[Stage 00](00-synthetic-video-dataset/) extends [mission 05](../05-vision-language-model/)'s
synthetic image generator along a time axis, reusing its drawing primitives
unmodified and adding only the temporal part: a shape moving in one of 8
fixed directions at constant speed, bounded so it stays on-canvas for all 8
frames of a clip. 800 train / 150 eval clips generated in 2.7s CPU, \$0, with
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
attend over.

[Stage 02](02-generation-model/) is where the feasibility decision in
[`mission.yaml`](mission.yaml) actually gets made, on real hardware, against
a real ceiling — and did not need it: codec retrain, LM training, and
generation together used 152.5s of a declared 1800s local-CPU budget (8.5%).
Reusing mission 01's `Config`/`Transformer` unmodified for a 65-symbol
vocabulary, the trained sequence model's greedy 4-frame completion beats the
mission's declared frame-repeat baseline by 37.2% in pixel MSE and lands
within 3.2% of the oracle (true-token) ceiling — though only 6.7% of eval
clips get the exact right token continuation, an honest gap the aggregate
MSE alone does not show, attributable to stage 01's own low-fidelity
reconstruction rather than to this stage's sequence model. Full trace in
[its run record](02-generation-model/runs/2026-07-31-generation-training.md).
Two further seeds (1 and 2) confirm the pattern rather than being a lucky
single draw: LM-completion MSE across all three seeds is `[0.0804, 0.0865,
0.0882]`, a run-to-run spread of `0.0078` against a margin over baseline of
`0.0430` -- the baseline is beaten by roughly 5.5x the spread it would need
to clear.

[Stage 03](03-report/) holds all three stages' results against
[`mission.yaml`](mission.yaml)'s acceptance bar mechanically: `MET`. This is
only the second `MET` verdict among the five missions built this session
(after mission 07) -- missions 05 and 06 both closed `NOT MET` on their own
honestly-reported results. The declared 30-minute compute ceiling was never
close to binding on any of the three seeds (8.4-8.6% used each), so this
mission's original premise -- that video might not survive this
repository's compute discipline at all -- turned out not to be the binding
constraint; the video tokenizer's training difficulty (stage 01's three real
collapse failures) was. Full trace in
[its run record](03-report/runs/2026-07-31-outcome-report.txt).

[Stage 04](04-longer-sequences/) spends part of stage 03's measured headroom
(8.5% of ceiling) to test, on real hardware, the one thing stage 03 flagged
but did not run: does the finding hold at twice the clip length? Nothing in
`video_codec.py` or `video_lm.py` was reimplemented — both were already
frame-count-agnostic except for two trailing asserts, relaxed and
documented rather than silently duplicated. Doubling `N_FRAMES` from 8 to 16
at the original `SPEED` produced a real geometry failure (`empty range in
randrange`, travel distance exceeding the 32-pixel canvas) — a genuine
consequence of the extension, fixed by halving `SPEED` to hold travel
distance roughly constant, not a bug. Across three seeds, `lm_completion`
MSE (mean 0.0856) still beats frame-repeat (0.1185) by a margin more than
4x the run-to-run spread (0.0074): `MET`. Wall-clock grew roughly 4x (mean
660s vs 152.5s, still 31-39% of the declared ceiling) and reconstruction
quality is measurably worse than at 8 frames, confirming stage 03's
prediction that the tokenizer's quality, not compute, would be the harder
scale's real constraint. Exact-match rate — the one metric that was tight
across seeds at 8 frames (19.3%-22.0%) — became far noisier at 16 frames
(8.7%-33.3%), an unexplained finding reported honestly rather than
smoothed over. Full traces in
[its three run records](04-longer-sequences/runs/).

[Stage 05](05-multi-object/) tests the other half of the same named
follow-on: two independently-moving, occluding shapes composited into one
scene, still at 8 frames. Nothing in `video_codec.py` or `video_lm.py` was
reimplemented — the new code is a compositor and an occlusion-measurement
function in this stage's own dataset generator. All 3 seeds closed `MET`
(`lm_completion` MSE beats frame-repeat by roughly 6.8x the run-to-run
spread), but reconstruction quality is measurably worse than the
single-object case (mean MSE 0.1483 vs 0.0851) and exact-match rate both
fell and became far noisier across seeds (0.67%-28.67%, vs 19.3%-22.0% at
one object) — the tokenizer's one-token-per-frame capacity, not compute, is
the binding constraint along this axis too, the same pattern stage 04 found
along the frame-count axis. Full traces in
[its three run records](05-multi-object/runs/).

[Stage 06](06-longer-and-multi-object/) runs both axes together, so all four
corners of the frames-by-objects grid exist and any two of them differ by one
change. In pixel space the difficulties do not add: 16 frames with 2 objects
lands at 0.1375-0.1456 MSE, inside the range the second object alone already
cost, and doubling the frame count is close to free once the codec is
per-frame. In token space they compound to the floor -- exact-match falls to
0.00%-0.67%, and its seed-to-seed spread collapses with it, which reframes the
noisy exact-match both earlier stages reported as a mid-range artifact of an
all-or-nothing metric rather than a property of the task. All 3 seeds closed
`MET` at 22%-27% of the declared ceiling, and the model-to-oracle gap of
0.0001 on one seed says again that the tokenizer, not the sequence model, is
what is missing. Full traces in
[its run record](06-longer-and-multi-object/runs/2026-08-05-longer-and-multi-object.md).



## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-synthetic-video-dataset` | The state space that multiplied the collisions away | [when-the-collision-is-one](00-synthetic-video-dataset/when-the-collision-is-one/) |
| `00-synthetic-video-dataset` | The seed is the answer key | [when-the-seed-is-the-answer](00-synthetic-video-dataset/when-the-seed-is-the-answer/) |
| `01-video-tokenizer` | What is the discrete thing a video model conditions on? | [what-a-video-token-is](01-video-tokenizer/what-a-video-token-is/) |
| `01-video-tokenizer` | Three collapses, one revive mechanism, 63/64 codes | [when-the-dead-codes-revive](01-video-tokenizer/when-the-dead-codes-revive/) |
| `02-generation-model` | The remaining gap belongs to the codec, not the sequence model | [the-margin-vs-the-ceiling](02-generation-model/the-margin-vs-the-ceiling/) |
| `02-generation-model` | When the tokens are wrong but the frames still reconstruct | [when-wrong-tokens-still-reconstruct](02-generation-model/when-wrong-tokens-still-reconstruct/) |
| `03-report` | The verdict that pairs cost with quality | [the-cost-quality-pair](03-report/the-cost-quality-pair/) |
| `03-report` | The feasibility verdict, read: quality margin and cost headroom | [when-the-cost-ceiling-is-roomy](03-report/when-the-cost-ceiling-is-roomy/) |
| `04-longer-sequences` | 4.3x cost for 2x frames | [when-the-cost-grows-faster](04-longer-sequences/when-the-cost-grows-faster/) |
| `04-longer-sequences` | Doubling the frames: what the same recipe says at 16 | [when-the-frames-double](04-longer-sequences/when-the-frames-double/) |
| `05-multi-object` | Two objects, one token per frame, and the margin still clears | [the-margin-that-holds](05-multi-object/the-margin-that-holds/) |
| `05-multi-object` | One token per frame, two objects: where the capacity limit shows | [when-two-shapes-share-a-token](05-multi-object/when-two-shapes-share-a-token/) |
| `06-longer-and-multi-object` | The fourth corner: 16 frames and 2 objects together | [when-the-axes-compound](06-longer-and-multi-object/when-the-axes-compound/) |
| `06-longer-and-multi-object` | Which axis costs the generation — and when does the metric hit zero? | [when-the-metric-hits-zero](06-longer-and-multi-object/when-the-metric-hits-zero/) |

## What this will not prove

Nothing about real-world video realism, coherence beyond a handful of frames,
or competitiveness with any production video-generation system. Nothing about
audio or sound-video synchrony. And if this mission closes on a compute
infeasibility finding rather than a trained model, that finding is scoped to
the compute lanes available at the time of the run — it says nothing about
what a larger GPU or a longer budget would make possible. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
