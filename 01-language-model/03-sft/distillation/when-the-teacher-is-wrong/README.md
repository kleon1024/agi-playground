---
status: verified
level: frontier
base: scratch
label: When the teacher is wrong
verified: 2026-08-07
---

# When the teacher is wrong, what does distillation copy?

**Question:** the distillation chapter holds teacher quality fixed and asks
which signal transfers. This detour asks the question that chapter's control
deliberately set aside: what happens when the teacher is wrong? Does
distillation have a way to keep the teacher's competence and drop its
errors, or does the student inherit both — and what does a teacher with no
signal at all transfer?

**Before this:** [what can you actually copy from a better model?](../) for
the two paths and the control that isolates the method from the teacher's
quality. This chapter breaks that control on purpose: it is the "teacher is
wrong" arm the parent's table could not run, because the parent's teachers
were API models whose internal errors are not an experiment variable.

## The audit: a teacher with a wrong belief

The audit ([run record](runs/2026-08-07-teacher-error-audit.md)) trains two
teachers on the same corpus: `teacher-good` on clean tinyshakespeare, and
`teacher-noisy` on text where every `e` is replaced by `x` — a deterministic,
*systematically wrong* belief about one letter class, the way a teacher with
a factual blind spot is confidently wrong about one subject. A third
`teacher-random` is untrained. Each teacher then generates completions
(temperature 1.0, seeded), and a small student is trained on those
completions the parent chapter's path one way — copy the words. Three
measured results, each answering one question about teacher error.

## Result one: the teacher's error is in its output distribution, not beside it

```
model                  clean CE   x rate   e rate
-------------------------------------------------
teacher-good              1.520     0.0%    10.3%
teacher-noisy             2.614    10.4%     0.0%
```

The wrong teacher's completions swap the letters: `x` at 10.4%, `e` at 0.0%,
where the clean teacher writes `e` at 10.3% and `x` at 0.0%. The cost is
measurable on clean text: the noisy teacher's cross-entropy is 2.614 against
1.520 for the clean teacher. The error is not a separate quality dimension —
it is carved into the distribution the teacher emits, which is exactly what
distillation trains the student on.

## Result two: the student inherits the teacher's error

```
student-from-good        3.119     0.0%    8.9%
student-from-noisy       3.386    15.7%     0.0%
```

The student trained on the noisy teacher's completions writes `x` at 15.7%
and `e` at 0.0% — the wrong belief transferred, and then some. The student
trained on the clean teacher writes `e` at 8.9% and `x` at 0.0%. Two students
with identical architecture, identical training recipe, identical number of
steps: the only difference is who wrote the answers, and the wrong belief
rode along in them. Read the sample completions in the run record — the
noisy lineage produces `thx` and `hxrxin` where the clean lineage produces
`the` and `herring` — and the swap is visible in every line.

This is the mechanism behind the literature's "imitation falls short on
factuality": Gudibande et al.,
[The False Promise of Imitating Proprietary LLMs](https://arxiv.org/abs/2305.15717)
(ICLR 2024) find that imitation training transfers style, persona, and
instruction adherence but reliably falls short of the teacher on factuality,
coding, and problem-solving — and the reason is structural, not a matter of
more data: correctness the teacher does not have cannot be copied, while
the errors the teacher does have are in the distribution the student trains
on. Stanton et al.,
[Does Knowledge Distillation Really Work?](https://arxiv.org/abs/2106.05945)
(NeurIPS 2021) add the quantifier this chapter's table shows: distillation
improves generalization, but not by lifting the student past the teacher —
the student inherits the teacher's error surface, which is what makes
"distillation helped" and "we borrowed the teacher's mistakes" two readings
of the same number.

## Result three: a teacher with no signal transfers nothing — and poisons

```
teacher-random            4.322     0.0%     5.0%
student-from-random       5.840     4.6%     5.5%
base student (no teacher) 4.209     0.0%     5.0%
```

The untrained teacher's completions contain no signal, and the student
trained on them is *worse* than a student that never distilled at all:
5.840 against 4.209 clean cross-entropy. Distillation is not a lossless
pipe — it transfers the teacher's distribution, and a distribution with no
structure teaches confident garbage. The working version of this is the
parent chapter's control: a weak teacher's output is not free data, and
generating from a model worse than the one you are trying to build is how a
student ends up below its own base checkpoint.

## The fix and its trade

The fix is the three checks the ownership split names, in order: audit the
teacher's error surface per class before anyone distils from it (the `e`
swap shows up as a rate inside the teacher's own output, not as a
model-card quality score); after distillation, measure the student on the
teacher's known error classes rather than on aggregate loss (the swap is a
15.7%-vs-0.0% `x` rate hiding inside CEs that look close, 3.386 vs 3.119);
and evaluate the student under the teacher-strength control the parent
chapter requires, so "student improved" is separated from "student copied a
better teacher".

