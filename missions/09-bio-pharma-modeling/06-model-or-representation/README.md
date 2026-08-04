---
status: verified
level: applied
base: scratch
verified: 2026-08-05
label: Model or representation
---

# The descriptor baseline keeps winning. Is it the features or the learner?

Three endpoints in, the scoreboard reads: descriptors beat the trained model on
SR-MMP, tie on NR-PPAR-gamma, lose on NR-ER. But every one of those comparisons
changes two things at once. The baseline is *ten physicochemical numbers plus
logistic regression*; the model is *SMILES characters plus a small trained
network*. When the baseline wins, the win belongs to the pair, and nothing says
which half earned it.

This stage separates them by holding the learner fixed and swapping only what
the molecule is turned into.

**Before this:** [is variance the same claim as win/loss?](../05-cross-endpoint-analysis/),
which closed the scarcity question and named this as the kind of stage that
would come next — a different candidate explanatory variable, not another
endpoint from the same panel.

## The swap

Stage 01's `fit_logistic_regression` is imported and run unmodified. The same
molecules, the same scaffold splits written by the stages that introduced each
endpoint, the same three seeds. Only the feature matrix changes:

| Representation | What it encodes | Width |
|---|---|---|
| Descriptors | weight, LogP, polar surface area, ring and atom counts | 10 floats |
| Circular fingerprint | which local atomic neighbourhoods the molecule contains | 2048 bits |

The fingerprint is Morgan's algorithm, [written out in
`core/`](core/circular_fingerprint.py): hash each atom's own invariants, then
twice replace each atom's identifier with a hash of itself and its neighbours,
then fold every identifier produced along the way into 2048 bits. RDKit parses
the SMILES into a graph and does nothing else.

## The result

| Endpoint | Descriptors | Fingerprint | Verdict |
|---|---|---|---|
| SR-MMP | **0.8142** (spread 0.0010) | 0.6534 (0.0010) | descriptors win beyond spread |
| NR-PPAR-gamma | 0.6554 (0.0044) | 0.6564 (0.0023) | inconclusive (gap inside spread) |
| NR-ER | **0.6413** (0.0011) | 0.6140 (0.0012) | descriptors win beyond spread |

Test ROC-AUC, mean of 3 seeds, same decision rule stage 05 used: a gap smaller
than the larger of the two seed spreads is not a result.

Widening the representation by two orders of magnitude did not help anywhere and
cost 0.161 AUC on the endpoint where the descriptor baseline was strongest. So
the baseline was not winning merely because logistic regression on *any* fixed
representation beats this trained model. On SR-MMP, those ten specific numbers
are carrying the signal.

The descriptor column also reproduces stages 01, 03, and 04 exactly — 0.8142,
0.6554, 0.6413, to four decimals — which is the check that this harness is
comparable to the ones those stages ran, not a new pipeline that happens to
produce similar numbers.

## The confound the first run could not rule out

Report the training AUCs beside the test AUCs and a different explanation
appears:

| Endpoint | Descriptors train → test | Fingerprint train → test |
|---|---|---|
| SR-MMP | 0.8519 → 0.8142 (gap 0.038) | 0.9995 → 0.6534 (gap **0.346**) |
| NR-PPAR-gamma | 0.7530 → 0.6554 (gap 0.098) | 0.9998 → 0.6564 (gap **0.343**) |
| NR-ER | 0.6989 → 0.6413 (gap 0.058) | 0.9952 → 0.6140 (gap **0.381**) |

The fingerprint arm is not failing to fit. It is fitting the training set almost
perfectly and then generalizing badly — 2048 unregularized features against
roughly 5,000 training molecules is enough capacity to memorize. "The
representation carries less signal" and "the model at this width overfits" both
predict the low test AUC that was observed.

## Narrowing the fold, to tell them apart

Folding the same identifiers into fewer bits reduces capacity without touching
the algorithm. On SR-MMP, three seeds at each width:

| Bits | Columns ever set | Train AUC | Test AUC | Train − test |
|---|---|---|---|---|
| 64 | 64 | 0.8032 | 0.6812 | 0.122 |
| 256 | 256 | 0.9045 | **0.7135** | 0.191 |
| 1024 | 1024 | 0.9934 | 0.6732 | 0.320 |
| 2048 | 2048 | 0.9995 | 0.6534 | 0.346 |

