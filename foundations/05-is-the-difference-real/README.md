---
status: verified
level: applied
base: scratch
verified: 2026-07-30
---

# Does this data help?

**Question:** you have a candidate change to the training mixture from the
previous chapter — a new source, a re-weighted domain, a synthetic
supplement. Does it make the model better, and how many runs are you allowed
to run before you are entitled to answer either way?

[The corpus stage](../../01-language-model/00-corpus/) produced a versioned corpus and an explicit set of mixture
weights. It could not tell you whether those weights were the right ones.
That question needs a comparison: train the same model twice, once on the
current mixture and once with the candidate substituted in, and read the
difference. This chapter is about what has to be true of that comparison
before the difference means anything.

**Before this:** [what has to be true of text before you train on it?](../../01-language-model/00-corpus/). You need a
pipeline whose stages you could change before it is worth measuring whether a
change helped.

## 1. Fix everything except the mixture

An ablation is only informative if exactly one thing moved. Fix the
architecture, the parameter count, the token budget, the evaluation set, and
the set of random seeds before looking at a single result. Vary only the data
mixture between arms. Everything else — including which seeds you will use —
is a decision made in advance, not selected after seeing which one looks
better.

This is also why the comparison runs on a small proxy model rather than the
model you actually intend to ship. Frontier labs cannot afford to test a data
decision at full training scale — a single full run can cost more than the
decision is worth. The proxy exists to make the comparison cheap enough to
repeat, on the assumption that a mixture's relative effect transfers from the
proxy scale to the target scale. That assumption is not free, and section 4 is
about where it breaks.

## 2. One run per arm is not a weak result — it is no result

Train once on the baseline mixture, once on the candidate, and the run that
happens to score higher provides no basis for a decision. At the parameter
and token counts affordable for a proxy comparison, the score any single run
produces already varies with nothing but its random seed — initialization,
data shuffling order, and any other stochastic choice held fixed everywhere
else. That run-to-run spread frequently exceeds the size of the effect a data
change is expected to produce. A single pair of runs cannot separate "the
mixture helped" from "this seed happened to land well."

The quantity worth reporting is therefore not the raw score difference. It is
that difference measured against the spread you would see from seed noise
alone, holding the mixture fixed. Predict, before moving the control, whether
adding seeds will make a fixed apparent gap look more real or make it
dissolve.

<!-- interactive: SeedVariance -->

A harness that always returns a winner has not solved this problem; it has
hidden it. "Not detectable at this scale" must be a result the harness can
actually return, printed with the same confidence as a clear win. A tool that
cannot say "we don't know yet" will manufacture an answer out of noise every
time the true effect is small — which, for most data decisions, it is.

## 3. What makes the multi-seed comparison affordable

A single proxy run being cheap is not sufficient; a multi-seed comparison
across two arms needs to be cheap too, or nobody will run enough seeds to
trust the answer. State the inputs and the arithmetic is recoverable by
anyone reading this, not a number to take on faith.

Suppose one proxy training run takes *R* minutes on a 24GB card, you compare
*M* mixtures, and you commit to *S* seeds per arm before looking at results.
Total wall-clock is *M x S x R* minutes if runs are serial. With *M* = 2,
*S* = 8, and *R* = 20 minutes, that is 320 minutes serial — about five hours —
and the runs are independent of each other, so they parallelize across
whatever workers are available: on four workers at once, the same comparison
finishes in roughly 80 minutes. That is the arithmetic that turns "we cannot
afford to test this" into "this fits in an afternoon." Recompute it with your
own *R* before committing to a seed count; do not adopt someone else's *S* as
a fixed rule.

## 4. Two ways a correct result still fails to transfer

Everything above makes the comparison *sound*. Two confounds can leave it sound
and still wrong about the decision it was run for.

A proxy model has less capacity than the model the decision is for, and curated
data helps a small model disproportionately — so a mixture ranking measured at
proxy scale can invert at target scale. And if the candidate mixture is
model-generated text, an improvement may be measuring the teacher rather than
the generation method, or a benchmark the generator had already seen.

[The two confounds](the-two-confounds/) gives each its control, and the rule
they both point at: synthetic generation works where verification is cheaper
than generation, and fails where the only available filter is the generator
marking its own work.

## 5. What this chapter does not prove

Nothing above establishes that any particular mixture change is a good idea.
No ablation has been run against this repository's own corpus or model; the
harness below demonstrates the mechanics — seed handling, interval
arithmetic, the "not detectable" verdict — on a synthetic task built for that
purpose, not on the dataset from [the corpus stage](../../01-language-model/00-corpus/). A live result needs a fixed
proxy architecture, a committed seed count, and both confounds above checked
before the comparison is trusted at target scale.

## Run the harness

[`core/ablation.py`](core/ablation.py) is a from-scratch, paired multi-seed
A/B harness with no dependencies beyond the standard library. It trains a
tiny bigram character model on two synthetic mixtures — a "reference" domain
that resembles the fixed held-out evaluation, and a "general" domain that
does not — under a run of seeds, and prints the mean difference, the 95%
interval on that difference, and an explicit verdict:

```bash
python core/ablation.py --sweep 1,2,4,8,16,32,64
```