The trade is that every check costs eval design and generation budget. A
per-class audit requires deciding which slices the student will be asked
about before the teacher is chosen, and it cannot see error classes nobody
thought to slice. The inheritance check on known classes is cheap after the
fact but only as good as the audit that named the classes. And the ceiling
claim is a constraint, not a comfort: a student cannot be expected to
exceed the teacher on the teacher's own errors, so the honest eval reports
the ceiling rather than dressing it up as progress. The no-signal result
prices the biggest trade of all: teacher output is not free data —
student-from-random lands at 5.840 against a 4.209 base, a confidently
wrong prior replacing a weak one — so screening teacher quality before
generating costs tokens, and skipping the screen costs the student's own
baseline.

## Who owns it

- **The data team** owns the teacher's error surface before anyone distils
  from it: a per-class accuracy audit of the teacher on the slices the
  student will be asked about. The audit's `e`-class swap is the shape of
  that check — the error shows up as a rate inside the teacher's own output,
  not as a quality score on the model card.
- **The model team** owns the inheritance check: after distillation, measure
  the student on the *teacher's* known error classes, not just aggregate
  loss. Aggregate clean CE hides the swap (3.386 looks close to 3.119); the
  per-class rate sees it (15.7% vs 0.0%).
- **The eval team** owns the ceiling claim: a student distilled from a
  teacher cannot be expected to exceed the teacher on the teacher's errors,
  so the eval has to separate "student improved" from "student copied a
  better teacher" — the parent chapter's teacher-strength control.
- **The product owner** owns the choice of teacher in the first place:
  whose answers are the student allowed to inherit, and which error surface
  comes with them.

When nobody owns the teacher's error surface, the symptom is a distilled
model that is fluent and wrong in the same places its teacher was wrong —
and the wrongness is attributed to the student, the data, or the
architecture before anyone re-runs the per-class audit on the teacher.

## What this chapter does not prove

This is a mechanism demo at char scale on a toy corpus, per the
evidence-scale rule. It proves the inheritance mechanism exists and measures
its shape; the specific rates (10.4% vs 15.7%) do not carry to real
distillation, where teacher error is not a clean letter swap. It also
measures sequence-level distillation (path one) only — logit-level
distillation would soften the swap, not remove it, because the teacher's
distribution still assigns the mass. The factuality-ceiling magnitude is
cited to Gudibande et al. and Stanton et al. above rather than reproduced
here.

## Check your mental model

Answer each before opening it.

**1. The noisy teacher's clean cross-entropy is 2.614 against 1.520 for the
clean teacher. Why does the error cost the teacher CE but the student only
a little (3.386 vs 3.119)?**

<details>
<summary>Answer</summary>

The teacher is a larger model and the error is confined to one letter class,
so the swap costs it the cross-entropy of being confidently wrong at every
`e` position. The student is small and its aggregate CE is dominated by how
little it learned overall, so the class-specific penalty is a smaller
fraction of a larger number. Aggregate CE under-weights a concentrated
error — which is why the per-class `x`/`e` rates are the inheritance
check, not the CE. The swap is visible in the rates (15.7% vs 0.0% `x`)
even where the CE numbers look close.

</details>

**2. Why can a student be *worse* than its own untrained base after
distilling from a no-signal teacher?**

<details>
<summary>Answer</summary>

Distillation is supervised fine-tuning on the teacher's output, so the
student's weights move toward reproducing that output. When the output is
structured garbage (an untrained model's completions), the student learns
confident wrong predictions and its clean-text cross-entropy rises above the
untrained baseline — it traded a weak prior for a confidently wrong one. The
measured version is student-from-random at 5.840 vs base 4.209. This is why
the parent chapter's control holds teacher strength near the student's
scale: a weak teacher is not free data, it is data with a cost.

</details>

**3. The audit's aggregate table shows student-from-good at 3.119 and
student-from-noisy at 3.386 — close numbers. What measurement sees the
difference the aggregate cannot?**

<details>
<summary>Answer</summary>

The per-class letter rates: the noisy lineage writes `x` at 15.7% and `e` at
0.0%, the clean lineage writes `e` at 8.9% and `x` at 0.0%. The swap is
almost invisible in aggregate CE (0.267 apart) and unmistakable per class
(15.7 vs 0.0 percentage points apart). The same structure applies to real
models: a teacher with one wrong subject passes that subject's errors to the
student, and the check that catches it is a slice-wise eval on the teacher's
known error classes — never the aggregate number.

</details>

## Next

Return to [what can you actually copy from a better model?](../README.md)
with the teacher-error arm now measured: the parent's control (hold teacher
quality fixed) is what makes "distillation helped" mean anything, and this
chapter's swap is what that control protects against. The data-side half of
the same failure — a dirty corpus that teaches the wrong distribution before
any teacher is involved — is [the corpus stage's contamination chapter](../../../00-corpus/when-the-benchmark-is-in-the-train-set/).
