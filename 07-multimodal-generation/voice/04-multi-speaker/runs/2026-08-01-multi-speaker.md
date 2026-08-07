# Multi-speaker codec retrain: does the 1-2 speaker fix generalize to 10?

## Commands

```bash
cd 07-multimodal-generation/voice/04-multi-speaker/core
uv run --group torch python train_multi_speaker.py --codec-steps 2000 --lm-steps 800 --seed 0
uv run --group torch python train_multi_speaker.py --codec-steps 2000 --lm-steps 800 --seed 1
uv run --group torch python train_multi_speaker.py --codec-steps 2000 --lm-steps 800 --seed 2
```

Apple silicon laptop, macOS, CPU only (no CUDA GPU available in this
sandbox, same deviation from `mission.yaml`'s local-GPU-lane framing stages
01/03 already recorded). Per-seed wall-clock: data build 1-2s (reuses stage
03's already-downloaded, git-ignored LibriSpeech `dev-clean` cache, no new
download), codec training 780-861s, LM training 83-87s. \$0 marginal cost.

## Codec: no full collapse in any seed, but codebook health becomes seed-dependent

Same architecture, same step count (2000) and learning rate (1e-3) that
escaped collapse reliably at 1-2 speakers (stage 03), rerun on a balanced
10-speaker mix:

| seed | eval MSE | silence baseline | margin vs silence | codes used | entropy ratio |
|---|---|---|---|---|---|
| 0 | 0.02712 | 0.02833 | 4.3% | 18/64 | 0.405 |
| 1 | 0.01698 | 0.02750 | 38.2% | 63/64 | 0.760 |
| 2 | 0.02122 | 0.02746 | 22.7% | 32/64 | 0.644 |

Stage 03's 1-2 speaker result at the same step count, for comparison:

| seed | eval MSE | silence baseline | margin vs silence | codes used | entropy ratio |
|---|---|---|---|---|---|
| 0 | 0.01306 | 0.02722 | ~52% | 58/64 | 0.836 |
| 1 | 0.01369 | 0.02827 | ~52% | 51/64 | 0.787 |
| 2 | 0.01309 | 0.02766 | ~53% | 63/64 | 0.870 |

All three 10-speaker seeds beat both required naive baselines (no full
collapse), but the margin (4.3%-38.2%, vs. a consistent ~52-53% at 1-2
speakers) and codebook utilization (18-63/64, vs. a consistent 51-63/64) are
both far more seed-dependent than at 1-2 speakers. Full per-step
`codec_history` in `multi-speaker-seed{0,1,2}.json` — seed 0's `vq_loss`
stays flat and near-zero through step 1800, only beginning to spike at step
1850, a materially later and weaker escape signal than any seed in stage 03
showed. Per-speaker eval MSE breakdown (`per_speaker_mse` in each JSON) shows
no single speaker dominates the error in any seed.

## KV-cache correctness: holds regardless of speaker count

| seed | max logit gap | mean logit gap | token sequences matched |
|---|---|---|---|
| 0 | 2.22e-05 | 7.80e-06 | 100/100 |
| 1 | 1.86e-05 | 8.37e-06 | 100/100 |
| 2 | 2.45e-05 | 9.39e-06 | 100/100 |

Same order of magnitude as stages 01/03's results and this repository's
established tolerance (`TOL=2e-5` in `tests/test_decode_correctness.py`).

## Data note

`multi_speaker_data.build_balanced_dataset` bounds utterances per speaker
before combining (stage 03's `speech_data.build_dataset` extracts
speaker-major and slices `max_utterances` after combining, which would have
silently under-represented most of the 10 requested speakers). It also
raises rather than proceeds if the eval split ends up missing a requested
speaker — this guard fired during development at under-sized
`n_train`/`n_eval` values and was left in as a permanent check, not removed
once the run passed.
