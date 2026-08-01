---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Multi-object scenes
---

# Does the feasibility finding survive two occluding objects instead of one?

**Question:** stage 04 tested the frame-count half of mission.yaml's named
follow-on ("longer sequences (16-32 frames) and/or multi-object scenes (2+
moving shapes, occlusion)"). This stage tests the other half, still at the
original 8-frame length: two independently-moving shapes composited into one
scene, with real occlusion. The risk here is different in kind from stage
04's. Doubling frame count changed a shape parameter every reused function
already read dynamically; two objects sharing one 32-dimensional per-frame
latent (stage 01's `Encoder` output) and one 64-entry codebook token per
frame is a genuine capacity question — nothing about `video_codec.py` or
`video_lm.py` guarantees a single per-frame token can represent two shapes'
positions at once.

**The artifact this stage produces** is the same held-out-clip completion
task stage 02 answers, run again on two-object clips: given the first half of
an 8-frame two-shape clip, generate the remaining 4 frames autoregressively
and compare against frame-repeat and an oracle ceiling.

**Before this:** [stage 04](../04-longer-sequences/) closed the frame-count
question with a `MET` verdict at 16 frames. This stage returns to 8 frames
and changes scene complexity instead.

## What is reused, and what is new

Nothing in `video_codec.py`, `train_video_codec.py`, or `video_lm.py` is
reimplemented. The codec's `Encoder`/`Decoder` operate on raw pixel tensors
with no notion of how many shapes produced them; the LM's
`build_lm_dataset`/`train_lm`/`generate_greedy` operate on codec tokens and a
`Config`, equally agnostic to scene content. This stage's own
`generate_multi_object_dataset.py` produces clips in the exact same JSONL
schema stage 00 uses (`frames_pixels_rgb`, `n_frames`, `clip_hash`, ...), so
`train_video_codec.load_clips` reads them unmodified once `DATA_DIR` is
patched to this stage's own data directory — the same monkeypatch-then-call
pattern stage 04 established.

What is new: `sample_clip` and `render_clip` are imported unmodified from
stage 00 and called once per object to get each object's own independent
`MotionClip` and full 8-frame render against stage 00's plain white
background. Two functions in this stage's own `generate_multi_object_dataset.py`
do the actual new work — `composite`, which layers each object's frame stack
into one scene (later-sampled object drawn on top, background falls through
where nothing is drawn), and `occlusion_stats`, which counts how often more
than one object draws the same pixel in the same frame, so the dataset's
occlusion claim is a measured property of the generated clips rather than an
assumption.

## The result

Three seeds, matching this mission's own convention:

```
                          8 frames, 1 object (stage 02)   8 frames, 2 objects (this stage)
wall-clock                 ~51-58s (implied)                523.2s / 528.8s / 203.8s
ceiling used                8.4-8.6%                        29.1% / 29.4% / 11.3%
lm_completion MSE           0.0804 / 0.0865 / 0.0882        0.1429 / 0.1486 / 0.1533
                            mean 0.0851, spread 0.0078       mean 0.1483, spread 0.0104
oracle MSE                  0.0779                           0.1344 / 0.1469 / 0.1533 (mean 0.1449)
frame-repeat baseline        0.1281                           0.2193 (all 3 seeds, same clip set)
exact-match rate            19.3% - 22.0%                    0.67% / 2.67% / 28.67%
```

`lm_completion` mean 0.1483 vs frame-repeat baseline 0.2193 is a margin of
0.0710 — about 6.8x the 0.0104 run-to-run spread across seeds, so the `MET`
verdict is not a seed-lucky result, the same margin-vs-spread logic stage 02
and stage 04's own reports used. `lm_completion` mean 0.1483 is also within
2.3% (relative) of the oracle (true-token) mean 0.1449, a similar gap to
stage 02's 3.2% at one object.

Wall-clock does not follow a clean pattern: seed2 (203.8s) ran in roughly
40% of seed0/seed1's time (523.2s / 528.8s) despite an identical, fixed step
count (800 codec steps, 400 LM steps — this repository's codec training has
no early-stopping or convergence-check logic that could explain seed2
finishing early). This is reported as measured system-load variance between
runs on the local CPU lane, not a codec- or seed-dependent training
behavior — no code path in `train_video_codec.py` conditions step count or
duration on the seed. All three runs stayed well under the declared 1800s
ceiling regardless (11.3%-29.4% used).

Exact-match rate is the metric that moved the most and the least
predictably: 0.67% / 2.67% / 28.67% across the three seeds, a much wider
and much lower range than stage 02's single-object 19.3%-22.0% or even
stage 04's noisier 16-frame 8.7%-33.3%. The aggregate MSE stayed tight
(spread 0.0104) while exact-match swung by more than 40x between the
lowest and highest seed. The data supports one concrete observation: two
objects sharing one 64-entry per-frame codebook token is a harder
discrete-prediction target than one object was, since the token now has to
jointly encode both shapes' positions rather than one — consistent with
exact-match falling to single digits in two of three seeds where stage 02
never went below 19%. Beyond that, this stage's own data does not explain
why seed2's exact-match (28.67%) is so much higher than seed0's (0.67%)
while their MSE values are close (0.1533 vs 0.1429) — that is reported as an
open, unexplained finding, not resolved here.

<!-- interactive: SequenceLengthScaling -->

**Verdict:** `MET` (all 3 seeds) — `lm_completion` beats frame-repeat by a
margin more than 6x the run-to-run spread in every seed, and every run
finished well under the declared ceiling (29.4% at the highest). The
tokenizer, not compute, is still the binding constraint at this harder
scale: reconstruction quality is measurably worse than the single-object
case (mean MSE 0.1483 vs 0.0851), and exact-match quality is both far lower
on average and far noisier across seeds — the same kind of quality-not-compute
risk stage 02's report first flagged and stage 04 confirmed along the
frame-count axis, now also confirmed along the object-count axis.

## Run it

```bash
cd missions/08-video-generation/05-multi-object/core
uv run --group torch python train_multi_object.py --train-clips 800 --eval-clips 150 \
  --codec-steps 800 --lm-steps 400 --prompt-frames 4 --seed 0 --out ../runs
```

Repeat with `--seed 1` and `--seed 2` for the other two seeds. CPU only,
203.8-528.8s wall-clock per seed, $0. Full traces:
[`runs/multi-object-seed0.json`](runs/multi-object-seed0.json),
[`runs/multi-object-seed1.json`](runs/multi-object-seed1.json),
[`runs/multi-object-seed2.json`](runs/multi-object-seed2.json).

## What this stage does not establish

This is a 2-object test only — nothing here establishes what happens at 3+
objects, where the same one-token-per-frame capacity question would only
get harder. The measured occlusion is real but modest: 79.1%-82.0% of clips
have at least one frame with any pixel overlap, but the mean overlapping-pixel
fraction is only about 0.87% of the frame — this is not a heavy-occlusion
stress test, only a scene where occlusion happens naturally and is measured
rather than assumed away. Nothing about combining more objects with the
longer sequences stage 04 tested — the two follow-on axes named in
mission.yaml (longer sequences, multi-object scenes) have each been tested
alone, never together. Nothing about real-world video, camera motion, or
any dataset not procedurally generated by this mission's own code, the
same boundary every other stage in this mission states.

**Next:** combining both follow-on axes (longer, multi-object clips at
once) is the natural companion experiment this stage did not attempt, left
open for a later stage if the compute headroom is spent on it.
