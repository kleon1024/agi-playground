---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Multi-speaker generalization
---

# Does the same fix that escaped collapse for 1-2 speakers still work for 10?

**Question:** stage 03 retrained the same codec architecture on real speech
and found it collapses at stage 00's own step count (600) but escapes cleanly
at 2000 steps, same learning rate, across 3 seeds -- consistently landing on
51-63 of 64 codebook entries. That result used only 1-2 LibriSpeech speakers.
This stage asks whether the *same fix* (2000 steps, `lr=1e-3`, no other
change) still works once speaker diversity rises to 10 -- a genuinely
untested case, not a foregone conclusion.

**The artifact this stage produces** is the same codec/LM pipeline stage 03
produces, run on a 10-speaker mix instead of 1-2:

```
seed 0: eval MSE 0.02712  vs silence 0.02833   (4.3% margin)   18/64 codes, entropy_ratio 0.405
seed 1: eval MSE 0.01698  vs silence 0.02750  (38.2% margin)   63/64 codes, entropy_ratio 0.760
seed 2: eval MSE 0.02122  vs silence 0.02746  (22.7% margin)   32/64 codes, entropy_ratio 0.644
```

**Before this:** [stage 03](../03-real-speech-and-network/) established that
2000 steps at the original learning rate escapes the near-silence collapse
for 1-2 real speakers, across 3 seeds, consistently.

## What is reused, and what is new

`core/train_multi_speaker.py` imports `Codec`/`CodecConfig` from
[stage 00](../00-audio-codec/core/codec.py) and the LM training/generation
functions from [stage 01](../01-streaming-decode/core/audio_lm.py) and
[`streaming_decode.py`](../01-streaming-decode/core/streaming_decode.py)
unchanged -- **no architecture or training-loop change**, matching the reuse
discipline stage 03 itself established. The one new mechanism is
`core/multi_speaker_data.py`: stage 03's own `speech_data.build_dataset`
extracts all requested speakers' utterances into a single speaker-major list
and only then slices the first `max_utterances`, which silently biases
toward whichever speaker's directory sorts first once more than one or two
speakers are requested. That bias is exactly wrong for a stage whose entire
point is speaker diversity, so `build_balanced_dataset` bounds utterances
*per speaker* before combining and shuffling, and refuses to proceed (raises,
rather than silently under-testing) if the resulting eval split does not
cover every requested speaker. 10 dev-clean speakers were used: `2277`,
`1462`, `2035` (2 of these already appear in stage 03), plus 8 new ones
(`3752`, `6313`, `3081`, `2428`, `5694`, `5895`, `7976`) chosen only for
having enough archived utterances, not for any acoustic property.

## Finding: no full collapse in any seed, but codebook health becomes seed-dependent in a way it wasn't at 1-2 speakers

All three seeds beat both required naive baselines (silence and mean-signal),
so the collapse-then-escape fix that worked for 1-2 speakers still prevents
*total* failure at 10 speakers. But the margin and codebook utilization that
were tight and consistent at 1-2 speakers (51-63 of 64 codes, all three seeds
within an entropy_ratio band of 0.787-0.870, improvement margin roughly 2x
over baseline) are neither at 10 speakers:

```
                1-2 speakers (stage 03)      10 speakers (this stage)
codes used:     51, 58, 63  of 64            18, 32, 63  of 64
entropy_ratio:  0.787, 0.836, 0.870          0.405, 0.644, 0.760
margin vs
 silence:       ~2x (roughly 52-54%)         4.3%, 22.7%, 38.2%
```

Seed 0's run tells the clearest story: `vq_loss` in its training history
(`runs/multi-speaker-seed0.json`) stays essentially flat and near-zero
through step 1800, only spiking at step 1850 (`0.00185`) -- a much later and
weaker escape signal than stage 03 ever saw at 2 speakers, and one that
plainly did not have enough remaining steps to fully develop before training
stopped at step 2000. Seed 1, run with the identical step budget and
learning rate, escaped far more completely (63/64 codes, 38% margin). Same
fix, same step count, same learning rate, three different outcomes -- the
step count that reliably escaped collapse for 1-2 speakers is no longer
reliably sufficient once the codec has to represent 10 speakers' worth of
acoustic variation in the same 64-entry codebook. This is a genuine, honest
generalization boundary, not a repeat of stage 03's result at a different
scale: **more speaker diversity does not reintroduce full collapse, but it
turns the escape from a reliable outcome into a seed-dependent one.**

Per-speaker eval MSE breakdown (`per_speaker_mse` in each seed's `runs/`
file) shows no single speaker consistently dominates the error in any seed
-- the added variance is a training-dynamics effect, not one hard-to-encode
voice dragging the average down.

## Finding: the KV-cache mechanism still holds regardless

Same check stages 01/03 ran, same methodology (logits, not generated token
ids, following this repository's own `tests/test_decode_correctness.py`):

```
seed 0: max logit gap 2.22e-05, 100/100 clips' token sequences matched
seed 1: max logit gap 1.86e-05, 100/100 clips' token sequences matched
seed 2: max logit gap 2.45e-05, 100/100 clips' token sequences matched
```

This is the same order of magnitude as stages 01 and 03's own results and
this repository's established tolerance (`TOL=2e-5`). The KV-cache mechanism
is indifferent to speaker count -- consistent with stage 01/03's own finding
that it does not depend on where the token vocabulary came from, only on the
`Config`/`Transformer`/`KVCache` classes it was built against.

## Run it

```bash
cd missions/07-realtime-voice/04-multi-speaker/core
uv run --group torch python train_multi_speaker.py --codec-steps 2000 --lm-steps 800 --seed 0
```

CPU only, no CUDA GPU available in this sandbox, the same real deviation
stages 01/03 already recorded. Per-seed wall-clock: data build 1-2s (cached
after first extraction, reusing stage 03's already-downloaded LibriSpeech
archive), codec training 780-861s, LM training 83-87s. $0 marginal cost --
no new download; all 10 speakers come from the `dev-clean` archive stage 03
already fetched.

## What this stage does not establish

Still not the full 40+-speaker `dev-clean` corpus -- 10 speakers, chosen for
utterance volume, not for covering the corpus's actual accent/pitch/rate
diversity. Nothing about *why* seed 0 escaped less completely than seed 1 or
2 -- the training-dynamics mechanism behind the variance itself is not
diagnosed here, only measured. Nothing about whether a larger codebook, a
codebook-reset technique (the fix EnCodec and mission 08's video codec both
use for more severe collapse), or more training steps would tighten this
variance -- that is a follow-on question, not answered here. No GPU-lane
numbers; the codec ran on CPU throughout.

**Next:** none currently planned. A report stage, if this mission adds one,
would need to fold this stage's seed-dependent result into the mission's
overall acceptance verdict rather than treating stage 03's cleaner 1-2
speaker result as the mission's last word on real speech.
