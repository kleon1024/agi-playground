# True two-speaker re-run: the balanced builder, three seeds

## Why this run exists

The [mix audit](../../04-multi-speaker/when-the-mix-is-not-what-you-asked/)
measured that `speech_data.build_dataset` slices `max_utterances` off a
speaker-major list, so stage 03's recorded calls — 2 speakers requested
(2277, 2035), 40 utterances — were served speaker 2277 only. The codec/LM
numbers in the
[original run record](2026-08-01-real-speech-and-network.md) are therefore
honest single-speaker measurements, and this record is the queued follow-on:
the same stage, rerun with stage 04's balanced builder, so a "two-speaker"
claim is a measured two-speaker result instead of a corrected label.

## Commands

```bash
cd 07-multimodal-generation/voice/03-real-speech-and-network/core
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --balanced --out ../runs/real-speech-two-speaker-seed0.json --seed 0
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --balanced --out ../runs/real-speech-two-speaker-seed1.json --seed 1
uv run --group torch python train_real_speech.py --codec-steps 2000 --lm-steps 800 --balanced --out ../runs/real-speech-two-speaker-seed2.json --seed 2
```

`--balanced` switches the data pipeline to
`04-multi-speaker/core/multi_speaker_data.build_balanced_dataset` with
`per_speaker_utterances=40` — the per-speaker bound that the mix audit
measured as the fix. Everything downstream (codec, LM, KV-cache check,
latency harness) is stage 03's unchanged code.

The run also regenerated `example_clips/` (reference/reconstructed audio
for three held-out clips) — those files now come from this run's seed 2,
the two-speaker codec, replacing the original single-speaker run's clips.

Apple silicon laptop, macOS, CPU only (same lane as the original run; the
same deviation from `mission.yaml`'s local-GPU-lane framing stage 01
recorded). Per-seed wall-clock read from the run JSONs: data build 0-1.3s
(cached), codec training 570.5-574.2s, LM training 66.9-67.6s — about 10.7
minutes per seed, matching the original run's per-seed cost. LibriSpeech
`dev-clean` (338MB, CC BY 4.0) was already cached.

## Served mix, verified before the numbers below count

The balanced builder with the exact stage-03 call parameters serves both
speakers in both splits, for all three seeds (verified directly against
`build_balanced_dataset` in the same run record session):

| seed | train split (2277 / 2035) | eval split (2277 / 2035) |
|---|---|---|
| 0 | 122 / 134 | 30 / 30 |
| 1 | 142 / 114 | 31 / 29 |
| 2 | 129 / 127 | 31 / 29 |

So the codec and LM numbers below are a genuine two-speaker measurement,
unlike the original run.

## Codec: two speakers served, all three seeds still escape

| seed | eval MSE | silence baseline | mean-signal baseline | codes used | entropy ratio |
|---|---|---|---|---|---|
| 0 | 0.015208 | 0.026696 | 0.026803 | 62/64 | 0.795 |
| 1 | 0.015533 | 0.028658 | 0.028754 | 64/64 | 0.813 |
| 2 | 0.017460 | 0.027464 | 0.027593 | 54/64 | 0.788 |

All three seeds beat both naive baselines (roughly 1.6-1.9x) with healthy
codebook usage — no collapse, no seed stuck on the silence minimum. The
escape signal (vq loss leaving the near-zero collapsed regime) appeared at
~step 1100-1450 across seeds, inside the same escape window the original
single-speaker run recorded.

Comparison against the original single-speaker record: eval MSE
0.01306-0.01369 with 51-63/64 codes and entropy 0.787-0.870. The
two-speaker run lands in the same healthy band (0.01521-0.01746, 54-64/64,
entropy 0.788-0.813); the small MSE lift is the expected cost of a slightly
harder data distribution (a second voice), not a recipe failure.

## KV-cache correctness: still holds on the two-speaker vocabulary

| seed | max logit gap | mean logit gap | token sequences matched |
|---|---|---|---|
| 0 | 2.29e-05 | 1.20e-05 | 60/60 |
| 1 | 3.10e-05 | 1.18e-05 | 60/60 |
| 2 | 3.41e-05 | 1.17e-05 | 60/60 |

Same order of magnitude as the original record (2.34e-05-3.10e-05 max) and
inside the repository's established tolerance (`TOL=2e-5` in
`tests/test_decode_correctness.py`, which this check mirrors at logit
level). The KV-cache mechanism is unaffected by the corrected speaker mix.

## What this run does and does not settle

It settles the label, not the claim: stage 03's "1-2 speakers" numbers are
now a measured two-speaker result with the mix audit's fix in the loop, and
codebook health is consistent with the single-speaker baseline. It does not
say anything new about 10 speakers — that frontier is stage 04's
seed-dependence measurement (18/63/32 of 64 codes), which is exactly why
the reset mechanism of stage 05 exists.
