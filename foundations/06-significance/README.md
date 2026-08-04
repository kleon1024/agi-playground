---
status: verified
level: applied
verified: 2026-08-02
base: scratch
label: Statistical significance
---

# Model A scored 74%. Model B scored 71%. Is that a real difference?

[why should anyone believe the report?](../../missions/01-language-model-agent/07-eval/why-believe-the-number/)
already tells you not to trust a bare point estimate and gives you a
single-model confidence interval to prove it. This chapter answers the
question that actually decides a ship/reject call: when you have two scores
on the same task set, how much of their difference is signal, and how much is
the sampling noise of a finite eval set?

**Before this:** [metric gaming](../../missions/01-language-model-agent/07-eval/metric-gaming/) asks whether a score's
*meaning* survives optimization pressure. This chapter assumes the metric
means what you think it does, and asks a narrower question: given two
measured scores, is their gap distinguishable from chance?

## 1. The problem: a score is a sample statistic, not a fact

A pass rate on N held-out items is an estimate of the true, unobservable
pass rate a system would show over infinite items — same idea [Section
the evaluation stage](../../missions/01-language-model-agent/07-eval/why-believe-the-number/) already
applies to a single score. Two systems scored on the same N items each carry
their own sampling noise, and their *difference* carries the combination of
both. A 3-point gap on 30 items and a 3-point gap on 3,000 items are not
comparable claims, even though the headline number is identical.

## 2. The mental model: pairing cancels the difficulty you don't care about

If Model A and Model B are scored on the *same* items, each item's difficulty
affects both scores together — a hard item is hard for both, an easy item is
easy for both. A test that treats the two score lists as independent samples
throws that shared structure away. A **paired** test keeps every item's two
outcomes locked together and asks only about the per-item *difference*,
which cancels the item-difficulty noise neither model's score alone can
remove. This is why the eval chapter's own Section 6 says to "preserve task
pairing and inspect the disagreements" rather than just comparing two
marginal success rates.

## 3. The mechanism: resample items, not model outputs

