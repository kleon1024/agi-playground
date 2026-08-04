---
status: verified
level: applied
base: scratch
verified: 2026-07-31
label: Generation model
---

# Is a video tokenizer plus a small sequence model even buildable here?

**Question:** `mission.yaml` frames this mission's real decision as
feasibility, not quality: "is a video tokenizer paired with a small
autoregressive or diffusion model buildable and trainable inside this
repository's real-run, declared-compute-lane discipline at all." This stage
is where that question gets answered on real hardware, against a compute
ceiling declared before the run.

**The artifact this stage produces** is one held-out clip's completion:
given its first 4 (of 8) real frames, the model generates the remaining 4
autoregressively, and those decode back to pixels through stage 01's codec.

**Before this:** [stage 01](../01-video-tokenizer/) -- the codec whose
64-way token vocabulary this stage's sequence model is trained over.

## What is reused, and what is new

`Config` and `Transformer` are imported directly, unmodified, from
[mission 01's pretraining core](../../01-language-model-agent/02-pretrain/core/model.py)
-- the same RoPE/RMSNorm/SwiGLU/GQA decoder mission 05's vision fusion and
mission 07's audio LM already reuse for a non-text vocabulary, with
`vocab_size` set to this stage's 65-symbol alphabet (stage 01's 64 codes
plus one `BOS` marker, the same convention mission 07 stage 01 uses). **No
line of `model.py` was changed.** Stage 01's codec is retrained in-process,
deterministically, with its exact official recipe -- it never saved model
weights, only its result JSON and example frames, the same "retrain, don't
checkpoint" convention mission 07 stage 01 uses for its own audio codec.

## The declared ceiling, checked before it could be crossed

Per `mission.yaml`'s guardrail, this stage declares a 30-minute local-CPU
compute ceiling *before* running, and checks elapsed wall-clock after both
the codec retrain and the LM training step, ready to stop and report
`CEILING_EXCEEDED` -- a legitimate, mission-complete outcome `mission.yaml`
names explicitly -- rather than silently shrinking the task to fit. It did
not fire:

```
codec retrain:  140.9s
LM training:      7.4s
generation:       0.05s
total:          152.5s   /   1800.0s ceiling  (8.5% used)
```

## The result

```
LM completion (4 real frames -> 4 generated):  MSE 0.0804
oracle (all 8 real tokens, sanity check):       MSE 0.0779
frame-repeat baseline (no learning):            MSE 0.1281

-> LM completion beats frame-repeat by 37.2%, and lands within 3.2% of the
   oracle ceiling -- most of the remaining gap is stage 01's own
   reconstruction fidelity limit, not this stage's sequence model.
```

`frame-repeat` -- hold the last conditioning frame's real pixels static for
every unseen frame -- is a genuinely motion-aware baseline here, not a
strawman: since stage 00 built every clip as continuous motion, a static
repeat accumulates real positional error every frame it stays wrong.

**A caveat the MSE alone does not show**: only 6.7% of eval clips get the
*exact* right 4-token continuation
(`predicted_token_sequence_exact_match_rate`), even though pixel MSE beats
baseline decisively. Stage 01's codec reconstruction is a documented,
low-fidelity blur, so many "wrong" token sequences still decode close enough
to the true frames that aggregate MSE cannot tell them apart from the
correct continuation. This stage's LM is doing real, directionally useful
work -- beating a genuine motion baseline, landing near the oracle ceiling
-- but "beats frame-repeat in pixel MSE" and "predicts the exact right
future" are different claims, and only the weaker one is established here.

Training uses teacher forcing: at every position the model predicts the next
token conditioned on the true preceding tokens, so a wrong prediction at step
`t` never affects what the model sees at step `t+1` during training. Greedy
generation at inference time has no such guarantee -- each new token is
appended and fed back in, so a wrong token changes what the model conditions
on for every step after it, the standard exposure-bias gap for autoregressive
models. `oracle_tokens` MSE decodes the true future tokens through the codec
(no generation, no compounding, a pure measure of stage 01's reconstruction
floor); `lm_completion` MSE decodes the model's own greedily-generated
tokens, only 3.2% higher, because stage 01's codec is a low-fidelity blur --
a wrong predicted token often decodes close enough to the true frame that
pixel MSE barely notices. `predicted_token_sequence_exact_match_rate`
measures the same sequence in token space instead, where a compounded wrong
choice is not forgiven by a blurry decoder, which is why the two metrics
diverge so sharply on the same run.

<!-- interactive: SeedSpreadBands -->

Pairing a discrete video codec with a causal transformer over its tokens is
the same two-stage design VideoGPT (Yan et al., 2021) used for real video;
the exposure-bias gap this section derives is older still, standard in
sequence-to-sequence literature since Bengio et al.'s scheduled-sampling
paper (2015), which this mission's greedy decoder does not use -- a
documented scope limit, not an oversight.

## Run it

```bash
cd missions/08-video-generation/02-generation-model/core
uv run --group torch python train_generation.py --codec-steps 800 --lm-steps 400 --prompt-frames 4 --seed 0 --out ../runs
```

CPU only, ~153s wall-clock, \$0. Full trace:
[`runs/2026-07-31-generation-training.md`](runs/2026-07-31-generation-training.md).

Two further seeds confirm this is not a lucky single draw:
`--seed 1` gives `lm_completion` MSE `0.0865` (exact-match `22.0%`), `--seed 2`
gives `0.0882` (exact-match `19.3%`) -- both still decisively beat the fixed
`0.1281` baseline. Across all three seeds, the run-to-run spread (`0.0078`)
is far smaller than the margin over baseline (`0.0430`), which is what
`mission.yaml`'s acceptance bar requires. Raw results:
[`runs/generation-seed1.json`](runs/generation-seed1.json),
[`runs/generation-seed2.json`](runs/generation-seed2.json).

## What this stage does not establish

Nothing about real-world video, camera motion, multi-object scenes, or
sequences longer than 8 frames -- all outside stage 00's dataset by
construction. Nothing about the paged/continuous-batching serving layer --
generation here is plain full-recompute (9-token sequences are far too short
for the KV-cache latency question mission 07 stage 01 already answered on a
different modality to be interesting again). The compute-feasibility finding
above is scoped to this exact dataset, codec, and model size on this local
CPU lane right now -- it says nothing about whether a larger, more realistic
video task stays this cheap.

**Next:** stage 03 holds every result across this mission against
`mission.yaml`'s acceptance bar and reports a verdict.