At one seed it refuses to report an interval at all. As the seed count rises,
watch the verdict for the default mixtures cross from "not detectable" to a
declared winner. Run it and the crossover is exactly where the design put it:

```
n=2, 4, 8    NOT DETECTABLE — interval spans zero
n=16         mixture B wins: -0.0273 +/- 0.0209 bits/char
n=32, 64     mixture B wins, point estimate stable at -0.024 to -0.027
```

n=16 is the pivot: at n=8 the 95% interval is -0.0214 ± 0.0271 (spans zero);
at n=16 it is -0.0273 ± 0.0209 (does not). `prod/torch_ablation.py`'s
gradient-trained model and Welch's t-test agree independently at the same
n=16 (p=0.0001) — a different model and a different test, the same
crossover point. Below n=16 here, a reported winner would be reporting noise.
Full output: [`runs/2026-07-30-mixture-ablation-sweep.md`](runs/2026-07-30-mixture-ablation-sweep.md).

Read that crossover for what it is. The two default mixtures and the training
length were **chosen by search** until the effect was small enough to stay
invisible at a handful of seeds and large enough to emerge by a few dozen — a
demonstration tuned to put the crossover on screen, not a natural constant of
this model. Say so out loud, because a chapter arguing that a harness which
cannot report "not detectable" will manufacture wins has no business quietly
manufacturing one. Move `--mixture-a` and `--mixture-b` closer together and the
crossover retreats past any seed count you can afford; move them apart and it
arrives at the first pair. The seed count you need is a property of the effect
you are chasing, which is exactly why it cannot be fixed in advance by
convention.

[`prod/torch_ablation.py`](prod/torch_ablation.py) runs the identical design
against a real gradient-trained model and a proper Welch's t-test in place of
the counting model and the normal-approximation interval — the same
question, answered with the tools an actual proxy-scale ablation would use.

## Check your mental model

**1. Why must the seed set be fixed in advance rather than chosen after seeing
   which seeds produce the preferred result?**

<details>
<summary>Answer</summary>

Because choosing seeds after seeing the results is a way of picking exactly
the noise that flatters the answer you wanted — the seed becomes a second
uncontrolled variable hiding inside what's supposed to be a single-variable
comparison (only the mixture is meant to move). Section 1's whole discipline
— fix architecture, parameters, token budget, eval set, *and the seed set*
before looking at a single result — exists precisely so that "the mixture
did this" can't quietly mean "this particular seed happened to land well and
we picked it."

</details>

**2. What does "not detectable at this scale" mean as a reported outcome, and
   why is a harness that never returns it untrustworthy?**

<details>
<summary>Answer</summary>

It means the observed difference between two mixtures is no larger than the
spread you'd see from seed noise alone, holding the mixture fixed — you
genuinely cannot yet tell "the mixture helped" from "this seed happened to
land well." A harness that always returns a winner hasn't solved that
problem, it's hidden it: since most real data decisions produce a small true
effect, a tool that must always answer will manufacture a winner out of pure
noise every time the effect is too small to detect at the seed count run —
exactly the failure the n=8 "NOT DETECTABLE — interval spans zero" result is
built to demonstrate honestly instead.

</details>

**3. Given a stated per-run time and a seed count, how do you compute the
   wall-clock cost of a two-arm comparison?**

<details>
<summary>Answer</summary>

Serial wall-clock is *M x S x R* minutes — mixtures times seeds-per-arm times
minutes-per-run. With M=2, S=8, R=20, that's 320 minutes (about five hours)
run one at a time. Because the runs are independent of each other, they
parallelize across however many workers are available: on four workers, the
same 320 minutes of total work finishes in roughly 80 minutes. The chapter's
point in showing the arithmetic explicitly is that it's recoverable with your
own *R*, not a fixed number to take on faith — recompute it before deciding
how many seeds you can actually afford.

</details>

**4. Name the two confounds that can leave a statistically sound comparison
   wrong about the decision it was run for.**

<details>
<summary>Answer</summary>

First, proxy-to-target transfer: a proxy model has less capacity than the
model the decision is actually for, and curated data helps a small model
disproportionately more — so a mixture ranking measured at proxy scale can
invert once you scale up. Second, synthetic-data self-grading: if the
candidate mixture is model-generated text, an apparent improvement may really
be measuring the teacher model's own quality rather than the generation
method, or the generator having already seen the benchmark it's being scored
against. Both confounds can survive a comparison that is otherwise perfectly
sound statistically — the seed-variance discipline in this chapter catches
noise, not these two.

</details>

## Next

A mixture decision that survives this harness is still an untrained bet until
it is spent on a real training run. Continue to
[pretraining](../../01-language-model/02-pretrain/) to see what a token budget and a model size
commit you to, or to
[evaluation](../../01-language-model/07-eval/) for the
seed-variance and harness-disclosure machinery this chapter assumed.

Primary references: DoReMi, DataComp-LM, Chinchilla-style scaling-law
methodology, the Phi / "Textbooks Are All You Need" line of synthetic-data
work, Self-Instruct and Alpaca, and benchmark-contamination studies such as
Sainz et al. (2023).
