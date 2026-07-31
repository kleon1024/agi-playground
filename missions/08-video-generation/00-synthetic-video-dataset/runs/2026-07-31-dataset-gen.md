# Generating the synthetic motion-clip dataset

First real run of `core/generate_video_dataset.py`. The interesting part is
not the 800/150 split — it is that mission 05 stage 00's own small-state-space
collision lesson reproduces here, at a smaller scale, for a completely
different generator: extending the render space along a time axis widens it
enough that only a single eval candidate needed rejecting, not hundreds.

## Command

```bash
cd missions/08-video-generation/00-synthetic-video-dataset/core
uv run python generate_video_dataset.py dataset --train 800 --eval 150 --out ../data/raw
uv run python generate_video_dataset.py fixtures --fixtures 6 --fixtures-seed-start 0 --out ../fixtures
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | none beyond the standard library (`random`, `hashlib`, `json`) plus a direct import of mission 05's `generate_dataset.py` for the drawing primitives |
| Repository HEAD | `7bcbcfe` |

CPU only, no network, no GPU, $0.

## Why the collision problem is smaller here than in mission 05

Mission 05 stage 00's single-frame image space was `4 cells x 3 shapes x 4
colors = 48` states for a one-shape image, small enough that ~700 draws
collided constantly (116 train/eval collisions on the first attempt, before
jitter widened the space to 3,600). This generator's per-clip state space is
`3 shapes x 4 colors x 3 half-sizes x 8 directions x (valid start positions)`
— the direction and continuous start-position choice alone multiply the space
by roughly two orders of magnitude over a single static image, even before
counting that two clips must match at every one of 8 frames, not just one, to
collide at all. The real run below confirms this directly.

## Real run: train 800 / eval 150

```
train clips    : 800
eval clips     : 150
frames/clip    : 8
wall-clock     : 2.716s
train-internal clip-hash duplicates: 9
eval candidates rejected for colliding with train (or a prior eval draw): 1
clip-hash collisions between train and eval (must be 0): 0
```

`make_eval_set_disjoint_from()` uses the exact rejection-sampling fix mission
05 stage 00 needed (advance the eval seed past its starting range, skip any
candidate whose hash already exists in train or in eval-so-far) — but here it
rejects a single candidate out of 150+1, not hundreds, because the render
space per clip is far larger. The 9 train-internal duplicates (out of 800) are
reported, not eliminated, matching mission 05's own disclosed limit: the
guardrail is about train/eval leakage, not train-internal repeats.

## Distribution, final run

```
train  n=800   directions: down_right 111, left 108, down_left 80, up_left 112,
               up_right 95, right 90, down 95, up 109
       shapes:  square 266, circle 279, triangle 255
       colors:  yellow 200, red 197, green 192, blue 211

eval   n=150   directions: up_right 23, up 14, right 16, left 21, down_right 18,
               down_left 13, up_left 23, down 22
       shapes:  circle 44, square 51, triangle 55
       colors:  yellow 37, green 36, blue 41, red 36
```

All 8 directions, 3 shapes, and 4 colors are present in both splits, roughly
proportional to their uniform sampling weights — no bucket collapsed to zero,
unlike mission 05 stage 00's first (pre-jitter) attempt.

Full manifests: `data/raw/train.jsonl` (121M), `data/raw/eval.jsonl` (20M) —
git-ignored, regenerate with the command above. Six committed example clips
(48 `.ppm` frames total) and their manifest: `fixtures/`.

## What this run does not establish

Nothing about a trained model — no tokenizer or generation model has touched
this data yet; that is stages 01 and 02. Nothing about real-world video —
every clip is one flat-color shape translating in a straight line on a plain
background, by construction, and the fixed 8-frame length, 32x32 resolution,
and constant per-clip speed are all deliberate scope limits, not incidental
ones. The state-space finding above is specific to this generator's canvas
size, shape/color/direction counts, and clip length — a longer clip or a
denser direction set would need its own collision check, not an assumption
that this run's numbers still hold.