`core/bootstrap_significance.py` builds a synthetic paired eval: each item
gets a random difficulty, Model A carries a fixed +0.06 true edge over Model
B in per-item pass probability (symmetric around the item's own difficulty),
and a single Bernoulli draw per item produces the observed pass/fail —
exactly the shape of a real per-item eval record.

The **paired bootstrap** (Efron, 1979; adopted for comparing system scores in
Koehn, 2004) does not resample two independent populations. It resamples
*item indices*, with replacement, and applies the same resampled index list
to both A's and B's outcomes — so on every resample, item difficulty still
cancels out of the differenced statistic the same way it did in the real
data. Repeat this thousands of times and the spread of `mean(A) - mean(B)`
across resamples is the empirical distribution of the gap; its 2.5th and
97.5th percentiles are a 95% confidence interval.

## 4. Turn the knob: the same true effect, two item-set sizes

<!-- interactive: BootstrapSignificance -->

Both conditions above share the identical generator and the identical
`true_effect = 0.06` — the only thing that changes is how many items were
sampled, 300 versus 25.

## 5. Observed consequence: the bigger-looking gap is the less certain one

At n=300, the observed gap is 0.1333 and the 95% bootstrap CI is (0.0600,
0.2067) — entirely above zero. At n=25, the observed gap is *larger*,
0.2000, and the 95% CI is (−0.0400, 0.4400) — it includes zero. The same
true +0.06 edge, generated the same way, produces a bigger point estimate at
the smaller sample and a wider, zero-including interval around it. Trusting
the point estimate alone would rank the n=25 result as the stronger win; the
interval says the opposite — it is the one result that cannot rule out no
difference at all. Full numbers: [`runs/2026-08-02-bootstrap-significance.md`](runs/2026-08-02-bootstrap-significance.md).

## Brief history

The resampling loop in `core/` is one of the oldest things in this repository,
and the argument for running it routinely is one of the newest.

<!-- interactive: BootstrapLineage -->

## What this toy does not establish

- **Real eval-harness variance.** The per-item outcomes here come from a
  synthetic generator with a known, fixed true effect. A real evaluation's
  noise sources (annotator disagreement, prompt sensitivity, non-determinism
  in generation) are not modeled and may not resemble this toy's independent
  Gaussian-plus-Bernoulli construction.
- **Non-paired designs.** This chapter only builds the paired case, which
  this repository's own eval chapter recommends as the default when both
  systems share a task set. An unpaired comparison (different systems scored
  on different item sets) needs a different bootstrap construction not built
  here.
- **Multiple-comparisons correction.** Comparing many models or many
  configurations at once inflates the chance that at least one pairwise gap
  looks significant by chance alone. This is a real, well-studied problem
  (family-wise error rate, false discovery rate corrections) that this
  chapter's single pairwise comparison does not address.
- **A universal effect size.** The `true_effect = 0.06` and the two item
  counts (300, 25) were chosen to produce a clean, legible teaching case in
  this run's own numbers. They say nothing about what sample size a specific
  real eval needs — that depends on the real effect size and per-item noise,
  neither of which this toy's synthetic values are a substitute for.

## Reproduce it

```bash
cd foundations/06-significance/core
python3 bootstrap_significance.py --seed 0 --out ../runs/bootstrap-run.json
```

Deterministic given `--seed`. CPU only, well under 1 second, \$0 cost.

## Check your mental model

**1. Why does pairing matter here, given that an unpaired test would also
compare the same two score lists?**

<details>
<summary>Answer</summary>

Because item difficulty affects both models' scores on the same item
together — a hard item pulls both A's and B's per-item outcome down, an easy
item pulls both up. An unpaired test discards which items produced which
outcomes and just compares two independent-looking lists of numbers, so
that shared item-level noise stays mixed into the comparison instead of
cancelling out. The paired bootstrap resamples the same item index into
both A's and B's outcome lists on every resample, so whatever that item's
difficulty contributed to both scores cancels out of the *difference*
exactly the way it did in the original data — which is why pairing
increases power (a narrower interval) for the same underlying data.

</details>

**2. The n=25 condition has a larger observed gap than n=300, but a CI that
includes zero. What does that combination tell you, and what would it be a
mistake to conclude?**

<details>
<summary>Answer</summary>

It tells you the n=25 result is *less certain*, not that the effect is
smaller — the bigger point estimate at small N is exactly what you'd expect
noise to occasionally produce, whether or not a real effect exists
underneath it. It would be a mistake to read "the observed gap is bigger" as
"this is the stronger result" — the interval, not the point estimate, is
what tells you how much to trust the number. In this case, the interval says
n=25 alone cannot rule out zero difference at all, despite showing what
looks like the bigger effect.

</details>

**3. This chapter's true effect and both item counts were chosen by the
author before running the script. Why doesn't that undermine the result?**

<details>
<summary>Answer</summary>

Because the *inputs* being chosen for a clean, legible demonstration
doesn't change what the bootstrap procedure computes from the resulting
data — the 95% CI at each sample size is a real, deterministic function
(given the seed) of the actual generated outcomes, not an assumed or
asserted number. What would undermine the result is choosing the *reported
seed* after seeing many seeds' outputs and cherry-picking one that tells a
flattering story — which is exactly why the "What this toy does not
establish" section says the specific effect size and item counts don't
generalize to what a real eval needs, even though the mechanism (paired
bootstrap resampling) generalizes fine.

</details>

**4. A real eval task set usually can't be re-run at an arbitrary size —
you have the items you have. What does this chapter's finding actually
recommend doing about that?**

<details>
<summary>Answer</summary>

It recommends computing the bootstrap CI on whatever item set you actually
have, and reporting the interval alongside the point estimate rather than
the point estimate alone — the chapter never claims you can choose your
sample size at will. The practical use of the small-N case here is
diagnostic: if your own eval set is small and the CI on an observed gap
includes zero, that is real information (the gap is not yet distinguishable
from noise at this task-set size), not a reason to report the gap as a win
anyway. The fix, when one exists, is collecting more held-out items before
trusting a close comparison, not reinterpreting the interval you already
have.

</details>

## Next

Return to [why should anyone believe the report?](../../missions/01-language-model-agent/07-eval/why-believe-the-number/)
to see this same discipline applied to a single model's score before ever
reaching a two-system comparison. If you are comparing more than two systems
or configurations at once, the multiple-comparisons problem named above is
the next open question this chapter does not answer.

[The evaluation landscape](../../missions/01-language-model-agent/07-eval/LANDSCAPE.md) names the production libraries
that implement paired bootstrap and other significance tests at scale.
