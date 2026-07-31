---
status: verified
level: applied
verified: 2026-07-31
label: Outcome report
---

# Does a video tokenizer plus a small sequence model clear this repository's own bar?

**Before this:** [stage 00](../00-synthetic-video-dataset/) built the
dataset, [stage 01](../01-video-tokenizer/) built the per-frame VQ-VAE codec
after three real training-collapse failures, and
[stage 02](../02-generation-model/) trained the sequence model over three
seeds, all beating the frame-repeat baseline.

This stage holds all three results against the contract
[`mission.yaml`](../mission.yaml) declared before stage 00 existed. It does
not get to soften the comparison after seeing the numbers.

## The contract, and the answer it produces

`core/report.py` reads stage 00's dataset run record, stage 01's codec
result, and stage 02's three seed results directly, and checks the primary
acceptance line mechanically -- beats frame-repeat by more than run-to-run
spread:

```
frame-repeat baseline (fixed, no learning):  0.1281
LM completion per seed:                       [0.0804, 0.0865, 0.0882]
LM completion mean:                           0.0851
LM completion run-to-run spread (max-min):    0.0078
margin (baseline - mean):                     0.0430

margin > spread (0.0430 > 0.0078) -> beats baseline outside seed noise, by
roughly 5.5x the spread it would need to clear

VERDICT: MET
```

This is only the second `MET` verdict among the five missions built this
session (after mission 07) -- missions 05 (vision) and 06 (game AI) both
closed `NOT MET` on their own honestly-reported results. Unlike mission 07's
"does an already-proven mechanism transfer" bar, this mission's primary claim
was closer to mission 06's -- "does training produce something that beats a
real baseline" -- and it did, on every one of the three seeds run, not just
on average.

## Why three seeds, not one

`mission.yaml` requires beating the baseline "by more than run-to-run
spread," which a single seed cannot establish -- the same requirement mission
06's GRPO acceptance check applies. Seeds 0, 1, and 2 each retrain both the
codec and the LM from scratch (the codec's own seed varies with the
generation seed, so codec quality itself is part of the measured spread, not
held fixed): `0.0804`, `0.0865`, `0.0882`. The spread this produces (`0.0078`)
is small relative to the margin over baseline (`0.0430`) -- the result is not
a coin flip that happened to land favorably once.

## The caveat the primary metric alone does not show

`predicted_token_sequence_exact_match_rate` per seed: `[0.067, 0.220, 0.193]`
-- noisier across seeds than the pixel-MSE result, and consistently low. This
is stage 01's own documented low-fidelity reconstruction showing through: many
"wrong" token sequences still decode close enough to the true frames that
pixel MSE cannot tell them apart from the correct continuation. This is not
part of `mission.yaml`'s acceptance line, but it is reported beside it per
this mission's own guardrail that a quality number never stands alone.

## Compute: the declared ceiling was never close to binding

```
seed 0: 152.5s   seed 1: 150.6s   seed 2: 153.9s   (all local CPU, $0)
ceiling: 1800.0s -- 8.4-8.6% used on every seed
```

The infeasibility outcome `mission.yaml` explicitly allows as a legitimate,
mission-complete result did not occur, on any seed. This mission's original
premise -- that video might not survive this repository's compute discipline
at all -- turned out not to be the binding constraint; the video tokenizer's
training difficulty (three real collapse failures, see below) was.

## Failure catalogue

Three real, sequential training-collapse failures preceded stage 01's working
codec, each with its own diagnostic (full trace in
[stage 01's run record](../01-video-tokenizer/runs/2026-07-31-codec-training.md)):
codebook-initialization collapse, dead-code entrenchment, and a decoder
`Tanh` that saturated to background white and blocked gradient regardless of
which code the decoder received -- the real bug, confirmed by feeding two
different codes into the decoder and measuring a 0.001 max output difference.
Stage 02 itself reported zero training failures across all three seeds.

## Run it

```bash
cd missions/08-video-generation/03-report/core
uv run python report.py
```

`report.py` refuses to print a verdict if any upstream artifact is missing --
it says `CANNOT DETERMINE` and names exactly which file is absent, the same
discipline this repository's other report stages already established.

## What this does not establish

Nothing about real-world video, camera motion, multi-object scenes, or
sequences longer than 8 frames -- all outside stage 00's dataset by
construction. Nothing about GPU-lane cost or latency, since no CUDA GPU was
available anywhere in this mission's build. And the compute-feasibility
finding is scoped to this exact dataset, codec, and model size on the local
CPU lane at this point in time -- it says nothing about whether a larger,
more realistic video task stays this cheap, per `mission.yaml`'s own
`does_not_prove`.
