---
status: verified
level: applied
base: none
verified: 2026-07-31
label: Synthetic video dataset
---

# What makes a short clip scoreable without a single frame of real footage?

**Question:** before any tokenizer or generation model can be built, this
mission needs clips with a specific property: a seed condition (a short
prompt like "a red circle moving down_right") that fully determines what the
correct sequence of frames looks like, so a model's completion can be checked
against a real answer rather than judged by eye.

**The artifact this chapter produces** is one clip from the committed
fixtures — `vid-0`, "a yellow square moving down_right" — shown at frames 0,
3, and 7 (`Y`=yellow, `.`=background):

```
frame 0                              frame 3                              frame 7
................................    ................................    ................................
................................    ................................    ................................
................................    ................................    ................................
................................    ................................    ................................
................................    ................................    ................................
................................    ................................    ................................
................................    ................................    ................................
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
........YYYYYYY.................    ..............YYYYYYY...........    ......................YYYYYYY...
................................    ................................    ................................
```

The square moves 2 pixels right and 2 down every frame, for 8 frames — exactly
what `"down_right"` at a fixed speed means, and exactly what a later stage's
prediction can be checked against.

**Before this:** [why this mission exists](../README.md) — the compute-and-
feasibility question this whole mission is really asking, before any quality
claim is attempted.

## What is reused, and what is new

The single-frame drawing code — `_draw_circle`, `_draw_square`,
`_draw_triangle`, the shape/color tables, and the PPM writer — is imported
directly from
[mission 05 stage 00's `generate_dataset.py`](../../../01-language-model/vision/00-image-caption-task/core/generate_dataset.py),
unmodified, the same cross-mission `sys.path.insert` convention mission 07
uses for mission 01's serving engine. **No line of that file was changed.**
What this stage adds is entirely temporal: picking a start position and one
of 8 fixed directions such that a shape stays fully on a 32x32 canvas for all
8 frames of a clip — deterministic bounds arithmetic, not a new renderer.

## Why the collision problem here is smaller than mission 05's

Mission 05 stage 00 discovered that a single 32x32 image's state space (48
combinations for a one-shape image, before jitter) is small enough that
disjoint seed *ranges* still produced 116 pixel-identical train/eval
collisions, fixed only by rejection sampling and then widening the render
space with size/position jitter. This generator's per-clip space multiplies
shape, color, size, direction, *and* a continuous start position, and
requires all 8 frames of two clips to match for a collision, not just one
static image. The real run confirms the difference directly: rejection
sampling this time discarded a single eval candidate out of 150, not
hundreds. Full numbers in
[`runs/2026-07-31-dataset-gen.md`](runs/2026-07-31-dataset-gen.md).

A clip's identity is fixed by five choices: shape, color, half-size,
direction, and a continuous start position bounded so all 8 frames stay
on-canvas. Unlike mission 05's single static image, two clips only collide
if their hash matches across all 8 frames. The real run gives a way to
estimate the effective size of that space: with 800 train clips and 9
duplicate-hash pairs, the birthday-approximation collision rate
`k(k-1) / (2N)` solves to an effective space size `N ≈ 800² / (2×9) ≈
35,600` -- two orders of magnitude larger than mission 05's pre-jitter
single-image space of 48 combinations, which is why rejection sampling only
discarded a single eval candidate out of 150 here.

<!-- interactive: MotionRangeSampler -->

Procedurally generated shape-motion clips with a known ground truth are the
standard toy substrate for motion-prediction research precisely because they
cannot be found by memorizing web content -- Moving MNIST (Srivastava,
Mansimov & Salakhutdinov, 2015) established the pattern this mission's own
`mission.yaml` cites as its external baseline.

## The fix and its trade

The failure this stage exists to prevent is leakage between train and eval
that looks perfectly well-formed: mission 05's same-style static generator
collided 116 times on its first attempt because a 48-combination image space
is small enough that ~700 draws revisit the same image. This generator's
per-clip space multiplies shape, color, half-size, direction, *and* a
continuous start position, and requires two clips to hash-identically match
across all 8 frames — the recorded run puts the effective space near 35,600
(the birthday-approximation solve from 800 train clips and 9 duplicate-hash
pairs), two orders of magnitude larger, so rejection sampling discarded
exactly one eval candidate out of 150 instead of hundreds.

The fix is space widening by construction plus rejection sampling, and its
trade is scope for checkability: the collision headroom is bought with a
deliberately impoverished dataset — one flat-color shape translating in a
straight line at constant speed on a plain background, 8 frames at 32x32 —
so the seed, prompt, and motion dict together pin the exact correct frames.
That determinism is what makes a later completion mechanically checkable
instead of judged by eye, and the collision count is recorded rather than
assumed so a future dataset change cannot quietly shrink the space back.

## Who owns this loop

- **The dataset owner** owns the generator and its space: the collision
  count is an evidence record of the space's size, not an assertion of
  "no leakage," and a widened or re-seeded dataset is a correctness event
  for every downstream stage, not a tuning event.
- **The evaluation owner** owns the split and its audit: the 800/150
  train/eval split, the rejection count that proves the split is clean, and
  the seed manifest that lets any later stage verify a clip was generated
  from its declared seed — the same leakage guardrail mission 05
  established for images, applied to time.
- **The model team** inherits the scope limits: the fixed clip length,
  resolution, and single-object design are the contract the tokenizer and
  generation model prove feasibility against, and nothing in this stage
  licenses a claim about real video.

## Run it

```bash
cd 07-multimodal-generation/video/00-synthetic-video-dataset/core
uv run python generate_video_dataset.py dataset --train 800 --eval 150 --out ../data/raw
uv run python generate_video_dataset.py fixtures --fixtures 6 --out ../fixtures
```

CPU only, no network, no GPU, ~3s wall-clock, \$0.

## What this stage does not establish

Nothing about a trained model — no tokenizer or generation model has seen
this data yet; that is stages 01 and 02. Nothing about real-world video: every
clip is one flat-color shape translating in a straight line at constant
speed on a plain background, by construction. The fixed clip length (8
frames), resolution (32x32), and single-object-per-clip design are deliberate
scope limits so the next stage's tokenizer and the stage after that's
generation model have the smallest possible temporal problem to prove
feasibility on first, per `mission.yaml`'s own compute-feasibility framing.

**Next:** stage 01 turns this frame sequence into a discrete token sequence a
decoder can condition on — the first genuinely new mechanism this mission
needs.

A detour from here: [the seed is the answer
key](when-the-seed-is-the-answer/) — the fixture manifest read: the seed,
prompt, and motion dict together pin the exact correct frames, which is
what makes a completion checkable mechanically instead of by eye.

Another detour: [the state space that multiplied the collisions away](when-the-collision-is-one/) — the recorded run read: one rejected eval candidate vs mission 05's 116, because the per-clip space grew by two orders of magnitude.
