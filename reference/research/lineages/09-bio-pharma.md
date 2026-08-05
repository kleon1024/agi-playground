---
level: reference
---

# The open-source line behind bio-pharma modeling

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission's scoreboard is descriptors beating the trained
model on one endpoint, tying on a second, losing on a third — and its last
stage separates whether that is the features or the learner. Every term in
that comparison is a line of open-source evolution: representations, models,
and the splits that decide whether a number means anything.

## Representations

**SMILES** (Weininger, 1988) gave molecules a string a model can tokenize —
the line's textual route. **ECFP** (Rogers & Hahn, 2010) gave them a
structural fingerprint: which local atomic neighborhoods the molecule
contains, in a fixed bit vector. **Murcko scaffolds** (1996) named the core
structure with substituents stripped off. The tradeoff at this end is what
each representation encodes and drops: fingerprints capture local structure
cheaply and lose global context; SMILES captures connectivity and pays with
tokenization; descriptors (molecular weight, LogP, polar surface area, ring
counts) are ten numbers computed directly from structure — the field's usual
first thing to try.

## Models

The learned line runs from **GCN** (Kipf & Welling, 2017) and **MPNN**
(Gilmer et al., 2017) — message-passing over molecular graphs — through
**GIN** (Xu et al., 2019) and **AttentiveFP**, to SMILES-based language
models (**SMILES-BERT**, 2019; **ChemBERTa**, 2020). **MoleculeNet** (Wu et
al., 2018) standardized the benchmarks and the published baseline numbers.
The tradeoff across the line is the one this mission measures: a small
trained model over SMILES characters versus logistic regression over ten
descriptors — when the baseline wins, the win belongs to the pair, and
nothing says which half earned it.

## Splits

The quietest line is the split. Molecular datasets cluster around a small
number of core scaffolds with different substituents, so a random split
leaks structural similarity across train and test and inflates every number.
The scaffold split groups by Murcko core first — the same principle mission
03 applies to market data with temporal ordering instead of structural
clustering: a held-out set that silently is not held out produces a number
that looks like evidence and is not.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the descriptor
beat/tie/lose scoreboard across three endpoints, the scaffold-split
discipline, the RDKit agreement grid separating representation from learner
— cite their runs. The line does not settle which representation is best; it
says the split is where a number first earns the right to be believed.
