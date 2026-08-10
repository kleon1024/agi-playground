# Mission 09 outcome report

Full mechanical output of `core/report.py`, reading stage 00 and stage 01's
own JSON artifacts directly.

## Command

```bash
cd 08-bio-pharma-modeling/02-report/core
uv run python report.py
```

Repository HEAD `9844b61`. CPU only, <1s, \$0 — this stage only reads JSON
files stage 00 and 01 already produced; it runs no model.

## Full output

```
Mission 09 outcome report
========================================================================

1. Acceptance: trained model beats descriptor baseline by more than run-to-run spread
------------------------------------------------------------------------
  descriptor baseline (RDKit + logistic regression): mean 0.8142  spread 0.0010  seeds [0.8142, 0.8146, 0.8136]
  trained model (SMILES char-transformer):           mean 0.7312  spread 0.0159  seeds [0.7217, 0.7377, 0.7341]
  gap (descriptor - model): +0.0830  (larger of the two spreads: 0.0159)
  -> trained model beats descriptor baseline: False
  -> the descriptor baseline wins, and by more than either spread: this is not a 'no result' near-tie, the trained model is clearly worse here.

2. Acceptance: scaffold overlap between train and test is measured and reported
------------------------------------------------------------------------
  overlap_scaffold_count: 0
  overlap_test_molecule_fraction: 0.0
  -> measured directly on the split output, not assumed: True

3. Acceptance: every stage has a runs/ entry before being marked verified
------------------------------------------------------------------------
  00-dataset-and-property: present
  01-descriptor-baseline-and-model: present
  02-report: present (this file)

4. Acceptance: the does_not_prove boundary appears in mission.yaml and the README
------------------------------------------------------------------------
  mission.yaml declares does_not_prove: True
  README restates the same boundary: True

========================================================================
VERDICT: NOT MET -- the trained model does NOT beat the descriptor baseline on SR-MMP.
The descriptor baseline (mean 0.8142) beats the trained model (mean 0.7312) by
0.0830 ROC-AUC, well outside either spread. The honest answer this mission's
own decision framing allows for is exactly this one: for SR-MMP, on this
scaffold split, with this ten-descriptor set and this from-scratch
architecture, the descriptor baseline is the better model to ship.
```

## What this verdict means, and does not mean

`mission.yaml`'s decision was never "does a trained model win" as an assumed
outcome — it was framed from the start as a real question with a real "no" as
a valid, complete answer, the same discipline
`01-language-model/02-pretrain/architecture-ablations` applies to its own ablation
rungs. The honest answer for SR-MMP, this scaffold split, this descriptor set,
and this architecture is: **ship the descriptor baseline.** A 696K-parameter
from-scratch character model trained on 4,643 examples with no pretraining
loses to ten fixed physicochemical numbers and a linear fit — plausible,
given the assay's known link to lipophilicity, and exactly the kind of result
`mission.yaml`'s own framing exists to let surface honestly rather than be
tuned away.

This is a complete, mission-acceptance-bar answer, not a stalled mission:
three of four `mission.yaml` acceptance items are satisfied outright
(scaffold overlap measured, every stage has a real `runs/` entry, the
`does_not_prove` boundary is stated in both places), and the fourth — "beats
the descriptor baseline" — is answered clearly in the negative rather than
left ambiguous.

## What this does not establish

This verdict is scoped exactly as tightly as stage 01's own result: one
endpoint (SR-MMP), one scaffold split, one ten-descriptor feature set, and one
from-scratch architecture and hyperparameter setting for the trained model. It
does not say a trained model can never beat a descriptor baseline on Tox21 —
a different endpoint, a larger or pretrained model, or a learned molecular
representation (graph neural network, pretrained chemical language model)
could plausibly close or reverse this gap, and none of that is tested here.
Nothing here is evidence about anti-aging biology, drug efficacy, or any real
screening outcome, per `mission.yaml`'s `does_not_prove`.
