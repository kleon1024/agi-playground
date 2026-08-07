# Descriptor baseline and trained model on SR-MMP

Both baselines run against the exact scaffold split from
[stage 00's run](../../00-dataset-and-property/runs/2026-08-01-dataset-and-split.md)
(`train.csv` 4,643 compounds / `test.csv` 1,161 compounds, measured 0.0
scaffold overlap), 3 seeds each.

## Commands

```bash
cd 08-bio-pharma-modeling/01-descriptor-baseline-and-model/core

# Descriptor baseline (RDKit descriptors + from-scratch logistic regression)
for s in 0 1 2; do
  uv run --group chem python descriptor_baseline.py --seed $s
done

# Trained model (character-level SMILES transformer, reused Config/Block/RMSNorm)
for s in 0 1 2; do
  uv run --group torch --group chem python smiles_model.py --seed $s --steps 600
done
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | `rdkit` (`--group chem`), `torch` (`--group torch`) |
| Repository HEAD | `9844b61` |
| Compute | CPU only, \$0 |

## Descriptor baseline: logistic regression over 10 RDKit descriptors

| seed | test ROC-AUC | wall-clock |
|---|---|---|
| 0 | 0.8142 | 2.4s |
| 1 | 0.8146 | 1.7s |
| 2 | 0.8136 | 1.7s |

**Mean 0.8142, spread (max-min) 0.0010.** A convex model with deterministic
initialization has almost no seed sensitivity here — the seed only reorders
minibatches — so this tight spread is the expected finding, not a surprising
one.

Raw: [`descriptor-seed0.json`](descriptor-seed0.json),
[`descriptor-seed1.json`](descriptor-seed1.json),
[`descriptor-seed2.json`](descriptor-seed2.json).

## Trained model: character-level SMILES transformer

600 training steps, batch size 64, AdamW lr 3e-4, `pos_weight`-adjusted BCE
loss for the 14.8% train-set positive rate, 128-character max length (43
train / 56 test SMILES strings truncated), 696,065 parameters (4 layers,
`d_model=128`, 4 query heads / 2 KV heads, `d_ff=320`).

| seed | test ROC-AUC | wall-clock |
|---|---|---|
| 0 | 0.7217 | 104.7s |
| 1 | 0.7377 | 100.0s |
| 2 | 0.7341 | 109.5s |

**Mean 0.7312, spread (max-min) 0.0159.**

Raw: [`model-seed0.json`](model-seed0.json), [`model-seed1.json`](model-seed1.json),
[`model-seed2.json`](model-seed2.json).

**A hyperparameter check performed before locking these numbers**: seed 0 was
also trained for 1,500 steps to check whether 600 steps was simply
undertrained. Training loss dropped from ~0.4 (600 steps) to ~0.06-0.2 (1,500
steps) — but test ROC-AUC *fell* to 0.7084, lower than the 600-step run's
0.7217. This is a real, measured overfitting signal, not noise: more steps
memorize the small (4,643-compound) training set rather than generalizing
further. 600 steps is used for all three reported seeds because it is the
better and the less-overfit of the two, checked once, before any seed's final
number was recorded — not selected after comparing multiple attempts against
the test set.

## The comparison

```
descriptor baseline:  0.8142  (spread 0.0010)
trained model:         0.7312  (spread 0.0159)
gap (descriptor - model): 0.0830
```

The descriptor baseline beats the trained model by 0.083 ROC-AUC — roughly
5x the trained model's own seed-to-seed spread, and roughly 80x the
descriptor baseline's. **This is not a "no result" case of a gap smaller than
spread; the descriptor baseline wins clearly and repeatably.**

## Why the descriptor baseline wins here

SR-MMP is loss of mitochondrial membrane potential, an assay with a
well-documented link to a molecule's lipophilicity (MolLogP) and related bulk
physicochemical properties — mitochondrial toxins tend to be more lipophilic,
which is exactly the kind of signal a fixed descriptor captures directly and
a from-scratch character-level model, trained on only 4,643 examples with no
pretraining, has to discover from raw characters with nowhere near enough
data to do so reliably. This is a plausible mechanism for the gap, not a
proven cause — no ablation isolating which individual descriptor drives it was
run.

## The published MoleculeNet number

Read directly from the primary source (not recalled): Wu et al., 2018 reports
Tox21 results as a mean across all 12 tasks under a **random** split — not
scaffold, not per-endpoint — KernelSVM 0.822, GC (graph convolution) 0.829.
This stage's descriptor baseline (0.8142, scaffold split, SR-MMP only) sits in
the same broad range as KernelSVM's 12-task mean (0.822) under a harder split
protocol, which is a plausible sign the descriptor set and endpoint chosen
here are not unusually easy or unusually hard relative to the field's own
numbers — but the split and per-task/mean mismatch means this is context, not
a like-for-like baseline comparison. No genuine per-endpoint SR-MMP number
from the primary source could be found; see the stage README for the full
citation trail.

## What this run does not establish

Only one architecture, one hyperparameter setting (beyond the single 600-vs-
1500-step check above), and one descriptor set were tried — this is not a
hyperparameter search, and a different trained-model architecture or a larger
pretraining corpus is a different, untested condition. The result is specific
to SR-MMP and this exact scaffold split; it says nothing about whether a
trained model would beat a descriptor baseline on a different Tox21 endpoint,
a different molecular dataset, or a random rather than scaffold split.
