# Descriptor baseline and trained model on NR-PPAR-gamma

Same protocol as [stage 01's SR-MMP run](../../01-descriptor-baseline-and-model/runs/2026-08-01-descriptor-and-model.md),
reusing stage 00 and stage 01's code unchanged via
[`core/run_second_endpoint.py`](../core/run_second_endpoint.py), applied to a
second, deliberately more imbalanced endpoint.

## Command

```bash
cd missions/09-bio-pharma-modeling/03-second-endpoint/core
uv run --group torch --group chem python run_second_endpoint.py
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | `rdkit` (`--group chem`), `torch` (`--group torch`) |
| Repository HEAD | `d087c50` |
| Compute | CPU only, $0 |
| Dataset SHA-256 | `7d7e7facd853a63e79ddce4e9c3fcb7a0d83a1c300b603031c0f2c64fbe77761` (same Tox21 file as stage 00) |

## The split: NR-PPAR-gamma

6,450 labeled compounds, 186 positive (2.88%) — the most imbalanced of
Tox21's 12 endpoints, versus SR-MMP's 15.8% over 5,810. 7 SMILES strings did
not parse under RDKit and were dropped by mol_id
(`TOX24724, TOX24723, TOX24552, TOX24622, TOX7518, TOX28892, TOX28623`; one
more than SR-MMP's 6, since this is a different subset of the same file).

Scaffold split (train-frac 0.8, split-seed 0), same construction as stage 00:

```
n_scaffold_groups:              1812
n_train / n_test:               5154 / 1289
n_train_scaffolds:               523
n_test_scaffolds:               1289
overlap_scaffold_count:            0
overlap_test_molecule_fraction:  0.0
empty_scaffold_group_size:       1640  (assigned to train)
train_positive_rate:            2.29%
test_positive_rate:             5.28%
```

Measured scaffold overlap is 0.0, same guarantee as stage 00. Class balance
shifts across the split even more sharply than SR-MMP's did (2.29% train vs
5.28% test, a >2x ratio) — a direct, expected consequence of the same
scaffold-grouping construction on a much rarer positive class: with only 148
positive compounds in the entire training set, whole-scaffold-group
assignment moves a larger fraction of the minority class's mass at once.

Full JSON: [`../data/split_summary.json`](../data/split_summary.json).

## Descriptor baseline: logistic regression over the same 10 RDKit descriptors

| seed | test ROC-AUC |
|---|---|
| 0 | 0.6530 |
| 1 | 0.6575 |
| 2 | 0.6558 |

**Mean 0.6554, spread (max-min) 0.0044.**

Raw: [`descriptor-seed0.json`](descriptor-seed0.json),
[`descriptor-seed1.json`](descriptor-seed1.json),
[`descriptor-seed2.json`](descriptor-seed2.json).

## Trained model: same character-level SMILES transformer, same hyperparameters

600 steps, batch size 64, AdamW lr 3e-4, `pos_weight`-adjusted BCE loss
(reweighted for this split's own 2.29% train positive rate — a far sharper
weight than SR-MMP's), same 4-layer/128-d architecture, unchanged.

| seed | test ROC-AUC |
|---|---|
| 0 | 0.6956 |
| 1 | 0.6337 |
| 2 | 0.6480 |

**Mean 0.6591, spread (max-min) 0.0619** — roughly 4x the trained model's own
spread on SR-MMP (0.0159), from the same architecture and step count. With
only ~148 positive training examples (2.29% of 5,154), each seed's minibatch
sampling draws a meaningfully different effective positive set over 600
steps, which is the direct, measurable cause of the wider spread: this is not
a new instability in the model, it is the same seed-only randomness (batch
order, `pos_weight`-scaled gradient noise) amplified by a much smaller
positive count.

Raw: [`model-seed0.json`](model-seed0.json), [`model-seed1.json`](model-seed1.json),
[`model-seed2.json`](model-seed2.json).

## The comparison, and the verdict

```
descriptor baseline:  0.6554  (spread 0.0044)
trained model:        0.6591  (spread 0.0619)
gap (model - descriptor): +0.0037
larger of the two spreads: 0.0619
```

**INCONCLUSIVE — a "no result," by the exact rule `mission.yaml` itself
declares:** "if the gap is smaller than the run-to-run spread, the honest
answer is 'no result.'" The trained model's mean is nominally higher by
0.0037, but that is roughly 1/17th of the trained model's own 0.0619 seed
spread — nowhere near large enough to call a win, exactly the same
statistical bar stage 02 applied to reach its own clear NOT MET on SR-MMP.

**This does not replicate stage 02's finding, and it does not reverse it —
it is a third, equally legitimate outcome the mission's decision framing was
built to allow.** On SR-MMP, the descriptor baseline won clearly and
repeatably (gap 5x the larger spread). On NR-PPAR-gamma, neither approach
wins by more than run-to-run noise. The most likely proximate cause is
directly measurable rather than mysterious: NR-PPAR-gamma's training split
has only 148 positive compounds, versus SR-MMP's 764 — roughly 5x fewer —
and the trained model's spread scales with that scarcity in a way the
convex, closed-form-gradient descriptor baseline's does not (0.0044 vs
0.0619, a >14x difference in spread between the two endpoints for the same
model, while the descriptor baseline's own spread barely moves, 0.0010 to
0.0044).

## What this run does not establish

Two endpoints out of Tox21's twelve have now been checked, not a systematic
sweep of all twelve, and no attempt was made to fix the trained model's high
variance here (more seeds, a smaller learning rate, or explicit class-balanced
batch sampling are all untried, different conditions). This says nothing
about whether the same inconclusive pattern would hold on a third endpoint of
similar or different imbalance, and nothing about anti-aging biology, drug
efficacy, or any real screening program, per `mission.yaml`'s `does_not_prove`.
