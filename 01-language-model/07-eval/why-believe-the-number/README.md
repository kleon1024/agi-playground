---
status: draft
level: applied
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

## The fix and its trade

The failure mode is a number that is not miscomputed but false: it does not
mean what a reader will take it to mean, in three ways that each cost
different defenses. Contamination — SWE-bench Verified's public fix PRs are
the answer, not merely the question, and a model trained on post-cutoff
data has plausibly seen them; the documented response is construction, not
detection (SWE-bench Pro from private or undisclosed repositories, with
Terminal-Bench 2.0 cited as the successor generation as of 2026), and the
practical rule is attribution: "SWE-bench Verified, as reported in [paper],
[year]" is a checkable claim and bare "SWE-bench" is not. Judge bias —
position, verbosity, and self-preference are reproducible biases (Zheng et
al., 2023) that no better-worded prompt fixes, because none of them is a
misunderstanding, so the countermeasures are structural: score both
orderings, length control as in AlpacaEval 2.0, judge with a different
model family. Variance — 300 samples at 50% success carries a roughly
±5.7-point 95% bootstrap interval, so two runs four points apart are not
distinguishable from noise, and agentic evaluation compounds that with
seed and environment variance that has nothing to do with instance
sampling.

The fix is the reporting contract that owns all three: date every number,
report both uncertainties (a bootstrap interval over instances, mean plus
standard deviation over seeds — a report with one and not the other has
silently assumed the second away), and validate the judge against a
human-labeled gold set before trusting it on anything uncheckable by hand.
The trade is that each defense is partial, and the missing part is the
important disclosure: you can prefer well-constructed benchmarks but cannot
prove a public benchmark clean for a model whose training data you did not
see; you can measure judge-human agreement but cannot exceed the quality of
the gold set, which is the expensive part nobody reports; and a tighter
interval around a contaminated or biased number is still a contaminated or
biased number. The dated anchors are external: SWE-bench (Jiménez et al.,
2024), the MT-Bench and Chatbot Arena judge-bias results (Zheng et al.,
2023), and the contamination response family this chapter names by version
rather than by vendor.

## Who owns the loop

- **The evaluation team** owns the disclosure contract: date-every-number,
  both-uncertainties reporting, and the tooling refusal to emit a
  single-seed agent score — the report is structured so a bootstrap
  interval without seed spread cannot be produced at all.
- **The data team** owns benchmark selection and contamination risk: prefer
  construction that makes leakage unlikely, version the benchmark family
  (Verified versus Pro is a different trust claim), and record the cutoff
  date beside every quoted number.
- **The product-quality team** owns the gold set: held-out human labels for
  judge validation are the expensive part, and the decision to pay for them
  is what separates a validated instrument from a second model's opinion.
- **The model team** owns the judge choice as a structural countermeasure:
  judging with a different model family than the generator, and inspecting
  judge-human disagreements for the three bias signatures before trusting
  the judge on anything.

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

<details>
<summary>Answer</summary>

The fix PRs are the problem — they are the answer, not just the question. A
model trained on post-cutoff web and code data has plausibly seen the actual
resolution to some fraction of the 500 issues, which is what turns a
capability score into a partial memorization score. The issues being public
is not by itself the problem: an issue statement alone is just a task
description, the same kind of thing any benchmark publishes. It only becomes
a problem once the matching fix sits in the same public corpora a model was
trained on.

</details>

2. Why does a better-worded judge prompt not fix verbosity bias, when it
   plausibly would fix a judge that misunderstood the rubric?

<details>
<summary>Answer</summary>

A misunderstood rubric is a comprehension failure — the judge didn't grasp
what to score, and a clearer prompt can fix that. Verbosity bias is not a
comprehension failure; the judge understood the rubric fine and still favors
longer, more elaborately formatted answers *independent of correctness*,
because that preference is baked into how it was trained, not into how the
question was phrased. Asking it nicely not to doesn't change the underlying
distribution it learned. That's why the fix is structural — length control,
as in AlpacaEval 2.0's length-controlled win rate — rather than a rewritten
prompt.

</details>

3. A report shows 61% with a ±5.7-point bootstrap interval and one seed. Which
   uncertainty is quantified and which is missing?

<details>
<summary>Answer</summary>

Quantified: uncertainty about which instances happened to be sampled — that's
exactly what a bootstrap confidence interval over a fixed instance set
measures. Missing: uncertainty about what the model does on repeated attempts
at the *same* instance, which needs mean ± standard deviation over multiple
seeds/rollouts and simply isn't produced by one seed. The chapter is explicit
that these are two different uncertainties that don't substitute for each
other — a report with a bootstrap interval and one seed has answered the
first question and silently assumed the second away.

</details>

4. You raise the sample count from 300 to 3,000 and the interval narrows. What
   class of error does that not touch at all?

<details>
<summary>Answer</summary>

More samples only shrinks the uncertainty about *which instances* you
happened to draw — it says nothing about the other two failure modes this
chapter names. Contamination (the benchmark's answers leaking into training
data) doesn't shrink with more samples of the same contaminated benchmark;
neither does judge bias (position, verbosity, self-preference), which is a
property of the scoring instrument, not the sample size. And it doesn't touch
seed/rollout variance either — a bigger fixed-instance sample is a different
axis from repeated attempts at the same instance. A tighter interval around
a systematically biased or contaminated number is still a systematically
biased or contaminated number.

</details>

5. Under what circumstance is "we could not tell these two systems apart" the
   correct and complete finding rather than a failed experiment?

<details>
<summary>Answer</summary>

When the measured difference is smaller than the combined noise the
evaluation can't rule out — smaller than the bootstrap interval's width, or
within the seed-to-seed spread of repeated rollouts. The chapter's own
example makes this concrete: two runs four points apart at 300 samples and a
±5.7-point interval are not distinguishable from noise at all. Reporting
"cannot tell apart" in that situation is the honest, complete finding; it
would only be a failed experiment if the tooling that should have quantified
the uncertainty (the bootstrap CI, the seed spread) was never run in the
first place.

</details>

## Next

Return to [stage 07](../) for what a passing mission report has to contain, and
what this mission's evaluation explicitly does not prove. The three failure
modes here are why that section exists in the form it does — every item in it
is a disclosure that stops a correct number from being read as a stronger claim
than it supports.
