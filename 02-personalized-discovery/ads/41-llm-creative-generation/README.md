---
status: verified
level: applied
base: scratch
label: LLM creative generation
verified: 2026-08-07
---

# Generate cheap, select before delivery

**Question:** stage 26 chose between human-made creatives. This stage
asks what changes when an LLM generates the creative itself and answers:
generation is cheap but impressions are not — the model produces many
variants and a scoring model picks the one that gets delivered.

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
instead of measured CTR, which the two detours price.

## Why this belongs in the mission

Creative is the ads surface the user actually sees, and LLM generation
changes its economics: supply stops being a fixed catalogue and becomes
on-demand. That is the mission's frontier claim for the ad surface —
but the funnel's discipline still applies. Selection is only as good as
the score, and the score is only as good as the measured delivery, which
is the same calibration rule stage 16 established for pCTR.

## Evidence boundary

The executed scoring over four declared variants (illustrative,
deterministic, assumed generation and scores). It demonstrates the
mechanism; real creative generation needs the model, the scoring
model, and measured CTR over delivered impressions, which the detours
quantify.

## Check your mental model

Answer each before opening it.

**1. Why is generating many variants cheap but showing them
expensive?**

<details>
<summary>Answer</summary>

Because generation consumes tokens and latency; delivery consumes
impressions, reach, and advertiser budget. A discarded variant costs
nothing but the generation, while a delivered creative occupies a slot
that could have shown something else — stage 18's displacement again.
That asymmetry is why the pipeline generates a batch and delivers one.

</details>

**2. What makes the scoring model the bottleneck instead of the
generator?**

<details>
<summary>Answer</summary>

The score decides which variant gets delivered, so the selection is only
as good as the score. If the score rewards surface appeal — urgency,
buzzwords — it ships the wrong creative, and if generation has already
collapsed to near-identical variants, even a perfect score chooses
between copies. The two detours are the two ways the bottleneck
appears.

</details>

## Next

The frontier ads track continues. Next is [stage 42 — marketplace
economics](../42-marketplace-economics/), where the platform's cut is
the decision.

A detour from here: [the generated creative collapses to
near-identical variants](when-the-generated-creative-is-identical/) —
the executed normalization read: three variants collapse to two
distinct messages, so selection is choosing between a copy and a
punctuation edit.

Another detour: [the score stays on the surface and misses real
CTR](when-the-score-is-on-surface/) — the executed read: the surface
winner "Buy now" scores 0.9 against a 0.02 measured CTR, while the
specific creative at 0.7 surface scores 0.08 measured, so the score has
to be calibrated against real delivery.
