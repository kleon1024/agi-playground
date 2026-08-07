---
status: verified
level: applied
base: scratch
label: When the score is on the surface
verified: 2026-08-07
---

# The score stays on the surface and misses real CTR

**Question:** [stage 41's creative selection](../) scores generated
variants. This chapter reads the executed calibration comparison and
asks what a surface score rewards.

**Before this:** [stage 41 — LLM creative generation](../) and its
executed generate-then-select model.

## The comparison, executed

The run ([record](runs/2026-08-07-score-is-on-surface-read.md)) scores
three creatives two ways:

| creative | surface score | measured CTR |
|---|---:|---:|
| Buy now | 0.9 | 0.02 |
| Run faster, pay less | 0.7 | 0.08 |
| Marathon shoes, 20% off | 0.6 | 0.06 |

Surface winner: Buy now. CTR winner: Run faster, pay less.

## The reading

The surface score rewards urgency — "Buy now" scores 0.9 — while the
measured CTR rewards specificity: "Run faster, pay less" converts at
0.08 against "Buy now"'s 0.02. The two metrics pick different winners,
and a launch that trusts the surface score ships the wrong creative.
The score has to be calibrated against real delivery before it decides;
an uncalibrated surface score is stage 16's pCTR problem repeated at
the creative level.

## The fix and its trade

The fix is to score against measured delivery, not surface appearance:
train the creative score on delivered-impression CTR, hold back a
rotation of creatives to keep collecting fresh measurements, and treat
the surface score as a prior that delivery evidence overrides. The
trade is that measured CTR arrives slowly and only for what was
actually delivered — a new creative has no measurement until it has
run, so the pipeline must either pay exploration impressions to learn
it or trust the surface prior and risk shipping the wrong creative.
That missing feedback loop is exactly what the CAMERA benchmark
standardizes in Mita et al. (2024, "Striking Gold in Advertising:
Standardization and Exploration of Ad Text Generation", ACL 2024,
aclanthology.org/2024.acl-long.54): ad text generation has no standard
evaluation, so generators are scored on whatever each lab invents,
which is how a surface score that flatters the writer survives instead
of a CTR that pays the bills. Stage 16's calibration discipline is the
same medicine at the creative level.

## Evidence boundary

The executed comparison over three declared creatives (illustrative,
deterministic, assumed scores and CTR). It demonstrates the mechanism;
real creative selection needs the calibrated CTR model and measured
delivery, which an online experiment provides.

## Check your mental model

Answer each before opening it.

**1. Why does the surface score prefer the creative that converts
worst?**

<details>
<summary>Answer</summary>

Because it scores what the surface looks like, not what users do.
"Buy now" is urgent and punchy, so a surface-level judge gives it 0.9 —
but its measured CTR is 0.02, the worst of the three. The specific
creative ("Run faster, pay less") sounds less punchy and scores 0.7,
yet converts four times better. The surface score rewards the message's
appearance; CTR rewards its effect.

</details>

**2. What has to happen before the score may decide?**

<details>
<summary>Answer</summary>

Calibration against real delivery — the same rule stage 16 established
for pCTR. The score's mapping to actual CTR has to be verified, not
assumed; otherwise the launch ships the surface winner and loses the
CTR winner's conversions. Stage 41's discipline is that generation and
scoring are only as good as the measured feedback that validates them,
which is exactly what the executed comparison exposes.

</details>

## Next

Back to [stage 41](../). The
[collapse detour](../when-the-generated-creative-is-identical/) shows
the failure upstream of the score: generation that leaves nothing
different to score.
