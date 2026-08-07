# 16 frames and 2 objects at once: the fourth corner of the grid

## Commands

```bash
cd 07-multimodal-generation/video/06-longer-and-multi-object/core
uv run --group torch python train_longer_and_multi_object.py --seed 0
uv run --group torch python train_longer_and_multi_object.py --seed 1
uv run --group torch python train_longer_and_multi_object.py --seed 2
```

Defaults, unchanged from the two single-axis stages this is compared against:
`--frames 16 --speed 1 --train-clips 800 --eval-clips 150 --codec-steps 800
--lm-steps 400 --lm-lr 3e-3 --prompt-frames 8`.

Apple silicon laptop, macOS, CPU only (no CUDA GPU available in this sandbox —
the same deviation from `mission.yaml`'s local-GPU-lane framing every prior
stage in this mission recorded). Run 2026-08-05. The three seeds ran
**sequentially**, one after another, so each wall-clock below is uncontended;
stages 04 and 05 ran their seeds concurrently, which is why their wall-clock
spreads are wider than this stage's. \$0 marginal cost.

`--speed 1` rather than stage 00's default of 2, for the reason stage 04
recorded: at 16 frames, speed 2 leaves no valid start position on a 32px canvas
for several shape and direction combinations. Stage 04 uses the same value, so
the 16-frame rows are directly comparable.

## Dataset

Generated once per run from stage 05's `make_multi_example`, with the frame
count patched to 16. Identical across seeds — the clip seeds are `range(800)`
and `100000+`, independent of the training seed.

| Property | Value |
|---|---|
| Train clips | 800 |
| Eval clips | 150 |
| Frames per clip | 16 |
| Objects per clip | 2 |
| Dataset build wall-clock | 11.4s |
| Train-internal clip-hash duplicates | 0 |
| Eval candidates rejected for collision | 0 |
| Train/eval clip-hash collisions | 0 |

Occlusion, computed rather than assumed:

| Split | Clips with any occluded frame | Mean overlapping-pixel fraction | Max |
|---|---|---|---|
| Train | 661 / 800 (82.6%) | 0.96% | 7.13% |
| Eval | 128 / 150 (85.3%) | 0.77% | 4.69% |

## Frame-count bindings

Five modules take independent copies of `N_FRAMES` through `from ... import`.
All five were asserted equal before training, and the assertion is recorded:

```json
{"generate_video_dataset": 16, "generate_multi_object_dataset": 16,
 "video_codec": 16, "train_video_codec": 16, "train_generation": 16}
```

The 800 training and 150 eval clips were also checked to have been *written*
with 16 frames each (`clip_frame_counts_written: [16]`), so a disagreement
between the renderer and the loader could not pass silently.

## Result, per seed

| seed | LM completion MSE | oracle-token MSE | frame-repeat baseline | exact-match | verdict |
|---|---|---|---|---|---|
| 0 | 0.1391 | 0.1245 | 0.1998 | 0.00% | MET |
| 1 | 0.1375 | 0.1179 | 0.1998 | 0.67% | MET |
| 2 | 0.1456 | 0.1455 | 0.1998 | 0.67% | MET |

`MET` on all three seeds: `lm_completion` beats the frame-repeat baseline by
27–31%, several times the 0.0081 run-to-run spread. The baseline is identical
across seeds because it involves no training — it repeats frame 7 for all 8
remaining frames.

Model-to-oracle gap: 0.0146, 0.0196, 0.0001. The sequence model is close to the
best any sequence model could do given this codec's tokens, and on seed 2 it is
within 0.0001 of it.

## Compute

| seed | dataset | codec training | LM training | generation | total | ceiling |
|---|---|---|---|---|---|---|
| 0 | 11.4s | 466.5s | 15.5s | 0.19s | 494.3s | 1800s |
| 1 | 11.4s | 374.4s | 14.9s | 0.19s | 401.5s | 1800s |
| 2 | 11.4s | 377.8s | 18.0s | 0.19s | 408.3s | 1800s |

22.3%–27.5% of the declared ceiling used. `CEILING_EXCEEDED` was never reached.
Codec training is 93–94% of the total; the sequence model and the generation
pass together are under 4%.

## The four corners, for comparison

Every row is 3 seeds at the same 800/150 clip counts, 800 codec steps, 400 LM
steps, and half the clip as prompt. Rows 1–3 are read from the run records of
[stage 02](../../02-generation-model/runs/), [stage
04](../../04-longer-sequences/runs/), and [stage
05](../../05-multi-object/runs/) — no number is recomputed here.

| Frames | Objects | LM MSE range | baseline | exact-match range |
|---|---|---|---|---|
| 8 | 1 | 0.0804–0.0882 | 0.1281 | 6.67–22.00% |
| 16 | 1 | 0.0818–0.0892 | 0.1185 | 8.67–33.33% |
| 8 | 2 | 0.1429–0.1533 | 0.2193 | 0.67–28.67% |
| 16 | 2 | 0.1375–0.1456 | 0.1998 | 0.00–0.67% |

Note that exact-match at 8 frames is computed over 4 predicted tokens and at 16
frames over 8, so the 16-frame rows face a strictly harder all-or-nothing
target. That does not account for the last row on its own: stage 04 also
predicted 8 tokens and reached 33.33% on its best seed.

## Raw records

[`longer-and-multi-object-seed0.json`](longer-and-multi-object-seed0.json),
[`longer-and-multi-object-seed1.json`](longer-and-multi-object-seed1.json),
[`longer-and-multi-object-seed2.json`](longer-and-multi-object-seed2.json) —
each carries the full dataset report, occlusion statistics, frame-count
bindings, per-stage wall-clock, and the generation result. The
`generation-seed*.json` files beside them are `train_generation.run()`'s own
output, written by the reused stage 02 code path.