That is the shape overfitting makes: test performance rises to a peak at 256
bits and then falls as the extra width goes into memorizing, with the train−test
gap climbing monotonically the whole way. Capacity was a real problem, and the
2048-bit number understated the representation.

It also does not rescue the conclusion. The fingerprint's best measured width
reaches 0.7135, and the descriptor baseline sits at 0.8142 on the same split
with the same learner. On this endpoint, ten physicochemical numbers beat
substructure membership even after the substructure arm is given its most
favourable width of the four tried.

## What `prod/` says about the from-scratch fingerprint

Production would not write a hundred lines for this:

```python
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
bits = gen.GetFingerprint(mol)
```

The two cannot agree bit for bit — RDKit hashes atom environments with its own
function, so the same substructure lands on a different index — and over 60
molecules from the SR-MMP test split, **zero** had identical bit sets. What can
be compared is the thing fingerprints are used for. Across all 1,770 pairs, the
Tanimoto similarities from the two implementations rank molecules the same way
to a Spearman correlation of **0.901**, with mean absolute difference 0.017 and
worst case 0.123. Same chemistry, different hash. Details in
[`runs/rdkit-agreement.json`](runs/rdkit-agreement.json).

## What this stage does not establish

The fingerprint arm was never regularized. The width sweep bounds the capacity
explanation but does not eliminate it — an L2 penalty at 2048 bits is an
untried arm, and it could land above 0.7135. Only four widths were tried, and
only on SR-MMP, so the peak at 256 is the best of four measured points rather
than an optimum. Radius stayed at 2 and no count-based or feature-based
fingerprint variant was tested.

Nothing here says the trained SMILES model would behave the same way on
fingerprints; that arm crosses the representation with a different learner and
was not run. And the mission's standing boundary holds: three endpoints from
Tox21, one small public dataset picked for tractability, and no claim about
anti-aging biology, drug efficacy, or pharmacological safety.

## Check your mental model

1. Fingerprint train AUC is 0.9995 and test AUC is 0.6534. Why is that not
   simply "the model is bad"?

<details>
<summary>Answer</summary>

Because a bad model fails on the training set too. This one fits the training
molecules almost perfectly, so the fitting machinery works — what fails is
transfer to molecules it has not seen. That is a capacity story, not a
competence story, and the two need different fixes: a bad model wants more
capacity or better features, an overfitting model wants less capacity or
regularization. Reading 0.6534 without the 0.9995 beside it would have sent the
next experiment in exactly the wrong direction.

</details>

2. Test AUC peaks at 256 bits and falls at 1024 and 2048, using the identical
   fingerprint algorithm. Where did the information go?

<details>
<summary>Answer</summary>

Nowhere — the wider folds carry strictly *more* information, since fewer
distinct substructures collide onto the same bit. What changed is what the
learner does with it. At 2048 features against about 4,600 training molecules,
unregularized logistic regression has enough free parameters to fit noise in the
training labels, and the extra resolution gets spent distinguishing training
molecules rather than generalizing. The narrow fold acts as a crude regularizer:
collisions force unrelated substructures to share a weight, which limits how
finely the model can carve up the training set. The peak is where those two
pressures cross.

</details>

3. The descriptor AUCs here match stages 01, 03, and 04 to four decimals. Why
   does that matter more than it looks?

<details>
<summary>Answer</summary>

Because the comparison this stage makes is only valid if its descriptor arm is
the same measurement those stages made. A new script that loads the same CSVs,
featurizes, standardizes, and fits could easily differ in some small
way — a different split file, a different standardization, a changed number of
epochs — and then the fingerprint number would be measured against a baseline
that no longer matches the mission's published one. Exact reproduction is the
evidence that only the representation changed. If it had come out at 0.81 rather
than 0.8142, the right move would have been to find out why before reading the
fingerprint column at all.

</details>

## Next

This closes the "was it the features or the learner" question for the fixed-
representation arm. What remains untested is the other diagonal: the trained
SMILES model given fingerprints instead of characters, which would complete a
representation-by-learner grid rather than one row of it. Return to
[the mission report](../02-report/) for what the whole chain does and does not
license you to claim.

Primary reference: Rogers & Hahn, *Extended-Connectivity Fingerprints*
(J. Chem. Inf. Model., 2010), for the circular-fingerprint algorithm implemented
in `core/`.
