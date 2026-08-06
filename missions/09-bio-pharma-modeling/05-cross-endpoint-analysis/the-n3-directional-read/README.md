---
status: verified
level: applied
base: scratch
label: The n=3 directional read
verified: 2026-08-06
---

# Three endpoints, two directions, and the ceiling stated

**Question:** [stage 05's cross-endpoint analysis](../) reads the
three-endpoint pattern. This chapter reads the recorded JSON and asks what
the two directions do and do not establish.

**Before this:** [stage 05's cross-endpoint analysis](../) and its recorded
JSON.

## The pattern, read

The run ([record](runs/2026-08-06-directional-read.md)) reads the recorded
rows:

| endpoint | train+ | model spread | gap | verdict |
|---|---:|---:|---:|---|
| SR-MMP | 689 | 0.0159 | -0.0830 | descriptor wins |
| NR-PPAR-gamma | 118 | 0.0620 | +0.0037 | inconclusive |
| NR-ER | 628 | 0.0227 | +0.0265 | model wins |

variance vs positives: monotonic decreasing. Gap vs positives: not
monotonic.

## Two readings

**Scarcity decides where a winner can be seen, not who wins.** The model's
variance grows monotonically as positives shrink — PPAR's 118 positives
carry a 0.0620 spread, 4x SR-MMP's — and that variance is exactly what
swallows its tiny gap into "inconclusive." Scarcity explains the
no-verdict row. It does not explain the winners: SR-MMP and NR-ER both
resolve beyond spread, one each way, with positive counts that bracket
PPAR's. The gap direction is explicitly not monotonic.

**The monotonicity check is n=3 and directional — that is the stated
ceiling.** The recorded analysis says it itself: no correlation
coefficient is computed or implied. The finding is a legible pattern
(scarcest -> noisiest -> no verdict), not a fitted claim, which is the
honest limit of a three-endpoint comparison — and why the mission treats
it as a pattern to investigate, not a law.

## Evidence boundary

The recorded cross-endpoint JSON (three endpoints, three seeds each, the
mission's own verdict rule). It reads that artifact; it does not re-run.

## Check your mental model

Answer each before opening it.

**1. Why is the variance direction meaningful if the gap is not?**

<details>
<summary>Answer</summary>

Because they answer different questions. The variance direction says
scarcity makes the model noisier — a monotonic, legible pattern across
all three endpoints. The gap direction asks who wins, and it is not
monotonic because the winner depends on endpoint-specific structure, not
scarcity alone. The analysis separates the claim it can support (variance
scales with scarcity) from the one it cannot (scarcity decides winners).

</details>

**2. What does "directional" mean as an honest limit?**

<details>
<summary>Answer</summary>

That the pattern is read by eye across three points, not measured by a
fitted statistic. Three endpoints cannot support a correlation
coefficient with any meaning; the recorded analysis says so explicitly.
The honest claim is "the pattern holds in the direction scarcity
predicts," with the sample size stated — which is the difference between
a finding and an overclaim.

</details>

## Next

Back to [stage 05](../), or to
[what does scarcity decide, and what does it not](../when-scarcity-decides/)
which reads the same analysis's verdict side.
