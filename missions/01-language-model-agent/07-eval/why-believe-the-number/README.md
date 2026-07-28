---
status: draft
base: scratch
label: Why believe the number
---

# The report is correct. Why should anyone believe it?

[The previous chapter](../) built tooling that refuses to emit a score without
its tokenizer, context length, seed count, baseline, and harness. Suppose it
emits one. Every disclosure field is filled in, the arithmetic is right, and
the report is exactly what the acceptance criteria ask for.

The number can still be false. Not miscomputed — false in the sense that it
does not mean what a reader will take it to mean. This chapter is about the
three ways that happens, and what each one costs to defend against.

## The benchmark has already seen the answer

SWE-bench (Jiménez et al., 2024) scores whether a generated patch makes a real
GitHub issue's test suite pass. SWE-bench Verified — a human-filtered 500-issue
subset meant to remove ambiguous issues — became the number everyone quoted for
coding agents.

Then the problem surfaced. The repositories and their fix PRs are public. A
model trained on post-cutoff web and code data has plausibly seen the *answer*,
not merely the question, on some fraction of those 500 issues. And a static,
published benchmark cannot self-correct for that once it is sitting inside
enough training corpora — the contamination is in the model, and the benchmark
has no way to look.

**SWE-bench Pro** is the field's documented response, built from private or
otherwise undisclosed repositories so the fix is not already circulating. As of
2026, **Terminal-Bench 2.0** is cited alongside it as a successor generation of
agentic coding benchmarks designed with the same lesson in mind.

The practical rule is attribution: "SWE-bench Verified, as reported in [paper],
[year]" is a specific, checkable claim, and bare "SWE-bench" is not, because
this benchmark family's trustworthiness has visibly shifted across versions in
a few years. The lesson outlives the family. **Any static, public benchmark has
a shelf life, and "widely cited" is a different claim from "uncontaminated."**

Note what this does *not* give you: a way to detect contamination in a
benchmark you did not build. You can only prefer benchmarks whose construction
makes it unlikely, and date every number you quote.

## The judge has preferences you did not ask for

Wherever an open-ended answer needs scoring — this mission's generations, an
agent's free-form final response — an LLM judge substitutes for a human rater.
It does not inherit neutral judgment. It inherits specific, reproducible biases
(Zheng et al., 2023, the MT-Bench and Chatbot Arena paper):

| Bias | What it favors | Structural countermeasure |
|---|---|---|
| position | whichever response is shown first | score both orderings, discard cases where the verdict flips |
| verbosity | longer or more elaborately formatted answers, independent of correctness | length control, as in AlpacaEval 2.0's length-controlled win rate |
| self-preference | outputs from the judge's own model family | judge with a different model than generated the answer |

The important word is *structural*. None of these is solved by a
better-worded judge prompt, because none of them is a misunderstanding — the
judge is doing what it was trained to do, and being asked nicely not to does
not change the distribution.

The detection protocol is concrete, and it costs human labeling: hold out a
small human-labeled gold set, measure judge-human agreement, and inspect the
disagreements for exactly these three signatures before trusting the judge on
anything you cannot check by hand. If you will not pay for the gold set, you do
not have a validated instrument; you have a second model's opinion.

## The difference you measured is smaller than the noise

A point estimate from a few hundred samples carries a confidence interval wide
enough to make most reported differences look far more decisive than they are.
**300 samples at a 50% success rate carries a roughly ±5.7-point 95% bootstrap
interval**, so two runs four points apart at that sample size are not
distinguishable from noise at all.

Agentic evaluation compounds this with variance that has nothing to do with
sampling which instances you scored. Nonzero temperature, environment
nondeterminism, and the multi-turn compounding of small per-step differences
all mean the identical agent, scored twice, lands in different places for
reasons unrelated to anything you changed.

Those are two different uncertainties and they do not substitute for each
other, which is why `core/evaluate.py` reports both:

- a **bootstrap confidence interval** over the fixed set of `loglik`
  instances — uncertainty about *which instances you happened to sample*;
- **mean ± standard deviation over `--seeds` real rollouts** for `generate`
  instances and agent transcripts — uncertainty about *what the model does on
  repeated attempts at the same instance*.

A report with a bootstrap interval and one seed has answered the first question
and silently assumed the second away. The tooling will not produce it.

Change the task count below and decide for yourself when a four-point
difference becomes meaningful. The repeated bars hold the system completely
fixed and vary only the sample.

<!-- interactive: EvaluationUncertainty -->

## What this chapter cannot do for you

Each of the three defenses is partial, and saying which part is missing is more
useful than the defense itself.

Contamination: you can prefer well-constructed benchmarks and date your quotes.
You cannot prove a public benchmark is clean for a model whose training data
you did not see. Judges: you can measure agreement against a gold set. You
cannot exceed the quality of that gold set, and building one is the expensive
part nobody reports. Variance: seeds and bootstrap intervals tell you how
uncertain a number is. Neither tells you the number measures the thing you care
about — a tight interval around the wrong metric is a precise, confident,
useless result.

## Exercises

1. **Compute the bootstrap interval by hand.** Take five `loglik` correctness
   values, resample 2,000 times with `bootstrap_ci`, and compare the interval
   width to the 300-sample, 50%-success-rate example above. Confirm yours is
   wider, and explain why it must be at n=5.
2. **Force the single-seed refusal.** Build a `tasks.jsonl` with one `generate`
   instance and run `tasks` without `--seeds`. Read the error, then re-run with
   `--seeds 3` and confirm `per_seed_accuracy` actually varies rather than
   repeating one value three times.
3. **Date a contaminated number.** Find one paper quoting SWE-bench Verified and
   one quoting SWE-bench Pro for the same model family, and write two sentences
   on what the second specifically changes about the first's contamination risk.

## Check your mental model

1. A benchmark's fix PRs are public and its issues are public. Which of the two
   makes the score untrustworthy, and why is only one of them a problem?
2. Why does a better-worded judge prompt not fix verbosity bias, when it
   plausibly would fix a judge that misunderstood the rubric?
3. A report shows 61% with a ±5.7-point bootstrap interval and one seed. Which
   uncertainty is quantified and which is missing?
4. You raise the sample count from 300 to 3,000 and the interval narrows. What
   class of error does that not touch at all?
5. Under what circumstance is "we could not tell these two systems apart" the
   correct and complete finding rather than a failed experiment?

## Next

Return to [stage 07](../) for what a passing mission report has to contain, and
what this mission's evaluation explicitly does not prove. The three failure
modes here are why that section exists in the form it does — every item in it
is a disclosure that stops a correct number from being read as a stronger claim
than it supports.
