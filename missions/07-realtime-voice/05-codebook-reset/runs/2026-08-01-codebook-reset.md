# Codebook dead-code reset: does it fix stage 04's seed-dependent utilization?

## Commands

```bash
cd missions/07-realtime-voice/05-codebook-reset/core
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 0
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 1
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 2
```

Apple silicon laptop, macOS, CPU only (no CUDA GPU available in this
sandbox, same deviation from `mission.yaml`'s local-GPU-lane framing every
prior real-speech stage in this mission recorded). All three seeds launched
concurrently on a 10-core machine. Per-seed wall-clock: data build under
0.1s (reuses stage 04's `multi_speaker_data.build_balanced_dataset`, which
reuses stage 03's already-downloaded, git-ignored LibriSpeech `dev-clean`
cache — no new download), codec training 1256-1259s. $0 marginal cost.

## Codec: dead-code reset (every 50 steps, dead_threshold=1.0) vs stage 04's plain VQ

Same architecture, same balanced 10-speaker dataset, same step count (2000),
learning rate (1e-3), batch size (32), and seeds as stage 04 — only the
vector quantizer's dead-code-reset mechanism differs.

| seed | eval MSE | silence baseline | margin vs silence | codes used | entropy ratio | resets performed |
|---|---|---|---|---|---|---|
| 0 | 0.01875 | 0.02833 | 33.8% | 64/64 | 0.826 | 1893 |
| 1 | 0.01717 | 0.02750 | 37.6% | 64/64 | 0.814 | 1848 |
| 2 | 0.01733 | 0.02746 | 36.9% | 64/64 | 0.791 | 1388 |

Stage 04's plain-VQ result at the identical setup, for comparison:

| seed | eval MSE | silence baseline | margin vs silence | codes used | entropy ratio |
|---|---|---|---|---|---|
| 0 | 0.02712 | 0.02833 | 4.3% | 18/64 | 0.405 |
| 1 | 0.01698 | 0.02750 | 38.2% | 63/64 | 0.760 |
| 2 | 0.02122 | 0.02746 | 22.7% | 32/64 | 0.644 |

All three reset-codec seeds beat both required naive baselines (silence and
mean-signal). Codebook coverage is now 64/64 in every seed (vs. 18-63/64
without reset), and the reconstruction-margin spread tightened from
4.3%-38.2% to a narrow 33.8%-37.6% band. Full per-step `codec_history` and
`reset_log` (per-50-step reset counts) in
`reset-codec-seed{0,1,2}.json`. Reset activity is heaviest in the first ~200
steps (60-63 resets per 50-step window) and tapers to 1-3 by the run's final
few hundred steps. Total resets over 2000 steps: 1893 (seed 0), 1848 (seed
1), 1388 (seed 2).

## Data note

`core/train_reset_codec.py` imports `build_balanced_dataset`, `TEN_SPEAKERS`,
and `CLIP_LEN` from stage 04's `multi_speaker_data.py` unchanged, so the
dataset construction, speaker set, and per-speaker utterance bounds are
identical to stage 04's own run — the only variable under test is the vector
quantizer. This stage does not rerun stage 04's LM-training or
streaming-decode-correctness check; stages 01/03/04 already established the
KV-cache mechanism is indifferent to speaker count and to where the token
vocabulary came from, so repeating that check here would not test anything
new about the actual question (codebook health during codec training).
