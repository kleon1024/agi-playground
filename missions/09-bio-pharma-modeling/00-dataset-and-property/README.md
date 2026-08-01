---
status: verified
level: applied
base: none
verified: 2026-08-01
label: Dataset and property
---

# Which endpoint, and does a scaffold split actually hold one out?

**Question:** Tox21 carries 12 different toxicity labels on the same ~8,000
compounds. Before any model gets built, two things have to be fixed and
justified: which one label this mission answers for, and whether the
train/test split that will judge it actually holds out structurally distinct
molecules — or only looks like it does.

**The artifact this stage produces** is two CSVs, `train.csv` and `test.csv`,
each row a `(mol_id, smiles, label, scaffold)` tuple for one chosen endpoint,
plus a measured number: the fraction of test molecules that share a Murcko
scaffold with any training molecule.

**Before this:** [`mission.yaml`](../mission.yaml) and the [mission
README](../README.md), which declare the endpoint-selection and split
requirements this stage satisfies.

## Picking one endpoint, before seeing any result

Tox21's 12 endpoints range from 2.9% to 16.2% positive. A wildly imbalanced
label (say, NR-PPAR-gamma at 2.9%) makes ROC-AUC noisy and a
"beat the baseline" claim easy to get by accident on a small held-out set.
[`core/prepare_dataset.py`](core/prepare_dataset.py) computes the real
per-endpoint balance from the downloaded file first — see the full table in
[`runs/2026-08-01-dataset-and-split.md`](runs/2026-08-01-dataset-and-split.md)
— and **SR-MMP** (15.8% positive, 5,810 labeled compounds) is picked: it is
one of the two best-balanced endpoints, and it measures a single, nameable
mechanism — loss of mitochondrial membrane potential, a standard cellular
stress readout — rather than a broader multi-pathway reporter. This choice is
made here, in this stage, before stage 01 trains anything against it.

## Why a random split would lie about generalization

Molecular datasets cluster around a small number of core ring structures with
different substituents attached. Shuffle-and-split at random, and near-
identical molecules routinely land on both sides — the model doesn't need to
generalize to score well, it needs to recognize a scaffold it has already seen
with a different side chain. A **scaffold split** groups molecules by their
Murcko scaffold (ring system, substituents stripped) first, then assigns whole
groups to train or test, so a held-out result is actually a test of
generalization to unseen structures.

**A brief history.** The descriptors this mission's baseline fits — LogP,
polar surface area, ring counts — descend from Hansch and Fujita's 1964
quantitative structure-activity relationship work (*J. Am. Chem. Soc.* 86(8):
1616-1626), the first framework to correlate a fixed set of computed
physicochemical properties with biological activity rather than fitting
structure directly. The "Murcko scaffold" grouping used for this stage's split
comes from a specific, later paper: Bemis and Murcko, "The Properties of Known
Drugs. 1. Molecular Frameworks" (*J. Med. Chem.* 39(15): 2887-2893, 1996),
which defined the ring-system-with-substituents-stripped decomposition this
mission uses directly. Tox21 itself is a US federal interagency screening
program (NIH/EPA/FDA, launched 2008) that tests thousands of compounds against
a panel of toxicity-pathway assays; MoleculeNet (Wu et al., 2018, cited in
stage 01) later packaged a slice of that data as a standard ML benchmark,
which is the exact CSV this stage downloads.

## Building and checking the split

`core/prepare_dataset.py`:

1. Downloads the exact Tox21 CSV named in `mission.yaml` (SHA-256 recorded in
   `runs/`, so a future re-run can confirm it fetched the same file).
2. Filters to the 5,810 compounds labeled for SR-MMP; 6 SMILES strings do not
   parse under RDKit and are dropped, by mol_id, not silently.
3. Computes each remaining compound's Murcko scaffold, groups by it, sorts
   groups largest-first (seed-broken ties), and assigns whole groups to train
   until an 80% target is hit, the rest to test.
4. **Measures** train/test scaffold overlap directly on the output, rather
   than trusting that step 3's construction produced it.

The guardrail in `mission.yaml` asks for this overlap to be "checked and
reported... a nonzero overlap is reported, not silently dropped from the
number." Here it measures **0.0** — the construction held — but the number
comes from checking the actual split, not from assuming a scaffold split is
clean by definition.

## What the check surfaced

Two things a shuffle-and-split would never reveal:

- **Acyclic molecules share one artificial scaffold.** A molecule with no
  rings has an *empty* Murcko scaffold, so all 1,467 acyclic compounds in this
  dataset collide into a single group — the largest one — and land entirely
  on one side of the split (train, this run). Test-set performance below says
  nothing about ring-free molecules specifically; that is a real scope limit
  of this split, not an oversight.
- **Class balance shifts across the split.** Train positive rate is 14.8%,
  test is 19.7%. Grouping by scaffold means whole clusters of same-labeled
  compounds move together, so the split is not the same distribution on both
  sides by construction — expected, and reported rather than treated as if
  the split were drawn i.i.d.

Full numbers, the per-endpoint balance table, and the exact command:
[`runs/2026-08-01-dataset-and-split.md`](runs/2026-08-01-dataset-and-split.md).

## Run it

```bash
cd missions/09-bio-pharma-modeling/00-dataset-and-property/core
uv run --group chem python prepare_dataset.py \
    --endpoint SR-MMP --train-frac 0.8 --split-seed 0 --out ../data
```

CPU only, ~28s (network fetch + RDKit parse), $0.
`data/raw/` (the downloaded Tox21 CSV) is git-ignored and re-downloads on
each run; `data/train.csv`, `data/test.csv`, and `data/split_summary.json`
are committed directly, since stage 01 reads them and they are small (356KB
combined) relative to re-running the network fetch and RDKit parse to
reproduce them.

## What this stage does not establish

No model, of any kind, has been trained or evaluated against this split.
Whether a descriptor baseline or a trained model beats anything on SR-MMP is
stage 01's question, not this one. The endpoint choice is specific to SR-MMP's
own balance and single-mechanism story — it is not a claim that SR-MMP is Tox21's
most important or most representative endpoint by any other measure, and
nothing here generalizes to a different endpoint without repeating this stage
against it.

**Next:** [stage 01](../01-descriptor-baseline-and-model/) fits the descriptor
baseline and the trained model against this exact split.
