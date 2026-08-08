---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Descriptor baseline and model
---

# Does a small trained model beat the descriptor baseline on SR-MMP?

**Question:** stage 00 fixed the endpoint (SR-MMP) and the split (scaffold,
measured zero overlap). This stage asks the mission's actual decision: does a
small model trained on molecular structure beat a logistic-regression-over-
descriptors baseline, by more than the spread across seeds — or is the honest
answer "no result"?

**The artifact this stage produces** is two numbers on the same held-out
scaffold split, each with a 3-seed spread: the descriptor baseline's test
ROC-AUC, and the trained model's.

**Before this:** [stage 00](../00-dataset-and-property/), which supplies
`train.csv`/`test.csv` and the measured scaffold-overlap guarantee this
stage's comparison depends on.

## Baseline 1: logistic regression over RDKit descriptors

[`core/descriptors.py`](core/descriptors.py) computes ten standard,
fixed descriptors per molecule (no learning beyond the final linear fit):
molecular weight, LogP, TPSA, H-bond donors/acceptors, rotatable bonds, ring
count, aromatic ring count, fraction of sp3 carbons, heteroatom count.
[`core/descriptor_baseline.py`](core/descriptor_baseline.py) standardizes
these against the train split's own mean/std and fits logistic regression
from scratch (batch gradient descent on the logistic loss — no `sklearn`;
`mission.yaml`'s `chem` dependency group adds RDKit, nothing else).

## Baseline 2: the published MoleculeNet number, and what could not be found

`mission.yaml` asks for "the published MoleculeNet baseline for the chosen
endpoint (Wu et al., 2018)... named, dated, and dependent on matching their
scaffold-split protocol." Both the paper's PMC full text and its supplementary
description were checked directly (not recalled from training data) before
writing this section.

**What the primary source actually reports:** for the Tox21 dataset, Wu et al.
2018 states results are evaluated "by AUC-ROC on random split" — a **random**
split, not a scaffold split, for this dataset specifically — and reports only
the **mean ROC-AUC across all 12 tasks**, not a per-endpoint breakdown, in the
paper's main text: KernelSVM (best conventional descriptor-based method)
0.822, GC — graph convolution (best learned-representation method) 0.829, on
their held-out test set. Per-task numbers are stated to exist only in
supplementary tables not available through the sources checked here.

**This means two honest caveats, not a clean comparison:**

1. **No genuine per-endpoint SR-MMP number could be found** in the primary
   source. Numbers describing SR-MMP or NR-AhR specifically (e.g. isolated
   claims of ~0.90-0.92 AUC surfaced by web search) could not be traced to,
   or confirmed against, the original paper or any source cited clearly
   enough to verify — per this mission's own rule, an unverifiable number is
   not reported here as fact.
2. **The split methodology does not match.** MoleculeNet's own Tox21 number
   uses a random split; this mission's split is a scaffold split by design
   (`mission.yaml`'s explicit guardrail). A scaffold split is harder — near-
   duplicate structures cannot inflate the score — so even if a comparable
   per-endpoint number existed, it would not be an apples-to-apples baseline
   without adjustment.

The real, citable number carried forward is therefore the **12-task mean**
under a **random split**: KernelSVM 0.822 / GC 0.829 (Wu et al., 2018, Table
3). It is reported beside this stage's result as context for where a
"reasonable descriptor-based ROC-AUC on Tox21" sits in the literature — not as
a same-endpoint, same-split baseline to beat, because it is neither.

## The trained model

`mission.yaml`'s decision names "a small from-scratch model over a learned or
fixed molecular representation." Missions 05, 07, and 08 all reuse mission
01's `Config`/`Transformer` unmodified for a non-text token vocabulary, but
each of those tasks is autoregressive prediction over learned tokens (image
patches, audio codes, video codes) — the same job as language modeling with a
different alphabet. Tox21 is different in kind: one binary label per whole
SMILES string, not a next-token target. Importing `Transformer` whole would
mean training a next-character predictor and grafting a classifier onto an
object optimized for the wrong objective, so
[`core/smiles_model.py`](core/smiles_model.py) instead imports the reusable
*architecture primitives* unmodified — `Config`, `Block` (RoPE attention +
SwiGLU, GQA), `RMSNorm`, straight from
[mission 01's pretraining core](../../01-language-model/02-pretrain/core/model.py)
— and composes them into a purpose-built classifier: character-level SMILES
embedding, four causal blocks, then the hidden state at each sequence's last
real (non-padding) token — which causal attention guarantees has already
attended to every real character before it — through one linear layer to a
single logit. [`core/smiles_tokenizer.py`](core/smiles_tokenizer.py) builds
the character vocabulary from the training split only, with an explicit
`<unk>` for any character only test contains.

That pooling line is the one architectural decision here that has no obvious
right answer from reading it. Change which position the head reads from and
watch what that position has attended to:

<!-- interactive: SmilesPooling -->

The two paths meet again at the same held-out split, and the comparison is what
the stage is for:

<!-- interactive: MoleculePropertyComparison -->

## The fix and its trade

The fix is the verification discipline applied to the published baseline:
the primary source (Wu et al., 2018) was checked directly, and it reports a
12-task mean under a *random* split (KernelSVM 0.822 / GC 0.829), not a
per-endpoint scaffold-split number. The trade is that the comparison stays
honest at the cost of being loose: no genuine per-endpoint SR-MMP number
could be traced and verified, so the reported figure is context for where a
reasonable descriptor-based Tox21 AUC sits, explicitly *not* a
same-endpoint, same-split baseline to beat. An unverifiable web-surfaced
number (~0.90-0.92) is refused rather than repeated, and the split mismatch
is named — a scaffold split is harder than the random split the published
number used, so even a matched per-endpoint number would need adjustment.
A team that copied a number without the verification would present a
cleaner-looking comparison that is a category error.

The second fix-and-trade is architectural: importing mission 01's
`Config`/`Block`/`RMSNorm` primitives unmodified and composing a
character-level SMILES classifier avoids grafting a classifier onto an
autoregressive object optimized for the wrong objective, at the cost of
owning the pooling decision (the last real token's hidden state) as a
deliberate, inspectable choice rather than an inherited default.

## Who owns this loop

- **The evaluation owner** owns the baseline-verification contract: the
  published number is traced to its primary source, dated, and reported
  with the split mismatch stated — never a recalled or unverifiable figure.
- **The model team** owns the architecture reuse and the pooling decision:
  the primitives stay unmodified from mission 01 so the comparison is
  clean, and the last-token pooling is documented as a choice the
  interactive makes the learner reason about.
- **The dataset owner** owns the scaffold split both paths are judged on;
  a baseline and a model compared on the same split are comparable, which
  is the property this stage's pairing exists to guarantee.

## Result

Full per-seed numbers, environment, and the exact commands:
[`runs/2026-08-01-descriptor-and-model.md`](runs/2026-08-01-descriptor-and-model.md).

## What this stage does not establish

This result is specific to SR-MMP, this exact scaffold split, this ten-
descriptor set, and this one architecture and hyperparameter choice for the
trained model — none of it transfers to a different endpoint, split, or
representation without repeating the comparison from scratch. The trained
model here is a from-scratch classifier with no pretraining of any kind; a
model pretrained on a larger molecular corpus first is a different, untested
condition. Nothing here says whether either number would hold under a
different scaffold-split fraction or a different random split seed for the
split itself (only the training seed is varied, 3 times, per `mission.yaml`).

**Next:** [stage 02](../02-report/) holds both results against
`mission.yaml`'s acceptance bar and reports a verdict.

A detour from here: [when does a ten-number baseline beat a trained
model?](when-the-baseline-holds/) — the three-endpoint scoreboard assembled
from the recorded runs: descriptor wins on SR-MMP, the model wins on NR-ER,
and the PPAR no-verdict row is the one with the largest split shift and the
scarcest positives.

The model's structure, drawn: [ten numbers, or 696,065
parameters](two-ways-to-read-a-molecule/) — the two representations read
from the recorded runs: the descriptor's ten-number summary with spread
0.0010 and ~2s/seed versus the character transformer's 0.0159 spread and
~105s/seed, the bias/variance trade the verdict sits on.
