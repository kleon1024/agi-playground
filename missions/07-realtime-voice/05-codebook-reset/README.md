---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Codebook dead-code reset
---

# Does a standard dead-code reset fix the seed-dependent codebook health stage 04 found?

**Question:** stage 04 reran the fix that reliably escaped collapse for 1-2
speakers (2000 steps, `lr=1e-3`, no architecture change) on a balanced
10-speaker mix and found it never fully collapses, but codebook utilization
becomes sharply seed-dependent — 18-63 of 64 codes used across 3 seeds,
versus a tight 51-63/64 at 1-2 speakers. `mission.yaml`'s `does_not_prove`
named this as unresolved. This stage asks whether the standard fix for
exactly this failure mode — periodic dead-code reset (Razavi, van den Oord &
Vinyals, "Generating Diverse High-Fidelity Images with VQ-VAE-2," NeurIPS
2019) — actually closes the gap, on this codec, on this dataset. Not a
foregone conclusion: the technique is well-established for larger,
EMA-updated codebooks, not this mission's small straight-through VQ.

**The artifact this stage produces** is the same codec retrained on the
identical 10-speaker balanced mix stage 04 used, with one component
replaced: `core/reset_vq.py`'s `ResetVectorQuantizer` tracks an EMA
cluster-size count per codebook entry and, every 50 steps, reinitializes any
entry whose EMA count has fallen below 1.0 to a random encoder output from
the current batch plus small noise. Everything else — encoder, decoder,
optimizer, batch size, step count, learning rate, dataset, speakers, seeds —
is unchanged from stage 04.

```
seed 0: eval MSE 0.01875  vs silence 0.02833  (33.8% margin)   64/64 codes, entropy_ratio 0.826
seed 1: eval MSE 0.01717  vs silence 0.02750  (37.6% margin)   64/64 codes, entropy_ratio 0.814
seed 2: eval MSE 0.01733  vs silence 0.02746  (36.9% margin)   64/64 codes, entropy_ratio 0.791
```

**Before this:** [stage 04](../04-multi-speaker/) found the 1-2-speaker fix
still avoids full collapse at 10 speakers, but with codebook health
(utilization, margin) that swings wildly by seed.

## What is reused, and what is new

`core/reset_vq.py` imports `CodecConfig`, `Encoder`, `Decoder` from
[stage 00](../00-audio-codec/core/codec.py) unchanged — only the
`VectorQuantizer` is replaced with `ResetVectorQuantizer`. Deliberately only
the dead-code-reset piece is implemented, not a full EMA-updated codebook
(VQ-VAE-2's other mechanism); adding both at once would confound which one
did the work. `core/train_reset_codec.py` imports
`build_balanced_dataset`/`TEN_SPEAKERS`/`CLIP_LEN` from
[stage 04](../04-multi-speaker/core/multi_speaker_data.py) unchanged, so the
dataset, speaker set, and per-speaker utterance counts are identical to
stage 04's own run — this stage isolates the one variable under test (the VQ
mechanism) rather than also varying the data. This stage does not rerun the
LM/streaming-decode half of stage 04's pipeline: stages 01/03/04 already
established the KV-cache mechanism is indifferent to speaker count and to
where the token vocabulary came from, so repeating that check here would not
test anything new about the actual question — codebook health during codec
training.

## Finding: dead-code reset closes the seed-dependent gap stage 04 found

All three seeds now land on **64 of 64 codes used** — no seed-to-seed
variance left in raw codebook coverage, where stage 04 saw 18-63/64:

```
                10 speakers, no reset (stage 04)   10 speakers, dead-code reset (this stage)
codes used:     18, 32, 63  of 64                  64, 64, 64  of 64
entropy_ratio:  0.405, 0.644, 0.760                0.826, 0.814, 0.791
margin vs
 silence:       4.3%, 22.7%, 38.2%                 33.8%, 37.6%, 36.9%
```

Reconstruction quality also tightened: margin over the silence baseline is
now a narrow 33.8%-37.6% band across all three seeds, close to stage 03's
1-2-speaker consistency (~52-54%) and nowhere near stage 04's 4.3%-38.2%
spread. Every seed still comfortably beats both required naive baselines
(silence and mean-signal).

The mechanism visibly does the work: each seed's `reset_log`
(`runs/reset-codec-seed{0,1,2}.json`) shows a large burst of resets in the
first few hundred steps (around 60-63 of 64 codes reset in the very first
50-step check — consistent with most codes starting effectively unused right
after random init) that tapers to 1-3 resets per 50-step window by the last
few hundred steps, as the codebook settles into stable, broad usage. Total
resets over the full 2000-step run: 1893 (seed 0), 1848 (seed 1), 1388 (seed
2) — seed 2 needed noticeably fewer, but this does not line up with which
seed had the best *unreset* utilization in stage 04 (seed 1, at 63/64), so
the training-dynamics reason behind that difference is not diagnosed here,
only measured.

Entropy ratio (0.79-0.83) stays below the 1.0 ceiling a perfectly uniform
codebook would reach — every code is used, but not equally often — so this
finding is that dead-code reset eliminates *dead* codes, not that it
produces a perfectly uniform codebook. That distinction is not tested
further here.

## What this stage does not establish

Only the dead-code-reset half of VQ-VAE-2's fix was tested; whether adding
full EMA-updated codebook embeddings on top would tighten the entropy-ratio
spread further (0.79 vs 0.83) is not answered here — testing that would
require a second variant and risks confounding two mechanisms in one
experiment, which this stage explicitly avoided. Only one value each of
`reset_every` (50) and `dead_threshold` (1.0) was tried; no sweep establishes
whether these specific values are optimal or merely sufficient. Still 10
speakers, not the full 40+-speaker `dev-clean` corpus — whether reset holds
at greater speaker diversity is unknown. No re-check of the KV-cache
streaming mechanism in this stage; stages 01/03/04 already established it is
indifferent to codec internals, so this stage's dataset and codec changes
are the only variables tested. No GPU-lane numbers; the codec ran on CPU
throughout, same deviation from `mission.yaml`'s local-GPU-lane framing as
every prior real-speech stage in this mission.

<!-- interactive: CodebookResetComparison -->

## Run it

```bash
cd missions/07-realtime-voice/05-codebook-reset/core
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 0
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 1
uv run --group torch python train_reset_codec.py --codec-steps 2000 --seed 2
```

Apple silicon laptop, macOS, CPU only (no CUDA GPU available in this
sandbox, same deviation from `mission.yaml`'s local-GPU-lane framing every
prior real-speech stage in this mission recorded). Run 2026-08-01, all three
seeds launched concurrently on a 10-core machine: per-seed wall-clock, data
build under 0.1s (reuses stage 03's already-downloaded, git-ignored
LibriSpeech `dev-clean` cache via stage 04's `multi_speaker_data.py`, no new
download), codec training 1256-1259s. \$0 marginal cost. Full per-step
`codec_history` and `reset_log` in
[`runs/reset-codec-seed0.json`](runs/reset-codec-seed0.json),
[`runs/reset-codec-seed1.json`](runs/reset-codec-seed1.json), and
[`runs/reset-codec-seed2.json`](runs/reset-codec-seed2.json).
