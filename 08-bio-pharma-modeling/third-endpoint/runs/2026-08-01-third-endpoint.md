# Descriptor baseline and trained model on NR-ER

Same protocol as [stage 01's SR-MMP run](../../01-descriptor-baseline-and-model/runs/2026-08-01-descriptor-and-model.md)
and [stage 03's NR-PPAR-gamma run](../../03-second-endpoint/runs/2026-08-01-second-endpoint.md),
reusing stage 00 and stage 01's code unchanged via
[`core/run_third_endpoint.py`](../core/run_third_endpoint.py), applied to a
third endpoint chosen to fill the middle of the imbalance range already
tested, not to push further outside it (see "Why NR-ER" below).

## Command

```bash
cd 08-bio-pharma-modeling/04-third-endpoint/core
uv run --group torch --group chem python run_third_endpoint.py
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | `rdkit` (`--group chem`), `torch` (`--group torch`) |
| Repository HEAD | `1bdec84` |
| Compute | CPU only, \$0 |
| Dataset SHA-256 | `7d7e7facd853a63e79ddce4e9c3fcb7a0d83a1c300b603031c0f2c64fbe77761` (same Tox21 file as stages 00/03) |
| Wall-clock | data prep 3.4s; descriptor baseline 1.7s/1.7s/1.7s (3 seeds); trained model 130.0s/135.3s/132.6s (3 seeds) |

## Why NR-ER, and a correction to stage 03's own numbers found while picking it

Stage 00's 12-endpoint balance table lists NR-PPAR-gamma (2.9%) as the single
most imbalanced endpoint in the whole panel and SR-MMP (15.8%) tied for the
most balanced with SR-ARE (16.2%, already rejected by stage 03 as a
near-duplicate of SR-MMP). No endpoint in this dataset is more extreme in
either direction than what stages 01 and 03 already tested — so a genuine
third data point has to come from the middle of the range, not further
outside it. **NR-ER** is picked: 793 total positive over 6,193 labeled
compounds (12.8%), second most balanced endpoint after SR-ARE/SR-MMP, and a
clean way to test whether the stage-03 variance hypothesis holds as a
monotonic trend across three points rather than being an artifact of only
two.

While reproducing stage 03's own cited counts to compare against, this run's
own `train.csv` and `split_summary.json` were checked directly against
stage 01's and stage 03's train.csv files (`sum(label==1)` over each), rather
than trusting the prose. That check found stage 03's README and runs entry
had reported the wrong **counts** for both endpoints, while their percentages
were correct: NR-PPAR-gamma's actual training-split positive count is **118**
(not 148 — 118/5154 = 2.29%, the percentage was right), and SR-MMP's is
**689** (not 764 — 689/4643 = 14.8%, also right). Both files have been
corrected in this commit to the counts verified directly from their own
`train.csv`; the ROC-AUC numbers and every other reported figure in stage 03
were unaffected and are unchanged.

## The split: NR-ER

6,193 labeled compounds, 793 positive (12.80%). 7 SMILES strings did not
parse under RDKit and were dropped by mol_id: `TOX24724, TOX24723, TOX24552,
TOX24622, TOX7518, TOX28892, TOX28623`. Scaffold split (train-frac 0.8,
split-seed 0): 4,949 train / 1,237 test, 1,769 scaffold groups, 0 scaffold
overlap between train and test (measured directly, same guarantee as stages
00/01/03). Train positive rate 12.69% (**628** positive compounds), test
positive rate 13.18% — a much smaller train/test balance shift than either
prior endpoint, consistent with NR-ER's larger, more even scaffold-group
sizes.

Full JSON: [`../data/split_summary.json`](../data/split_summary.json).

## Descriptor baseline: logistic regression over the same 10 RDKit descriptors

| seed | test ROC-AUC |
|---|---|
| 0 | 0.6411 |
| 1 | 0.6410 |
| 2 | 0.6420 |

**Mean 0.6413, spread (max-min) 0.0011.**

Raw: [`descriptor-seed0.json`](descriptor-seed0.json),
[`descriptor-seed1.json`](descriptor-seed1.json),
[`descriptor-seed2.json`](descriptor-seed2.json).

## Trained model: same character-level SMILES transformer, same hyperparameters

600 steps, batch size 64, AdamW lr 3e-4, `pos_weight`-adjusted BCE loss
(reweighted for this split's own 12.69% train positive rate), same 4-layer/
128-d architecture, unchanged.

| seed | test ROC-AUC |
|---|---|
| 0 | 0.6804 |
| 1 | 0.6577 |
| 2 | 0.6656 |

**Mean 0.6679, spread (max-min) 0.0227.**

Raw: [`model-seed0.json`](model-seed0.json), [`model-seed1.json`](model-seed1.json),
[`model-seed2.json`](model-seed2.json).

## Result: a third, distinct outcome, and what it does to the stage-03 hypothesis

**The trained model is numerically ahead of the descriptor baseline here**
(0.6679 vs 0.6413, gap 0.0266) **by a margin that is thin but real** — 1.17x
the trained model's own seed spread (0.0227), just clearing the same bar
stage 01/02 used to call a result "not detectable" when the gap sat inside
the spread. This is a third qualitative outcome, distinct from both priors:
SR-MMP was a clear, repeatable descriptor win (gap 5x the larger spread);
NR-PPAR-gamma was inconclusive (gap 1/17th of the model's own spread); NR-ER
is a marginal model win, right at the edge of detectability rather than deep
inside or clearly outside the noise band.

**The scarcity-drives-variance hypothesis holds directionally across all
three now-corrected data points, but only loosely:**

| Endpoint | train positives | model spread | descriptor spread |
|---|---|---|---|
| NR-PPAR-gamma | 118 | 0.0620 | 0.0044 |
| NR-ER | 628 | 0.0227 | 0.0011 |
| SR-MMP | 689 | 0.0159 | 0.0010 |

Model spread falls monotonically as positive count rises (0.0620 to 0.0227
to 0.0159), and the descriptor baseline's spread stays an order of magnitude
tighter throughout regardless of positive count (0.0044 to 0.0011 to 0.0010)
— both consistent with stage 03's hypothesis. But the relationship is not
smooth: NR-ER and SR-MMP have nearly the same positive count (628 vs 689, ~10%
apart) yet the model's spread differs by ~43% between them (0.0227 vs
0.0159). With only 3 training seeds per endpoint, "spread" here is itself a
noisy estimate of variance, not variance directly — this repository's own
rule against reading noise as signal applies to the hypothesis-test dimension
just as much as to the win/lose dimension. **Honest verdict: the direction of
the scarcity-variance relationship holds across all three tested points; its
exact shape does not, and cannot, be pinned down from three points at three
seeds each.**

## What this stage does not establish

This is a third data point, not a survey: three of Tox21's 12 endpoints have
now been checked. It says nothing about the other nine, nothing about a
different molecular dataset, and the marginal model win here is specific to
NR-ER, this exact scaffold split, and this one architecture/hyperparameter
choice — it does not transfer to a different endpoint or representation
without repeating the comparison from scratch. Restated from `mission.yaml`:
nothing here is evidence about anti-aging biology, drug efficacy, or any real
screening program.

**Next:** none planned; a fourth endpoint would need to sit outside the
range already covered by these three, and none of Tox21's remaining nine
endpoints does (all fall between NR-AR-LBD's 3.5% and NR-AhR's 11.7%,
already bracketed by NR-PPAR-gamma and NR-ER/SR-MMP).
