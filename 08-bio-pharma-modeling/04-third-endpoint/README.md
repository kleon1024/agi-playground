---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Third endpoint
---

# Does the scarcity-drives-variance hypothesis hold at a third endpoint?

**Question:** stage 03 floated a hypothesis after finding NR-PPAR-gamma's
result inconclusive where SR-MMP's was a clear descriptor win — that the
trained model's seed-to-seed variance scales with how scarce the positive
class is, while the convex descriptor baseline's variance does not. A
hypothesis proposed from two data points is not yet a finding; this stage
adds a third.

**The artifact this stage produces** is the same pair of numbers stages 01
and 03 produced — descriptor-baseline and trained-model mean ROC-AUC, each
across 3 seeds — on a third Tox21 endpoint, plus an explicit verdict on
whether the scarcity-variance relationship holds across all three.

**Before this:** [stage 00](../00-dataset-and-property/) (the split code this
stage reuses), [stage 01](../01-descriptor-baseline-and-model/) (the SR-MMP
result), and [stage 03](../03-second-endpoint/) (the NR-PPAR-gamma result and
the hypothesis this stage tests).

## Picking a third endpoint that fills the range, not extends it

Stage 00's own per-endpoint balance table already fixed the extremes:
NR-PPAR-gamma (2.9% positive) is the single most imbalanced endpoint in the
whole 12-endpoint panel, and SR-MMP (15.8%) is tied for the most balanced
with SR-ARE (16.2%, already rejected by stage 03 as a near-duplicate). No
endpoint in this dataset sits further outside that range in either
direction. The genuinely new information available is therefore whether the
relationship holds *in between* the two already-tested points, not further
outside them. **NR-ER** is picked: 12.8% positive over 6,193 labeled
compounds — roughly midway on the imbalance spectrum between NR-PPAR-gamma
and SR-MMP.

## What was reused, not reimplemented

[`core/run_third_endpoint.py`](core/run_third_endpoint.py) imports the exact
same functions stage 03 used from stage 00 and stage 01 — `download`,
`label_stats`, `load_endpoint`, `murcko_scaffolds`, `scaffold_split`,
`write_split`, `run` (descriptor baseline), `train_and_eval` (trained
model) — unchanged, parameterized only by endpoint name and output
directory. No descriptor set, split logic, model architecture, or
hyperparameter differs from stages 01/03; the only independent variable is
the endpoint.

## A correction found along the way

Cross-checking stage 03's cited positive-count numbers directly against its
own `train.csv` (rather than trusting the prose) turned up an arithmetic
error: stage 03's README and runs entry reported NR-PPAR-gamma's training
positive count as 148 and SR-MMP's as 764. Both percentages were correct
(2.29% and 14.8%), but the underlying counts were not — the real counts,
verified by direct count over each `train.csv`, are **118** and **689**.
Both files are corrected in this commit; no ROC-AUC number or verdict in
stage 03 changes, only the two positive-count figures.

## Result

**A third, distinct outcome: the trained model is marginally ahead of the
descriptor baseline** — 0.6679 vs 0.6413, a gap of 0.0266 that is 1.17x the
trained model's own seed spread (0.0227), just clearing the bar this
mission's other stages use to call a result real rather than noise. This
differs from both priors: SR-MMP was a clear, repeatable descriptor win;
NR-PPAR-gamma was inconclusive; NR-ER is a thin but real model win.

**On the scarcity-variance hypothesis itself:** it holds directionally
across all three corrected data points — model spread falls monotonically as
train positive count rises (118 → 0.0620, 628 → 0.0227, 689 → 0.0159) while
the descriptor baseline's spread stays an order of magnitude tighter
throughout — but the relationship is not smooth (NR-ER and SR-MMP have
almost the same positive count yet a 43% spread difference), and 3 seeds per
endpoint cannot resolve its exact shape. Full numbers, the correction detail,
and the honest verdict on both questions:
[`runs/2026-08-01-third-endpoint.md`](runs/2026-08-01-third-endpoint.md).

## The fix and its trade

The fix is the mid-range endpoint selection plus the correction discipline
that surfaced a real error on the way. NR-ER (12.8% positive) is picked
because it fills the imbalance range *between* the two tested extremes
rather than extending it — a fourth endpoint outside the bracket would add
no new information, while an interpolated point can falsify or confirm the
scarcity-variance relationship's shape. The trade is that mid-range points
land in the murkiest region: the result is a third, distinct outcome (model
0.6679 vs descriptor 0.6413, a 0.0266 gap at 1.17x the model's 0.0227
spread) that just clears the real-result bar, and the hypothesis holds
directionally but not smoothly — the 43% spread difference between NR-ER and
SR-MMP at nearly equal positive counts is exactly the kind of imperfection
three seeds cannot resolve. The correction (stage 03's positive counts 148
and 764 → verified 118 and 689) is part of the fix: numbers are checked
against the actual `train.csv`, and both files were corrected without
changing any verdict.

## Who owns this loop

- **The dataset owner** owns the endpoint-selection rationale and the
  correction protocol: selection comes from stage 00's measured balance
  table before results exist, and any cited count is verified by direct
  count over the data file rather than trusted from prose.
- **The evaluation owner** owns the thin-but-real verdict and its bar:
  the 1.17x-spread gap clears the mission's result rule, and the
  not-smooth relationship is reported as directionally-consistent but
  unresolved, not as a clean correlation.
- **The model team** owns the monotone spread-vs-scarcity read as the
  stage's real finding: 118 → 0.0620, 628 → 0.0227, 689 → 0.0159 is the
  evidence that scarcity inflates variance, with the caveat that 3 seeds
  cannot resolve its exact shape.

## What this stage does not establish

This is a third data point, not a survey: three of Tox21's 12 endpoints have
now been checked, not twelve, and this mission does not have a fourth
endpoint planned — every remaining endpoint's imbalance falls inside the
range these three already bracket. It says nothing about a different
molecular dataset or representation. Restated from `mission.yaml`: nothing
here is evidence about anti-aging biology, drug efficacy, or any real
screening program.

**Next:** none planned; this stage closes the generality question stage 03's
own hypothesis opened, with an honest "holds directionally, not precisely"
verdict rather than a forced confirm or deny.

A detour from here: [the third point that fills the
range](when-the-mid-range-point-lands/) — the recorded NR-ER seeds read:
the model wins beyond its own spread (+0.0265 vs 0.0227), so the
three-point pattern is variance up as positives shrink, with the winner
decided by enough data.

Another detour: [the mid-range endpoint gives the model its first clean win](the-model-first-win/) — the recorded seeds read: margin +0.0265 vs spread 0.0227, the third point that separates who wins from where a winner can be seen.
