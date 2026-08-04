---
status: draft
level: applied
label: Molecular property prediction
---

# Does structure alone predict whether a compound is toxic?

**Question:** someone screening candidate compounds needs to decide whether a
small trained model is worth building for one specific, measurable toxicity
property — or whether a descriptor-based baseline they already have is good
enough. Before answering that, they need one honest number: does a model
trained on molecular structure beat the baseline, on a held-out split that
actually holds out, and by how much?

**The artifact this mission follows** is one molecule: a SMILES string, a
declared toxicity endpoint from the Tox21 assay panel, and a prediction that
either matches the withheld label or doesn't. Everything below is about
whether that prediction is worth trusting.

## Why this mission exists, and what it deliberately is not

The curriculum this mission belongs to was asked to cover "science model
systems like anti-aging/pharma." That framing cannot be built honestly here.
No public dataset and no compute budget available to this repository lets
anyone verify a claim about aging biology, drug efficacy, or a real screening
outcome — and this repository's own rule, stated in `AGENTS.md`, is that if
you cannot run it, you do not write the number. An anti-aging claim is not
runnable at this scale, so this mission does not make one.

What survives, narrowed to something real: **Tox21**, a public NIH/EPA/NCATS
dataset of roughly 8,000 compounds with binary toxicity labels across 12
assay endpoints, distributed through MoleculeNet. This mission picks exactly
one endpoint and asks one question about it — does a small trained model beat
the field's standard descriptor-based baseline. That is the entire scope. If
you came here for evidence about anti-aging science, it is not in this
mission, and it will not be, on purpose. Read
[`mission.yaml`](mission.yaml)'s `does_not_prove` section before treating any
result here as more than that.

## What gets measured

**The descriptor baseline** is logistic regression over standard RDKit
descriptors — molecular weight, LogP, topological polar surface area, ring
counts, and similar fixed features computed directly from structure with no
learning involved beyond the final linear fit. This is the field's usual
first thing to try, and it is the control that decides whether a trained
model earns its complexity: if it cannot beat this, training one was not
worth it for this endpoint.

**The published baseline** is MoleculeNet's own reported number for the
chosen endpoint (Wu et al., 2018), read directly from the paper and recorded
with its split methodology, not quoted from memory into this file.

Both baselines are compared against **ROC-AUC** on a **scaffold split** — test
molecules grouped by Murcko scaffold so that near-duplicate structures common
in this kind of data cannot appear on both sides of the split. A random split
would silently leak structural similarity across train and test and inflate
every number measured against it; this mission measures and reports the
scaffold overlap directly rather than assuming a split is clean because it
was shuffled.

## Why a scaffold split, not a random one

Molecular datasets cluster tightly around a small number of core scaffolds
with different substituents attached. A random split puts near-identical
molecules on both sides far more often than the data's raw size suggests,
which lets a model memorize local structure rather than learn anything
general — and still score well. The scaffold split groups by core structure
first, so a held-out result actually tests generalization to structures the
model has not effectively seen before. This is the same category of problem
[mission 03](../03-quantitative-research/)'s train/test discipline addresses
for market data with a different mechanism (temporal ordering instead of
structural clustering) — different domain, same principle: a held-out set
that silently isn't held out produces a number that looks like evidence and
isn't.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Dataset and property](00-dataset-and-property/) | which endpoint, and what does the label actually measure? | verified |
| [01 — Descriptor baseline and model](01-descriptor-baseline-and-model/) | does a small trained model beat the standard descriptor baseline? | verified |
| [02 — Report](02-report/) | scaffold-checked result, and what it does and does not say beyond this one label | verified |
| [03 — Second endpoint](03-second-endpoint/) | does the SR-MMP finding generalize to a second, more imbalanced endpoint? | verified |
| [04 — Third endpoint](04-third-endpoint/) | does stage 03's scarcity-drives-variance hypothesis hold at a third endpoint? | verified |
| [05 — Cross-endpoint analysis](05-cross-endpoint-analysis/) | across all three endpoints, does one variable explain both the variance pattern and who wins? | verified |
| [06 — Model or representation](06-model-or-representation/) | does the descriptor baseline win because of its features or because of its learner? | verified |

Per [the mission contract](../../reference/standards/mission-contract.md), this
contract is declared before any stage is built, so the endpoint, baseline, and
split cannot be chosen after seeing which ones flatter a result. No stage
below is `verified` until it has a real `runs/` entry with the exact command,
dataset version, split seed, and per-seed results — the same bar every other
mission in this repository holds itself to.

## What this will not prove

Restated from [`mission.yaml`](mission.yaml)'s `does_not_prove`, because it is
the part of this mission most likely to be misread if stated only once: this
does not discover, validate, or provide evidence toward any anti-aging or
pharmacological claim. Tox21 and its one endpoint are a narrow, public,
checkable proxy chosen for tractability, not because they relate to aging
biology. A model beating a baseline on one toxicity label says nothing about
drug efficacy, in vivo safety, or the outcome of any real screening pipeline,
and the result does not generalize to a different endpoint, dataset, or
molecular representation without re-running the comparison from scratch.
