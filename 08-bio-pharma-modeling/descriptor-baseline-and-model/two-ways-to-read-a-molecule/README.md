---
status: verified
level: applied
base: scratch
label: Two ways to read a molecule
verified: 2026-08-06
---

# Ten numbers, or 696,065 parameters

**Question:** [stage 01's baseline and model](../) compared two ways of
turning a molecule into a number. This chapter dissects both structures
and asks what the recorded outcome says about each.

**Before this:** [stage 01's baseline and model](../) and its recorded
run.

## The two structures, read

The run ([record](runs/2026-08-06-representation-anatomy.md)) reads the
recorded seeds:

| | descriptor baseline | SMILES transformer |
|---|---|---|
| representation | 10 RDKit numbers | character-level string |
| learner | logistic regression | 4-layer transformer |
| parameters | ~10 + intercept | 696,065 |
| mean ROC-AUC | 0.8142 | 0.7312 |
| seed spread | 0.0010 | 0.0159 |
| wall-clock/seed | ~2s | ~105s |

<!-- interactive: RepresentationAnatomy -->

## The structures, named

The two approaches map the same molecule through different paths:

1. **Descriptor path** — RDKit computes ten physicochemical numbers
   (molecular weight, logP, H-bond donors/acceptors, and so on); a convex
   logistic regression maps those ten to a toxicity probability. The
   representation is a fixed human-chosen summary: cheap, interpretable,
   and blind to anything those ten numbers do not capture.
2. **SMILES path** — the molecule's string is tokenized into characters;
  a 4-layer transformer (52-character vocabulary, 696,065 parameters)
  learns which character sequences predict toxicity. The representation
  is learned, not chosen: it can express arbitrary string patterns, at
  the cost of 50x the parameters and 50x the wall-clock.

## The fix and its trade

The comparison is the fix: the same held-out split judged through two
different paths makes the representation choice the visible variable. The
trade is the cost asymmetry the table names — the descriptor path is
ten human-chosen numbers fitted by a convex learner (~10 parameters,
~2s/seed), while the SMILES path is 696,065 parameters and ~105s/seed,
50x both. The learned path's bet is that arbitrary string patterns carry
signal the ten numbers miss; the recorded outcome (0.8142 vs 0.7312, with
the model's 0.0159 spread 16x the baseline's 0.0010) is what the bet cost.
The chapter's job is to make the two paths comparable on the same split so
the loss is attributable to the representation/learner choice rather than
to a changed evaluation.

## Who owns this loop

- **The model team** owns the architecture and its cost profile: the
  SMILES path's 50x parameter and wall-clock cost is a decision the team
  made and the chapter reports, not a hidden tax.
- **The evaluation owner** owns the same-split comparability: both arms
  are judged on stage 00's scaffold split, which is what lets the 0.0830
  gap read as a representation finding rather than an artifact.
- **The dataset owner** owns the split both paths inherit; the descriptor
  baseline's near-determinism (±0.0010) and the model's variance
  (±0.0159) are both properties of the same data at different capacities.

## What the recorded outcome says about each

On SR-MMP the descriptor wins (0.8142 vs 0.7312) — and the anatomy explains
*why* it can win: it is a stable, cheap ten-number summary (spread 0.0010,
~2s/seed) whose convex learner has no seed sensitivity, while the
transformer's variance (spread 0.0159, ~105s/seed) is where the mission's
scarcity story begins. The comparison is not "simple beats neural" — it is
two representations with different bias/variance profiles, and on this
endpoint the fixed summary's stability beats the learned model's capacity.
The three-endpoint pattern (stages 03-05) is where that reading gets
tested.

## Evidence boundary

The recorded stage-01 run (SR-MMP, 3 seeds per arm, one scaffold split).
It reads those artifacts; it does not re-train and the descriptor's edge
here says nothing about other endpoints or larger data, per the mission's
own `does_not_prove`.

## Check your mental model

Answer each before opening it.

**1. The descriptor has ~10 parameters and beats a 696K-parameter model.
Why is that not "simple beats learned"?**

<details>
<summary>Answer</summary>

Because the comparison is between representations, not just learners. The
descriptor's ten numbers are a curated summary that a chemist chose; the
transformer starts from raw characters and must learn what matters. On
SR-MMP, the curated summary happens to capture the predictive structure,
and its convex learner is far more stable (spread 0.0010 vs 0.0159). The
headline is a bias/variance trade, not a demonstration that simplicity
wins — which is why the mission tests other endpoints before concluding
anything.

</details>

**2. Why does the transformer's variance matter for the verdict?**

<details>
<summary>Answer</summary>

Because the mission's rule is "a gap smaller than run-to-run spread is no
result." The transformer's spread (0.0159) is 16x the descriptor's
(0.0010) — so even a nominally better model mean could land inside its own
noise. The variance is not a footnote; it is the measurement that decides
whether a comparison is a win, a loss, or no result, and it scales with how
scarce the positive class is (the stage 03-05 pattern).

</details>

## Next

Back to [stage 01's baseline and model](../), or to
[the report's verdict](../../02-report/) where the comparison is held
against the mission's acceptance bar.
