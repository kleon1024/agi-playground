# Training the video-token LM, and checking it against the declared ceiling

This is the run `mission.yaml` frames as the actual feasibility decision:
"is a video tokenizer paired with a small autoregressive model buildable and
trainable inside this repository's real-run, declared-compute-lane
discipline at all." The interesting result is not just that the answer is
yes -- it is by how much compute headroom.

## Command

```bash
cd missions/08-video-generation/02-generation-model/core
uv run --group torch python train_generation.py --codec-steps 800 --lm-steps 400 --prompt-frames 4 --seed 0 --out ../runs
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Python | 3.12.9 (uv-managed), PyTorch (`--group torch`) |
| Repository HEAD at run time | `a2beecc` |

CPU only, no CUDA GPU available in this environment -- a real deviation from
`mission.yaml`'s "local GPU lane" framing, stated plainly rather than
assumed away, matching every other mission built this session. Local CPU
only, $0 real dollar cost -- no Modal spend for this stage.

## The declared compute ceiling, checked before it could be crossed

Per `mission.yaml`'s guardrail ("a declared compute ceiling is checked
before it is crossed, not after"), `train_generation.py` declares
`COMPUTE_CEILING_SECONDS = 1800` (30 minutes) before running, and checks
elapsed wall-clock after the codec retrain and again after LM training,
returning `CEILING_EXCEEDED` and stopping if either check fails.

```
codec retrain:     140.9s
LM training:          7.4s   (400 steps, a 4-layer, d_model=128 Transformer over 9-token sequences)
generation (eval):    0.05s  (150 clips, greedy, full-recompute, 4 new tokens each)
total:             152.5s
ceiling:          1800.0s
ceiling exceeded:  False   (8.5% of the declared budget used)
```

The infeasibility outcome `mission.yaml` explicitly allows as a legitimate,
mission-complete result did not occur -- this task, at this scale, is
comfortably feasible on the local CPU lane alone, with an order of magnitude
of headroom before the declared ceiling.

## Result: beats the frame-repeat baseline

Given the first 4 of 8 frames (real tokens from stage 01's codec), the LM
generates the remaining 4 tokens greedily; those decode to pixels and are
compared against the real remaining frames.

```
lm_completion (LM-generated tokens):        MSE 0.0804
oracle_tokens (true tokens, sanity check):  MSE 0.0779
frame_repeat_baseline (no learning):        MSE 0.1281

-> LM completion beats frame-repeat by 37.2%
-> LM completion is within 3.2% of the oracle (codec-only) ceiling
```

`frame_repeat_baseline` -- repeating the last conditioning frame's real
pixels for every unseen frame -- is the "no learning" control `mission.yaml`
names explicitly: since every clip's shape is in continuous motion by
construction (stage 00), a static repeat accumulates real positional error
every frame it is wrong for. The LM's completion lands close to the
oracle-tokens ceiling (the best stage 01's codec could do even with the true
future tokens), meaning most of the remaining gap to a lower MSE is stage
01's own reconstruction fidelity limit, not this stage's sequence model.

## A caveat the aggregate number does not show on its own

`predicted_token_sequence_exact_match_rate = 0.067` -- only 6.7% of eval
clips produce the exact same 4-token continuation as the true future. Pixel
MSE still beats the baseline decisively despite this, because stage 01's
codec reconstruction is a low-fidelity blur (documented in its own run
record): many different "wrong" token sequences decode to pixel patterns
close enough to the true frames that the aggregate MSE does not distinguish
them from the correct continuation. This stage's LM is doing real,
directionally-useful work -- it beats a genuine motion-aware baseline, not a
strawman -- but "beats frame-repeat in pixel MSE" and "predicts the exact
right future" are different, and only the weaker claim is established here.

## What this run does not establish

Nothing about real-world video, camera motion, multi-object scenes, or
sequences longer than 8 frames -- all outside stage 00's dataset by
construction. Nothing about the paged/continuous-batching serving layer --
generation here is plain full-recompute, since mission 07 stage 01 already
answered the KV-cache correctness/latency question for this repository's
decode mechanism on a different discrete-token modality, and this stage's
9-token sequences are far too short for that question to be interesting
again. The compute-feasibility finding above is scoped to this exact
dataset, codec, and model size on this local CPU lane at this point in time
-- it says nothing about whether a larger, more realistic video task stays
this cheap.
