---
status: verified
level: applied
base: none
label: When width memorizes
verified: 2026-08-06
---

# When does representation width start memorizing?

**Question:** [stage 06](../) held the learner fixed and swapped only the
molecule's representation. Its recorded grid also swept the fingerprint's
bit width — a dimension the stage's main path does not headline. What does
width actually buy, and at what point does it buy memorization instead of
generalization?

**Before this:** [stage 06's representation grid](../), including its
RDKit-agreement record.

## The sweep, laid out

The run ([record](runs/2026-08-06-width-memorization.md)) reads the
recorded grid's bit-width sweep on SR-MMP — same molecules, same logistic
learner, only the fingerprint width changes:

| n_bits | train AUC | test AUC | train minus test |
|---:|---:|---:|---:|
| 64 | 0.803 | 0.681 | 0.122 |
| 256 | 0.905 | **0.713** | 0.191 |
| 1,024 | 0.993 | 0.673 | 0.320 |
| 2,048 | 1.000 | 0.653 | 0.346 |

Two readings, and the second is the point:

**Test AUC peaks at 256 bits and declines beyond.** Going wider — 1,024,
2,048 bits — makes the held-out result *worse* (0.713 to 0.673 to 0.653),
with spread tiny at every width, so the decline is not noise. There is a
knee, and the sweep measures it at 256 bits for this endpoint.

**Train AUC never stops climbing, so the gap is the story.** The learner
memorizes the training scaffold distribution almost perfectly at 2,048 bits
(train AUC 1.000) while test AUC falls — the gap grows monotonically 0.122
to 0.346. Width adds capacity the logistic learner uses to fit the training
set, and the scaffold split is what stops that memorization from transferring.
This is the same mechanism as the model-size axis in SFT, expressed in
representation width: more capacity without more generalizable signal is
memorization, measured.

## The representation is faithful in ordering, not in bits

The RDKit-agreement record completes the picture: the core fingerprint
agrees with RDKit at rank level (Tanimoto Spearman 0.901, mean difference
0.017) but is never bit-identical (0 of 60 molecules). The representation is
the field's, the bits are this repo's — which is why the width sweep's
conclusion belongs to the representation *family* (circular fingerprints),
not to this repository's bit convention.

## Evidence boundary

One endpoint (SR-MMP), three seeds per width, the recorded grid's own
settings. It shows the knee at 256 bits and the monotone memorization gap
for this endpoint and learner; it does not claim the knee transfers across
endpoints (stage 06's note says per-endpoint verdicts only), and it does not
measure whether a different learner (not logistic regression) would use the
extra width differently.

## Check your mental model

Answer each before opening it.

**1. Why does test AUC fall while train AUC approaches 1.0 as the fingerprint
widens?**

<details>
<summary>Answer</summary>

Because width is capacity. A 2,048-bit fingerprint gives the logistic
learner enough dimensions to fit the training molecules' scaffold
distribution almost perfectly, and the scaffold split prevents that fit from
transferring to unseen scaffolds — so the extra width shows up entirely in
the train-minus-test gap. The learner is not "better" at 2,048 bits; it is
better at remembering.

</details>

**2. The RDKit agreement is 0.901 by rank but 0/60 bit-identical. Which number
matters for the sweep's conclusion?**

<details>
<summary>Answer</summary>

The rank agreement. The sweep's conclusion is about circular fingerprints as
a representation family — how width trades against generalization — and a
Tanimoto rank correlation of 0.901 says the core fingerprint orders
molecules like RDKit's does. The bit differences are an implementation
detail that would shift absolute numbers but not the shape of the width
curve; the curve's shape is the claim.

</details>

## Next

Back to [stage 06's grid](../), or forward to the mission's
[report](../../02-report/) where the cross-endpoint verdict is held against
the acceptance list.
