---
status: verified
level: applied
base: scratch
verified: 2026-08-08
label: When the mix is not what you asked for
---

# The mix is not what you asked for

**Question:** stage 04 asked for ten speakers and got ten — but only because
it swapped in a balanced builder. The naive builder it replaced,
[`speech_data.build_dataset`](../../03-real-speech-and-network/core/speech_data.py),
slices the first `max_utterances` files off a speaker-major list, so a
ten-speaker request with a 40-utterance cap serves the first speaker's first
40 utterances and nothing else. This chapter measures the gap: the same
request through both builders, how far apart the served mixes are, and a
correction the measurement forces on [stage 03's](../../03-real-speech-and-network/)
own recorded runs.

**Before this:** [stage 04's multi-speaker run](../) and the codebook-health
detours ([the fix that did not generalize](../when-the-fix-did-not-generalize/),
[a seed-dependent codebook](../when-codebook-health-is-seed-dependent/)).

## The failure mode

`build_dataset` builds its clip list speaker by speaker — `_extract_speakers`
extends one flat list in the order of the requested speakers — and then
slices `flac_files[:max_utterances]`. The cap is not per speaker; it is per
*total utterances*. Speaker 2277 alone has 95 archived utterances, so any
cap at or below 95 with 2277 first in the request serves nothing but 2277.
The requested list is a promise; the slice decides what the model actually
sees. The [recorded run](runs/2026-08-08-mix-audit.md) makes each step
explicit:

| probe | request | served train | served eval |
|---|---:|---|---|
| stage 03's call | 2 speakers, 40 utterances | `2277` × 256 | `2277` × 60 |
| naive at stage sizes | 10 speakers, 40 utterances | raised: "only 388 clips... need 500" | — |
| naive, completing | 10 speakers, 40 utterances | `2277` × 200 | `2277` × 50 |
| balanced | 10 speakers, 10 per speaker | 10 speakers | 10 speakers |

## Finding: the loud failure misdiagnoses itself, and the completing failure is silent

Two of the three naive probes fail in ways that hide the real cause.

**Stage 03's recorded "1-2 speakers" runs were one speaker.** The stage
requested speakers 2277 and 2035 with the default 40-utterance cap and was
served 2277 only — probe A replays the exact call (256 train, 60 eval,
`max_utterances=40`) and both splits come back all-2277. Stage 03's codec
and LM numbers are a real measurement, on a real single speaker; the
two-speaker label overstates the data. The claim this chapter corrects, and
the follow-on that re-measures it, are described below.

**The loud failure points at the wrong fix.** At the ten-speaker stage sizes
the naive builder raises `only 388 real-speech clips available from 40
utterances ... need 500. Raise max_utterances or add a speaker.` The
suggested remedy (more data) does not touch the real cause (the slice).
The error is real; the guidance is not.

**The completing failure is silent.** At a size that fits in one speaker's
utterances, the same call completes with one speaker in both splits and no
warning — the worst case, because nothing flags it. The verdict row of the
run record reads `requested 10 ... served 1/1` next to `balanced ... 10/10`.

## Why the mix matters here specifically

Stage 04's question is whether the stage-03 escape from codebook collapse
generalizes to ten speakers, and its recorded answer is seed-dependent
health (18/63/32 of 64 codes across seeds). That answer is only meaningful
if the ten-speaker split actually contained ten speakers. With the naive
builder the experiment would have been "one speaker at two utterance
counts," and the seed-dependence would be attributed to the wrong cause.
The balanced builder makes the served mix match the claim, and its
eval-coverage guard — it raises unless every requested speaker appears in
the eval split — converts silent under-testing into a loud, correctly
targeted error.

## The fix and its trade

The fix is per-speaker bounds: request a bounded number of utterances *per
speaker* (`per_speaker_utterances`) before combining and shuffling, and
refuse to proceed if the eval split misses a requested speaker. The trade is
that a per-speaker budget caps how much data each speaker can contribute —
a pipeline that bounds per speaker can no longer grow the corpus by pointing
at one prolific speaker, and a balanced 10-speaker set is smaller than the
naive set would have been if it had worked. That is the correct trade when
the question is coverage of a category. When the question is raw scale on a
long-tailed corpus, the balance becomes weighted sampling — ESPnet ships a
category-power sampler for exactly the multi-category, multi-dataset
imbalance case, and Google's production ASR fairness work rebalances toward
underperforming speaker cohorts (oversampling with semi-supervised data;
[arXiv:2207.11345, 2022](https://arxiv.org/abs/2207.11345)) — not a fixed
per-speaker cap.

## Who owns this loop

The dataset-builder owner. A builder that silently changes the served
distribution is a correctness bug, not a tuning knob: the training run and
every downstream conclusion inherit the mistake. The corpus itself is
LibriSpeech `dev-clean` (Panayotov et al., ICASSP 2015,
DOI 10.1109/ICASSP.2015.7178964, CC BY 4.0) — the flaw is not the data but
the extraction contract. This is why stage 04's balanced builder carries the
split-coverage guard as a permanent check rather than a one-off assertion.

## Evidence boundary

The audit measures served speaker counts, not model quality: it does not
re-train anything, does not quantify how much the one-speaker mix changed
stage 03's codebook health (the stage-03 runs stand as measured on speaker
2277), and does not answer whether a per-speaker-weighted sampler would
tighten stage 04's seed-dependence — that is a follow-on, not measured here.
The correction to stage 03's recorded claim is a data-label correction, not
a re-run: the runs stay exactly as measured, and the stage's README and run
record now say the request was two speakers and the served mix was one.

## Check your mental model

Answer each before opening it.

**1. A training run asks for 10 speakers but serves 1. Where does this class
of bug hide?**

<details>
<summary>Answer</summary>

In the builder's slicing logic, not in the training loop — the model trains
on whatever tensor stack it receives, so the bug is invisible to every
downstream stage. The served distribution is only visible if someone counts
it; the requested list is not evidence.

</details>

**2. Why does an eval-split coverage guard matter more than a train-split
one?**

<details>
<summary>Answer</summary>

Eval is where the claim "works for N speakers" is tested. A train split
missing speakers trains a model that never saw them; an eval split missing
them makes the metric silently measure one speaker. The guard converts
silent under-testing into a loud error.

</details>

**3. When is a per-speaker cap the wrong tool?**

<details>
<summary>Answer</summary>

When the question is raw scale on a long-tailed corpus — a hard cap throws
away the tail's volume. Then weighted, category-aware sampling is the right
instrument; the cap is right when the experiment's claim is per-category
coverage.

</details>

## Next

Back to [stage 04's multi-speaker run](../), or to the
[codebook-health detours](../when-codebook-health-is-seed-dependent/). The
follow-on this chapter queues: re-run stage 03 with a per-speaker-bounded
builder (three seeds, roughly 35 minutes on this lane) so the "1-2
speakers" claim becomes a measured two-speaker result instead of a
corrected label.
