---
status: verified
level: applied
base: none
verified: 2026-08-01
label: Report
---

# Does a small trained model beat the descriptor baseline — verdict

**Question:** stages 00 and 01 produced every number `mission.yaml`'s
acceptance bar names. This stage holds them against that bar mechanically —
reading the real `runs/` JSON directly, not re-typing numbers by hand — and
states MET or NOT MET for each item.

**The artifact this stage produces** is one printed verdict,
[`runs/2026-08-01-outcome-report.md`](runs/2026-08-01-outcome-report.md),
generated entirely by [`core/report.py`](core/report.py) reading stage 00 and
01's own output files.

**Before this:** [stage 01](../01-descriptor-baseline-and-model/), whose
descriptor-baseline and trained-model results this stage checks against
[stage 00](../00-dataset-and-property/)'s measured scaffold-overlap number.

## The verdict

**NOT MET.** The descriptor baseline (mean ROC-AUC 0.8142 across 3 seeds)
beats the trained model (mean 0.7312) by 0.0830 — roughly 5x the trained
model's own 0.0159 seed spread and roughly 80x the descriptor baseline's
0.0010 spread. This is not a case where the gap is smaller than the
run-to-run spread, which `mission.yaml` names as its own "no result"
condition — the descriptor baseline wins clearly and repeatably. The honest
answer this mission's own decision framing exists to allow is exactly this
one: for SR-MMP, on this scaffold split, with this descriptor set and this
from-scratch architecture, **the descriptor baseline is the better model to
ship.**

The other three acceptance items are satisfied outright:

- Scaffold overlap between train and test is measured (0.0), not assumed.
- Every stage — 00, 01, and this one — has a real `runs/` entry.
- The `does_not_prove` boundary is stated in both `mission.yaml` and the
  mission README.

Full mechanical output: [`runs/2026-08-01-outcome-report.md`](runs/2026-08-01-outcome-report.md).

## Why this counts as the mission succeeding, not stalling

`mission.yaml` declared, before any code existed, that "if the gap is smaller
than the run-to-run spread, the honest answer is 'no result.'" This run's gap
is not smaller than the spread — it is the opposite finding, a clear and
repeatable loss for the trained model — and reporting that plainly is what
this mission was built to do. A curriculum that only ever showed the trained
model winning would be evidence of tuning toward a preferred answer, not of
anything about SR-MMP.

## What this stage does not establish

This verdict is scoped to exactly the conditions stage 00 and 01 ran under:
one endpoint, one scaffold split, one descriptor set, one from-scratch
architecture. It says nothing about whether a different model — a graph
neural network, a pretrained chemical language model, more training data —
would close or reverse this gap on the same endpoint, and nothing about any
other Tox21 endpoint. Nothing here is evidence about anti-aging biology, drug
efficacy, or the outcome of any real screening program, per `mission.yaml`'s
`does_not_prove`, restated in the [mission README](../README.md).
