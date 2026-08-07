---
status: verified
level: applied
base: scratch
label: LLM creative generation
verified: 2026-08-07
---

# The surface score picks the creative that does not convert

**Question:** stage 26 chose between human-made creatives. This stage
asks what changes when an LLM generates the creative itself and answers:
generation is cheap but impressions are not — the model produces many
variants and a scoring model picks the one that gets delivered. The
frontier failure is that the score is a surface judgment and the
delivery is measured in CTR, and the two pick different winners.

**Before this:** [stage 26 — creative selection](../26-creative-selection/)
for the selection problem, and [stage 15 — eCPM
ranking](../15-ecpm-ranking/) for the score that decides which creative
is worth an impression.

## The generate-then-select run, executed

The run ([record](runs/2026-08-07-llm-creative-generation.md)) scores
four generated variants:

| score | variant |
|---|---:|
| 0.08 | Run faster, pay less |
| 0.06 | Marathon shoes, 20% off |
| 0.04 | New season, new pace |
| 0.02 | Buy now |

Selected: Run faster, pay less.

## The mechanism, named

The LLM generates candidate copy; a scoring model — stage 15's eCPM
machinery — ranks the variants; only the winner is delivered. The
asymmetry is the point: generating a variant costs tokens, showing an
impression costs reach and revenue, so the pipeline spends the cheap
step freely and gates the expensive one behind the score. The frontier
risks are that generation collapses to identical variants — leaving the
scorer nothing to pick — and that the score rewards surface appeal
instead of measured CTR, which the audits below price.

## The failure mode, named and audited

**The surface score picks the creative that does not convert.** The
audit ([record](runs/2026-08-08-score-ctr-gap.md)) draws 5,000 batches
of 10 generated variants and scores each with a surface mix — 60
percent true-signal proxy plus 40 percent appeal junk that predicts
nothing:

| metric over 5,000 batches of 10 variants | value |
|---|---:|
| surface selection != CTR-best creative | 55.1% |
| mean relative CTR loss from selection | 7.3% |
| mean chosen CTR vs best CTR | 0.0848 vs 0.0914 |

The verdict is measured: **THE SURFACE SCORE PICKS THE CREATIVE THAT
DOES NOT CONVERT.** A surface-appeal component of 0.40 is enough to
make the score miss the CTR-best creative in 55.1 percent of batches
and give up 7.3 percent of delivered CTR on average. The score is only
a delivery prediction when it is calibrated on measured CTR — the same
rule stage 16 established for pCTR — otherwise the creative team tunes
a score that does not predict what the delivery loop pays for.

**The generator re-emits the winners, and the cohort has seen them.**
The [generator-collapse detour](when-the-generator-collapses-to-the-train-set/)
measures the upstream failure: a mode-seeking generator re-emits the
historical top ads, so the scorer keeps delivering creative the cohort
has already seen. At collapse 0.6 the delivered CTR falls from 0.0911
to 0.0515, 59.8 percent of deliveries re-run seen copy, and the flight
decays 0.0406 from its first block to its last — the creative wears out
at generation time, before a single new impression is bought.

**The generated creative collapses to near-identical variants.** The
[identical-variants detour](when-the-generated-creative-is-identical/)
reads the message-level collapse: three generated variants normalize to
two distinct messages, so selection is choosing between a copy and a
punctuation edit, and the scoring step is decorative.

## Who owns the loop

Generation, selection, and delivery are owned by three different
teams, and each owner is tied to one of the failure modes above:

- **The generation and LLM team** owns the generator, its diversity
  controls, and the collapse of output toward the training corpus. It
  owns the mode-seeking failure — the executed fatigue audit's 33 to
  60 percent re-run share is a generator defect before it is a
  delivery problem, and temperature and repetition penalties are its
  levers (Keon et al. 2025, "Galton's Law of Mediocrity",
  arXiv:2509.25767, for the regression-to-the-mean measurement).
