# Representation swap: ten descriptors versus 2048 substructure bits

## Commands

```bash
cd missions/09-bio-pharma-modeling/06-model-or-representation/core
uv run --group chem python run_representation_grid.py

cd ../prod
uv run --group chem python rdkit_fingerprint.py --sample 60
```

Apple silicon laptop, macOS, CPU only. Run 2026-08-05. Grid wall-clock 83.3s
total for three endpoints (both representations, three seeds each, plus the
four-width sweep); RDKit agreement check 0.69s. \$0 marginal cost. Mission 08's
stage-06 seeds were running on the same machine during part of this run, which
affects the wall-clock figures above and nothing else — the AUCs are
deterministic given the seed.

The learner is stage 01's `fit_logistic_regression`, imported unmodified:
300 epochs, batch size 256, learning rate 0.1, zero weight initialization. The
seed varies only the minibatch shuffle order, which is the sole source of
randomness in a convex problem with deterministic initialization.

## Splits

Not rebuilt. Each endpoint's train/test CSVs are read from the stage that
introduced them, all written with a Murcko scaffold split at `train_frac 0.8`,
`split_seed 0`.

| Endpoint | Split written by | n train | n test | Train positive rate |
|---|---|---|---|---|
| SR-MMP | [00-dataset-and-property](../../00-dataset-and-property/) | 4,643 | 1,161 | 14.84% |
| NR-PPAR-gamma | [03-second-endpoint](../../03-second-endpoint/) | 5,154 | 1,289 | 2.29% |
| NR-ER | [04-third-endpoint](../../04-third-endpoint/) | 4,949 | 1,237 | 12.69% |

Both featurizers were asserted to have produced the same labels in the same
order and to have dropped the same molecules, so the two AUCs per endpoint are
computed over identical test sets.

## Featurization

| Endpoint | Descriptor wall-clock | Fingerprint wall-clock | Mean bits set / molecule | Columns ever set |
|---|---|---|---|---|
| SR-MMP | 1.7s | 1.7s | 28.52 | 2048 / 2048 |
| NR-PPAR-gamma | 1.6s | 1.8s | 28.23 | 2048 / 2048 |
| NR-ER | 1.6s | 1.8s | 28.49 | 2048 / 2048 |

Every one of the 2048 columns is set by at least one molecule in each corpus,
while any single molecule sets about 28 of them — a 1.4% dense matrix. The width
is being used; it is just used sparsely per row.

## Test ROC-AUC, per seed

| Endpoint | Representation | seed 0 | seed 1 | seed 2 | mean | spread |
|---|---|---|---|---|---|---|
| SR-MMP | descriptors | 0.8142 | 0.8146 | 0.8136 | 0.8142 | 0.0010 |
| SR-MMP | fingerprint | 0.6535 | 0.6539 | 0.6529 | 0.6534 | 0.0010 |
| NR-PPAR-gamma | descriptors | 0.6530 | 0.6575 | 0.6558 | 0.6554 | 0.0044 |
| NR-PPAR-gamma | fingerprint | 0.6566 | 0.6552 | 0.6575 | 0.6564 | 0.0023 |
| NR-ER | descriptors | 0.6411 | 0.6410 | 0.6420 | 0.6413 | 0.0011 |
| NR-ER | fingerprint | 0.6146 | 0.6141 | 0.6133 | 0.6140 | 0.0012 |

Seed changes only the minibatch order, and every spread above is at most
0.0044 — which is why a 0.1608 gap on SR-MMP is a result and a 0.0010 gap on
NR-PPAR-gamma is not.

Verdicts, using stage 05's rule that a gap smaller than the larger of the two
seed spreads is not a result:

| Endpoint | Gap (fingerprint − descriptor) | Verdict |
|---|---|---|
| SR-MMP | −0.1608 | descriptors win beyond spread |
| NR-PPAR-gamma | +0.0010 | inconclusive (gap inside spread) |
| NR-ER | −0.0273 | descriptors win beyond spread |

The descriptor means reproduce stages 01, 03, and 04 to four decimal places
(0.8142, 0.6554, 0.6413), which is the check that this harness measures the same
thing those stages did.

## Train versus test

| Endpoint | Descriptors train | test | gap | Fingerprint train | test | gap |
|---|---|---|---|---|---|---|
| SR-MMP | 0.8519 | 0.8142 | 0.0378 | 0.9995 | 0.6534 | 0.3460 |
| NR-PPAR-gamma | 0.7530 | 0.6554 | 0.0976 | 0.9998 | 0.6564 | 0.3434 |
| NR-ER | 0.6989 | 0.6413 | 0.0576 | 0.9952 | 0.6140 | 0.3812 |

The fingerprint arm memorizes: near-perfect training AUC on all three endpoints,
with a train−test gap 3.5 to 6.6 times the descriptor arm's.

## Bit-width sweep, SR-MMP, 3 seeds per width

| Bits | Columns ever set | Train AUC | Test AUC | Test spread | Train − test |
|---|---|---|---|---|---|
| 64 | 64 | 0.8032 | 0.6812 | 0.0037 | 0.1220 |
| 256 | 256 | 0.9045 | 0.7135 | 0.0013 | 0.1911 |
| 1024 | 1024 | 0.9934 | 0.6732 | 0.0009 | 0.3202 |
| 2048 | 2048 | 0.9995 | 0.6534 | 0.0010 | 0.3460 |

Every step in this column moves the test AUC by far more than the seed spread
at either end of it: 256 beats 2048 by 0.0601 against spreads of 0.0013 and
0.0010. Test AUC peaks at 256
bits and declines with further width while the train−test gap rises
monotonically — the signature of capacity, not of the algorithm. The peak,
0.7135, is still below the descriptor baseline's 0.8142 on the same split with
the same learner.

## RDKit agreement (`prod/`)

60 molecules from the SR-MMP test split, all 1,770 pairs:

| Quantity | Value |
|---|---|
| Molecules with identical bit sets | 0 / 60 |
| Mean bits set, `core/` | 47.35 |
| Mean bits set, RDKit | 42.97 |
| Tanimoto Spearman correlation | 0.9012 |
| Mean absolute Tanimoto difference | 0.0171 |
| Max absolute Tanimoto difference | 0.1226 |

Bit-level disagreement is expected and is not a defect: the two implementations
use different hash functions, so the same substructure lands on a different
index. The rank correlation is the comparison that means something, because
Tanimoto similarity is how a fingerprint is actually consumed.

## Raw records

[`representation-grid.json`](representation-grid.json) — per-seed train and test
AUCs for both representations on all three endpoints, fingerprint density
reports, the four-width sweep, and per-endpoint verdicts.
[`rdkit-agreement.json`](rdkit-agreement.json) — the `prod/` comparison above.
