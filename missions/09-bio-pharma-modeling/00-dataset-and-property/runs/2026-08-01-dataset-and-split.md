# Downloading Tox21 and building the scaffold split

First real run of `core/prepare_dataset.py` against the live Tox21 CSV named
in `mission.yaml`. This is the run that fixes the endpoint, the split, and the
scaffold-overlap number before any model touches the data.

## Command

```bash
cd missions/09-bio-pharma-modeling/00-dataset-and-property/core
uv run --group chem python prepare_dataset.py \
    --endpoint SR-MMP --train-frac 0.8 --split-seed 0 \
    --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz \
    --out ../data
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed, via `--group chem`) |
| Dependencies | `rdkit` 2023.9+ (new opt-in `chem` group in `pyproject.toml`) |
| Repository HEAD | `9844b61` |
| Wall-clock | 28.3s (network download + RDKit parse + split), \$0, CPU only |

## Why SR-MMP

Before writing any split or model code, every one of the 12 Tox21 endpoints'
label balance was computed directly from the downloaded CSV (not estimated):

| endpoint | labeled | positive | positive rate |
|---|---|---|---|
| NR-AR | 7265 | 309 | 4.3% |
| NR-AR-LBD | 6758 | 237 | 3.5% |
| NR-AhR | 6549 | 768 | 11.7% |
| NR-Aromatase | 5821 | 300 | 5.2% |
| NR-ER | 6193 | 793 | 12.8% |
| NR-ER-LBD | 6955 | 350 | 5.0% |
| NR-PPAR-gamma | 6450 | 186 | 2.9% |
| SR-ARE | 5832 | 942 | 16.2% |
| SR-ATAD5 | 7072 | 264 | 3.7% |
| SR-HSE | 6467 | 372 | 5.8% |
| **SR-MMP** | **5810** | **918** | **15.8%** |
| SR-p53 | 6774 | 423 | 6.2% |

SR-ARE (16.2%) and SR-MMP (15.8%) are the two best-balanced endpoints by a
wide margin over the rest, which mostly sit under 8%. Between the two, SR-MMP
is picked here because the assay it measures has a single, statable
mechanism — loss of mitochondrial membrane potential, a standard early
readout of cellular stress/toxicity — which makes "what does this label
actually measure" answerable in one sentence, unlike SR-ARE's antioxidant-
response-element reporter, which responds to a broader and less specific set
of stressors. This choice is made once, here, before stage 01 sees any model
result, per `mission.yaml`'s own guardrail against choosing after seeing which
endpoint flatters a number.

## The scaffold split, and what "checked, not assumed" means concretely

6 of the 5,810 labeled SMILES strings did not parse under RDKit
(`Chem.MolFromSmiles` returned `None`) and were dropped, reported here rather
than silently excluded: `TOX24723, TOX24552, TOX24622, TOX7518, TOX28892,
TOX28623`.

The remaining 5,804 compounds group into **1,668 distinct Murcko scaffolds**.
Scaffold groups are sorted by size (largest first, ties broken by a
seed-0 shuffle) and assigned whole to train until the 80% target is reached,
then the rest to test — the standard construction that makes scaffold overlap
zero *by design*. The guardrail asks for this to be measured anyway rather
than assumed, so the split output was checked directly for any scaffold
string appearing in both `train_scaffolds` and `test_scaffolds`:

```
n_scaffold_groups:              1668
n_train / n_test:                4643 / 1161
n_train_scaffolds:                507
n_test_scaffolds:                1161   (mostly singleton scaffolds)
overlap_scaffold_count:             0
overlap_test_molecule_fraction:   0.0
```

The measured overlap is 0.0 — the construction held, and this run confirms
that by direct check rather than by trusting the algorithm.

**One real wrinkle worth recording**: a molecule with no ring system at all
(a plain acyclic chain) has an *empty* Murcko scaffold (`""`). All 1,467 such
molecules collide into one artificial "scaffold" group under this
definition — the single largest group by a wide margin — and by the
size-first assignment rule, that entire group lands on one side of the split
(train, this run). This is a real property of Murcko scaffolds on this
dataset, not a bug: acyclic compounds are simply structurally closer to each
other than to any ringed compound, so grouping them together is the correct
behavior of the split, but it does mean every acyclic compound in this run's
test set is absent — test performance here says nothing about acyclic
molecules specifically. Recorded as a scope limit, not smoothed over.

**Class balance also shifted between train and test**, a direct consequence
of splitting by scaffold group rather than by molecule: train positive rate is
14.8%, test is 19.7%. This is expected — grouping compounds by scaffold means
whole clusters of same-labeled compounds move together — and is reported
rather than treated as if the split were i.i.d.

## Full run output

```json
{
  "endpoint": "SR-MMP",
  "dataset_sha256": "7d7e7facd853a63e79ddce4e9c3fcb7a0d83a1c300b603031c0f2c64fbe77761",
  "n_total_rows_in_file": 7831,
  "n_labeled_for_endpoint": 5810,
  "n_dropped_unparseable_smiles": 6,
  "train_frac_target": 0.8,
  "split_seed": 0,
  "n_train": 4643,
  "n_test": 1161,
  "train_positive_rate": 0.1484,
  "test_positive_rate": 0.1972,
  "scaffold_split_stats": {
    "n_scaffold_groups": 1668,
    "n_train_scaffolds": 507,
    "n_test_scaffolds": 1161,
    "overlap_scaffold_count": 0,
    "overlap_test_molecule_fraction": 0.0,
    "empty_scaffold_group_size": 1467,
    "empty_scaffold_assigned_to": "train"
  },
  "wall_clock_seconds": 28.26
}
```

Full JSON: [`../data/split_summary.json`](../data/split_summary.json), committed
alongside `train.csv`/`test.csv`; only `data/raw/` (the downloaded Tox21 CSV)
is git-ignored and re-fetched by the command above.

## What this run does not establish

No model has touched this data yet — this stage only fixes the endpoint, the
split, and the measured scaffold-overlap number. Nothing here says whether a
descriptor baseline or a trained model can predict SR-MMP; that is stage 01.
The endpoint choice is specific to SR-MMP's own balance and mechanism; it is
not a claim that SR-MMP is the "best" or most important Tox21 endpoint by any
other criterion.