- **The creative selection and ranking team** owns the score that
  picks the delivered variant. It owns the surface-score failure —
  the 55.1 percent mismatch rate is a calibration defect, and the
  score only earns its authority by being trained on delivered
  impressions, the CAMERA-benchmark feedback loop Mita et al. (2024,
  "Striking Gold in Advertising", ACL 2024) standardize because ad
  text generation otherwise has no evaluation to score against.
- **The delivery and ads-intelligence team** owns measured CTR and the
  fatigue it records. It owns the feedback side — the score's
  calibration data, the flight-level CTR the audit prices, and the
  per-ad exposure counts that turn re-runs into wearout, which is why
  the delivery team's measured numbers are what the other two teams'
  levers are judged on.

When the ownership is implicit, the generation team ships novel-looking
copy, the selection team ships a confident score, and the delivery team
ships a CTR that neither predicted — each side correct within its own
definition, wrong for the loop as a whole.

## Why this belongs in the mission

Creative is the ads surface the user actually sees, and LLM generation
changes its economics: supply stops being a fixed catalogue and becomes
on-demand. That is the mission's frontier claim for the ad surface —
but the funnel's discipline still applies. Selection is only as good as
the score, and the score is only as good as the measured delivery, which
is the same calibration rule stage 16 established for pCTR.

## Evidence boundary

The executed scoring over four declared variants and the two audits
over declared distributions (illustrative, deterministic, fixed seed,
assumed generation, scores, and fatigue factor) demonstrate the
mechanism and its error rate; real creative generation needs the model,
the scoring model, and measured CTR over delivered impressions. The Keon
et al. and Mita et al. citations are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why can a score that looks reasonable pick the creative that
converts worst?**

<details>
<summary>Answer</summary>

Because the score rewards what the surface looks like, not what users
do. The audit mixes 40 percent appeal junk into the score and the
selection misses the CTR-best creative in 55.1 percent of batches,
giving up 7.3 percent of delivered CTR. Generation is cheap and
delivery is expensive, so the cheap step spends freely and the
expensive one is gated behind a score that has to be calibrated on
measured CTR before it may decide.

</details>

**2. What makes the scorer repeat the same creative even when its
score is honest?**

<details>
<summary>Answer</summary>

Because the generator's preferred mode is the corpus — the copy that
already worked — and the scorer rates that copy highly, so the winner
is delivered again to a cohort that has already seen it. In the fatigue
audit the scorer picks the highest latent CTR and is never wrong about
that; the collapse is upstream in generation, and the cohort's
response decays with each re-run — 0.0406 of delivered CTR inside a
flight at collapse 0.6.

</details>

**3. Why is the generation step not free even though it costs only
tokens?**

<details>
<summary>Answer</summary>

Because the cheap step decides what the expensive step can deliver. A
generator that collapses to identical variants leaves the scorer
nothing to pick; a generator that re-emits the historical winners
spends the cohort's attention on copy it has already seen; a score
that rewards surface appeal ships the wrong creative. The audit prices
each: 55.1 percent selection mismatch, 33 to 60 percent re-run share,
7.3 percent CTR loss — the token cost of generation is the smallest
part of what generation actually costs.

</details>

## Next

The frontier ads track continues. Next is [stage 42 — marketplace
economics](../42-marketplace-economics/), where the platform's cut is
the decision.

A detour from here: [the generator collapses to the train
set](when-the-generator-collapses-to-the-train-set/) — the executed
fatigue sweep read: at collapse 0.6 delivered CTR falls from 0.0911 to
0.0515 and 59.8 percent of deliveries re-run copy the cohort has
already seen, so the creative wears out at generation time.

Another detour: [the score stays on the surface and misses real
CTR](when-the-score-is-on-surface/) — the executed read: the surface
winner "Buy now" scores 0.9 against a 0.02 measured CTR, while the
specific creative at 0.7 surface scores 0.08 measured, so the score has
to be calibrated against real delivery.

Another detour: [the generated creative collapses to near-identical
variants](when-the-generated-creative-is-identical/) — the executed
normalization read: three variants collapse to two distinct messages,
so selection is choosing between a copy and a punctuation edit.
