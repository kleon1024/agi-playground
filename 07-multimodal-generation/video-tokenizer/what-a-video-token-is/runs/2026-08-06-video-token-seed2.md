# Run — video codec seed 2: what the token stream holds

**Date:** 2026-08-06
**Command:** `cd 07-multimodal-generation/video/01-video-tokenizer/core && uv run --group torch python train_video_codec.py --steps 800 --batch-size 16 --lr 1e-3 --seed 2 --out ../runs`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; the stage's own `video_codec.py` and
`train_video_codec.py` unmodified.
**Wall-clock:** 186s (800 steps).
**Cost:** \$0 (local lane).

## Purpose

The recorded seed-0 run ended healthy (63/64 codes). This run repeats the
same 800-step recipe on a second seed to measure what the token stream holds
and whether the codebook health the stage's fixes bought is seed-stable.
Output: `runs/video-codec-seed2.json` (committed beside this record).

## Metrics

| | seed 0 (recorded 2026-07-31) | seed 2 (this run) |
|---|---:|---:|
| steps | 800 | 800 |
| wall-clock | 136s | 186s |
| codebook usage | 63/64 | 49/64 |
| entropy ratio | 0.912 | 0.601 |
| eval MSE (codec) | 0.0788 | 0.0885 |
| baseline MSE (background / mean_frame) | 0.0944 / 0.0858 | 0.0944 / 0.0858 |

## Notes

- Both seeds avoid the full collapse mission 07's codec showed without a
  revival mechanism (15/64 at seed 7, same geometry class): the video
  codec's `init_codebook_from_data` plus `revive_dead_codes` keep the
  codebook alive. But health is still seed-dependent — 63/64 versus 49/64 —
  and reconstruction quality tracks it (0.0788 versus 0.0885).
- Seed 2's codec beats the background baseline (0.0885 < 0.0944) and
  roughly ties the mean-frame baseline (0.0858); seed 0 beat both. The
  margin over the cheap baselines is thin at this scale, which is exactly
  what the mission's cost-first framing says to expect.
- `tokens_per_clip` is not recorded in either JSON; the token structure is
  frames x spatial patches per clip, from the codec config (see the stage
  README's encoder downsampling).
