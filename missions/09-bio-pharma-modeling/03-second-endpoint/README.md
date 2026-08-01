---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Second endpoint
---

# Does the SR-MMP finding generalize to a different endpoint?

**Question:** stage 02 closed with a clear, repeatable finding for one
endpoint — SR-MMP, 15.8% positive over 5,810 labeled compounds — where the
descriptor baseline beat the trained model by far more than either's seed
spread. `mission.yaml`'s own `does_not_prove` already warns that this result
"does not generalize to a different endpoint... without re-running the
comparison from scratch." This stage does exactly that: same split
discipline, same baseline, same architecture, a different Tox21 endpoint.

**The artifact this stage produces** is the same pair of numbers stage 01
produced — descriptor-baseline and trained-model mean ROC-AUC, each across 3
seeds — measured on a second, materially different endpoint, plus an
explicit replicates / reverses / inconclusive verdict against stage 02's
finding.

**Before this:** [stage 00](../00-dataset-and-property/) (the split code this
stage reuses) and [stage 02](../02-report/) (the SR-MMP finding this stage
tests for generality).

## Picking a genuinely different endpoint

Stage 00's own per-endpoint balance table (in its
[dataset run](../00-dataset-and-property/runs/2026-08-01-dataset-and-split.md))
already computed all 12 endpoints' label counts and rates. Repeating the
comparison on SR-ARE (16.2%, closest neighbor to SR-MMP's 15.8%) would be
close to a duplicate run. **NR-PPAR-gamma** is picked instead: 2.9% positive
over 6,450 labeled compounds — the most imbalanced endpoint in the panel, and
roughly 5x more imbalanced than SR-MMP with a meaningfully different labeled
count. A finding that holds under this much more severe imbalance is a
stronger generality claim than one that only holds on a second
similarly-balanced endpoint; a finding that breaks under it is an equally
real result.

## What was reused, not reimplemented

[`core/run_second_endpoint.py`](core/run_second_endpoint.py) imports directly
from stage 00 and stage 01's own modules — `download`, `label_stats`,
`load_endpoint`, `murcko_scaffolds`, `scaffold_split`, `write_split` from
[`00-dataset-and-property/core/prepare_dataset.py`](../00-dataset-and-property/core/prepare_dataset.py),
and `run` (the descriptor baseline) from
[`01-descriptor-baseline-and-model/core/descriptor_baseline.py`](../01-descriptor-baseline-and-model/core/descriptor_baseline.py)
and `train_and_eval` (the trained model) from
[`01-descriptor-baseline-and-model/core/smiles_model.py`](../01-descriptor-baseline-and-model/core/smiles_model.py) —
unchanged, parameterized only by endpoint name and output directory. No
descriptor set, split logic, model architecture, or hyperparameter differs
from stage 01; the only independent variable is the endpoint.

## Result

**INCONCLUSIVE — a "no result," by `mission.yaml`'s own rule.** Descriptor
baseline mean ROC-AUC 0.6554 (spread 0.0044); trained model mean 0.6591
(spread 0.0619). The trained model's mean is nominally 0.0037 higher, but
that gap is roughly 1/17th of the trained model's own seed-to-seed spread —
nowhere near the bar stage 02 used to call SR-MMP a clear, repeatable
descriptor-baseline win. This neither replicates nor reverses stage 02's
finding; it is the third legitimate outcome the mission's own decision
framing exists to allow. The most likely proximate cause is directly
measurable: NR-PPAR-gamma's training split has only 118 positive compounds
(2.29%) versus SR-MMP's 689 (14.8%), and the trained model's spread grows
roughly 4x between the two endpoints while the descriptor baseline's spread
barely moves — small-model training variance scales with positive-class
scarcity in a way a convex descriptor fit does not.

Full per-seed numbers, environment, and the exact command:
[`runs/2026-08-01-second-endpoint.md`](runs/2026-08-01-second-endpoint.md).

## What this stage does not establish

This is a second data point, not a survey: two of Tox21's 12 endpoints have
now been checked, not twelve. It says nothing about the other 10 endpoints,
nothing about a different molecular dataset, and nothing about whether the
same descriptor set or architecture would win or lose on an endpoint with a
different imbalance profile again. Restated from `mission.yaml`: nothing here
is evidence about anti-aging biology, drug efficacy, or any real screening
program.

**Next:** none planned; this stage closes the generality question stage 02's
own `does_not_prove` opened.
