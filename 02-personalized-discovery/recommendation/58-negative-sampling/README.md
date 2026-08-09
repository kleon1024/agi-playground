---
status: verified
level: applied
base: scratch
label: Negative sampling
verified: 2026-08-07
---

# Downsampling negatives breaks calibration, not ranking

**Question:** stage 56 and 57 assumed the training set is what it is.
This stage asks what happens when the negatives outnumber the positives
ten thousand to one and a team downsamples to train at all, and answers:
downsampling keeps the ranking and inflates every probability, and the
ratio correction restores calibration — which is why ranking metrics
alone never catch the break.

**Before this:** [stage 16 — CTR calibration](../../ads/16-ctr-calibration/)
for the calibration machinery this stage's correction feeds into.

## The downsample, executed

The run ([record](runs/2026-08-07-negative-sampling.md)) trains the same
logistic model on the full set and on a 10x-downsampled negative set,
then applies the inverse-sampling correction:

| model | auc | ece |
|---|---:|---:|
| full set | 0.659 | 0.011 |
| downsampled | 0.659 | 0.473 |
| downsampled + corrected | 0.659 | 0.017 |

<!-- interactive: NegativeSampling -->

## The mechanism, named

At a 1:1000 positive rate, the gradient is mostly easy negatives, so
teams downsample the negatives to give the positives a vote. The ranking
survives — pairwise order between positives and the sampled negatives is
preserved — but the base rate inside the model changes: a model trained
on 10% positives reports probabilities ten times too high. The
correction inverts the sampling ratio, mapping the model's probability
back onto the true base rate without touching the ranking at all. ECE
moves from 0.473 to 0.017; AUC does not move, because it never saw the
break.

## Why this belongs in the mission

The mission's later stages do arithmetic on probabilities — the value
tree blends them, the auction multiplies them, the budget paces on
them. A sampling artifact that inflates every number by 10x is invisible
to AUC and fatal to every downstream product, so the sampling ratio and
its correction belong in the curriculum next to the calibration chapter,
not inside it.

## The fix and its trade

The fix is to downsample the negatives so the positives get a vote, and
then invert the sampling ratio at prediction time so the model's
probabilities map back onto the true base rate. The executed read prices
both halves: AUC is untouched by sampling (0.659 in every row), while ECE
moves from 0.473 downsampled to 0.017 corrected — ranking metrics never
see the break, and the correction is what the downstream arithmetic
depends on.

The trade, named: the correction is a formula, and its only input is an
operational fact — the ratio actually applied at sampling time. A
mislogged ratio passes straight through (the overcorrects detour lands
the corrected probability half a decimal off), so the fix buys a
calibrated score at the price of a logging contract and a base-rate
check. The cheaper alternative — just downsample and ship the ranking —
looks identical on AUC and quietly inflates every probability the value
tree, auction, and pacing multiply downstream.

## Who owns the loop

- **The sample and data team** owns the exact sampling ratio, logged at
  sampling time — not reconstructed at training time, because a ratio
  that is assumed is a ratio that will be wrong.
- **The model team** owns the correction at prediction time and the
  slice-level calibration check against the observed base rate, which is
  the cheapest detector of a mislogged ratio.
- **The evaluation team** owns the ECE read alongside AUC in the
  acceptance gate — a model whose ranking holds but whose probabilities
  are inflated must fail review, not pass it.
- **The downstream teams** (value tree, auction, pacing) own the contract
  that every probability they consume is base-rate-correct, which is what
  turns a sampling detail into a product-wide defect when it breaks.

## Evidence boundary

The executed synthetic read over a declared 1:100 negative sampling ratio
(illustrative, deterministic). It demonstrates the correction formula;
real systems must log the exact ratio actually applied, because a
misestimated ratio — the overcorrects detour — shifts the corrected
probabilities instead of fixing them.

## Check your mental model

Answer each before opening it.

**1. Why does downsampling leave AUC untouched but destroy ECE?**

<details>
<summary>Answer</summary>

Because AUC only compares pairs — a monotone inflation of every score
keeps the order intact — while calibration compares the score's scale to
the observed base rate, and the base rate changed under sampling. The
two metrics measure different things, and the one that broke is the one
downstream arithmetic depends on.

</details>

**2. What is the correction actually inverting?**

<details>
<summary>Answer</summary>

The sampling ratio applied to the negatives: a model probability q from
the downsampled world maps back to the true probability p by inverting
the odds transform. It is only as good as the ratio it is fed, which is
why production logs the exact ratio at the moment of sampling instead of
reconstructing it later.

</details>

## Next

The ratio matters more as the rate gets extreme: [at 1:1000 the easy
negatives own 99% of the gradient](when-the-negative-rate-is-extreme/) —
the executed read.

The correction can overshoot: [a misestimated ratio leaves the
probabilities off on one side](when-the-correction-overcorrects/) — the
executed read: assuming 1:10 when the real ratio is 1:20 lands the
corrected probability half a decimal too high.
