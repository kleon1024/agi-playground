---
status: verified
level: applied
base: none
label: When the baseline holds
verified: 2026-08-06
---

# When does a ten-number baseline beat a trained model?

**Question:** [stage 01](../) fits logistic regression over ten
physicochemical descriptors against a trained SMILES model, and the mission
README's scoreboard spans three endpoints: descriptor wins, ties, loses.
This chapter assembles that scoreboard from the recorded runs, with the
seed spreads the verdicts depend on.

**Before this:** [stage 01's baseline and model](../), and the mission's
cross-endpoint analysis.

## The scoreboard, assembled

The run ([record](runs/2026-08-06-scoreboard.md)) reads all 18 recorded
checkpoints (3 endpoints x 2 arms x 3 seeds):

| endpoint | descriptor | model | margin | verdict |
|---|---:|---:|---:|---|
| SR-MMP | 0.8142 ± 0.0005 | 0.7312 ± 0.0080 | +0.083 | descriptor |
| NR-PPAR-gamma | 0.6554 ± 0.0022 | 0.6591 ± 0.0310 | -0.004 | inside spread |
| NR-ER | 0.6413 ± 0.0005 | 0.6679 ± 0.0113 | -0.027 | model |

## Three readings

**The scoreboard is per-endpoint, not a verdict about representations.** The
descriptor baseline wins on SR-MMP with the largest margin and the smallest
model variance (0.008); the model wins on NR-ER beyond its own spread
(0.011); PPAR is inside the model's seed spread (0.031) and has no winner.
The mission's stage 06 already separated features from learner on SR-MMP —
this table is the three-endpoint view that comparison sits in.

**The no-verdict row is the one with the largest confound.** PPAR is the
endpoint with the largest scaffold-split label shift (the split chapter's
+3.0pp test-positive shift) and the scarcest positives (2.3% train), and it
is the one where the model's seed spread (0.031) swallows any margin. The
scarcity, the split shift, and the inside-spread verdict are the same
confound measured three ways.

**The baseline's win is not the representation winning; it is the variance
not showing up.** On SR-MMP the descriptor baseline is nearly deterministic
(±0.0005) while the model varies (±0.008) — a small trained model on
SMILES characters with limited data is the noisier arm, and the baseline's
edge is partly that it is a stable, cheap, ten-number summary of the
molecule's obvious properties. That is the honest reading, not "simple beats
learned."

## The fix and its trade

The fix is the per-endpoint scoreboard with the confounds broken out:
descriptor wins on SR-MMP (0.8142 vs 0.7312, beyond a 0.008 model spread),
model wins on NR-ER (0.6679 vs 0.6413, beyond its 0.011 spread), and PPAR
is inside the model's 0.031 spread with no verdict. The trade is that the
per-endpoint view refuses the easy headline either way: "simple beats
complex" is wrong because the model wins on NR-ER, and "the model is
better" is wrong because it loses decisively on SR-MMP. The real reading —
the baseline wins where its near-determinism keeps a small signal visible,
and the model's variance (±0.008 vs ±0.0005) is what its edge is partly
made of — is more useful and harder to summarize, which is exactly why
the scoreboard is the fix rather than a single comparison.

## Who owns this loop

- **The evaluation owner** owns the 18-checkpoint scoreboard (3 endpoints
  x 2 arms x 3 seeds) and the per-endpoint verdict rule: a result only
  counts beyond the larger seed spread, applied to every row.
- **The model team** owns the variance story as the honest reading: the
  baseline's edge is partly stability, and the model's noisier arm is
  reported rather than hidden behind the NR-ER win.
- **The dataset owner** owns the scarcity/split-shift connection the
  no-verdict row exposes: PPAR is the largest label shift (+3.0pp) and
  the scarcest positives, which the split chapter measures and this
  scoreboard inherits.

## Evidence boundary

Three endpoints, three seeds each, the recorded ROC-AUCs; the verdict rule
is the mission's own (margin beyond the larger spread). It assembles the
recorded scoreboard; it does not re-train and does not explain why the model
is noisier — the representation-vs-learner decomposition is stage 06's
separate claim.

## Check your mental model

Answer each before opening it.

**1. Why is PPAR's comparison "inside spread" when the model's mean is
actually higher?**

<details>
<summary>Answer</summary>

Because the model's three-seed spread (0.031) is larger than its margin over
the baseline (-0.004). The mission's rule — a gap smaller than the run-to-run
spread is no result — says the model's edge could be seed noise. On a scarce
endpoint (2.3% train positives) the variance is large, which is the same
confound the split chapter's label shift and the mission's cross-endpoint
analysis name.

</details>

**2. The descriptor baseline wins on SR-MMP with a nearly zero spread. What
does that tell you about the baseline's nature, not just its score?**

<details>
<summary>Answer</summary>

That it is deterministic — logistic regression over ten fixed features has
no architectural randomness, so its seeds agree almost exactly (±0.0005).
Its win is partly stability: on limited data the trained SMILES model is
the noisier arm (±0.008), and a stable, cheap summary of the molecule's
obvious properties is hard to beat when the data is small. The score is
per-endpoint; the stability is a property of the baseline's simplicity.

</details>

## Next

Back to [stage 01's baseline](../), or to
[stage 06's representation grid](../../06-model-or-representation/) where
the SR-MMP win is decomposed into features versus learner.
