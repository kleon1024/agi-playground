---
status: verified
level: frontier
base: scratch
---

# What can you actually copy from a better model?

**Question:** you can afford to *generate* from a strong model but not to
*train* one. What transfers, what does not, and what does a gain afterwards
actually prove?

**The artifact this chapter follows** is one training example — the question
"What is the capital of France?" and the teacher's answer to it. Everything
below is about how much of that answer you are able to keep.

**What you will be able to decide:** which of two distillation paths your
situation permits, what the cheaper one costs you in transferred signal, and
what control has to be in place before "distillation helped" means anything.

[Stage 03 of the language-model system](../)
arrives here when the question becomes where its supervision should come from.
Take back the target format and the tokenizer constraint; both decide what the
stage can and cannot buy.

**Before this:** [stage 03 — SFT](../), for what supervised
fine-tuning already does with a fixed dataset. This chapter only changes who
wrote the answers in it.

## The line that decides everything: do you own the teacher's weights?

Not "which signal is better." That question comes second, and for most people
it never comes at all.

| | You have API access | You own the weights |
|---|---|---|
| The teacher's chosen words | yes | yes |
| The teacher's full distribution | **no** | yes |
| What you can run | sequence-level | either |

An API emits text. That is the whole constraint, and it is why nearly every
distillation you have heard of is text-only. DeepSeek-R1-Distill-Qwen-7B and
its siblings (2025) are plain supervised fine-tuning on roughly 800,000
R1-generated samples, with no logits involved at any point. OpenThoughts,
Bespoke-Stratos, OpenR1-Math and Magpie are all trace collections. When people
say "distillation" today they usually mean this.

Distribution-level distillation is alive, but it lives where one organisation
owns both models. Gemma 2's small variants (2024) were trained against a larger
teacher's distributions rather than on next-token prediction; Llama 3.2's 1B
and 3B (2024) used logits from Llama 3.1 8B and 70B as token-level targets;
Nvidia's Minitron line (2024) prunes a large model and distils the remainder
back from its parent. External results, attributed and dated — none of them
reproduced here.

Find your row; the rest of this chapter is what it costs.

## Path one: copy the words

If you see text and not logits, you generate completions from the teacher and
train the student on them with ordinary next-token cross-entropy. There is no
new mechanism: this is the chat-JSONL shape and the loss masking that
[stage 03](../README.md#loss-masking-worked)
already covers. Mask the prompt, train the assistant tokens, imitate style
rather than correctness. The only thing that changed is who wrote the assistant
turn.

This is also the fallback whenever a shared tokenizer is unavailable — a
constraint that ends path two before it starts.

## Path two: copy the shape of the teacher's doubt

A one-hot label — 1 for the right token, 0 for everything else — says `Paris`
and nothing more. The teacher's logits say something richer: heavy mass on
Paris, real but smaller mass on Lyon and Marseille, effectively none on
`banana`. That spread encodes *which mistakes are plausible*, and cross-entropy
against a one-hot label discards all of it. A KL divergence — a measure of how
far one probability distribution sits from another — keeps it.

Temperature controls how much of the structure survives comparison. Both
distributions are softened by the same $T$ before the divergence is taken:

$$
p_i(T) = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}
$$

At $T{=}1$ this is the teacher's raw call. Raising $T$ flattens the
distribution so the small probabilities become visible instead of rounding into
nothing.

**Worked, on illustrative logits** of 8.0 for `Paris`, 5.0 for `Lyon`, and 2.0
for `banana`:

| | `Paris` | `Lyon` | `banana` |
|---|---:|---:|---:|
| $T=1$ | 95.03% | 4.73% | 0.24% |
| $T=2$ | 78.56% | 17.53% | 3.91% |
| $T=4$ | 58.98% | 27.86% | 13.16% |

Read the `banana` column, not the `Paris` one. Temperature is not a free
magnifier of useful structure: at $T=4$ the nonsense token holds more mass than
the plausible alternative did at $T=1$. Raising $T$ buys visibility into the
teacher's ranking and pays for it by teaching the student that absurd
continuations are ordinary. That trade, not the flattening, is what a
temperature setting is choosing between.

Softening also shrinks the gradient by roughly $1/T$, so the loss carries a
$T^2$ factor to keep update magnitudes comparable across temperatures:

$$
L_{\text{KD}} = -T^2 \sum_{i} p_i^{\text{teacher}}(T)\,\log p_i^{\text{student}}(T)
$$

Move temperature below and watch the one-hot label sit still while the
teacher's softened distribution stretches and collapses around it. That gap is
what path one cannot transmit.

<!-- interactive: DistillationTargets -->

## Path two is closed to this student, and probably to yours

Two things have to be true before you can run it. You need somewhere to put the
teacher's distribution — at the usual top-16, 64 extra bytes per token, or
192 GB alongside a 3.0B-token corpus. And the student has to speak the *same*
vocabulary as the teacher, because a divergence between two tokenizers compares
unrelated strings and returns a number anyway.

This student fails the second test. Its tokenizer was trained from scratch in
[stage 01](../../01-tokenizer/), 16,512
entries, shared with no public model in existence.
[What path two requires](what-path-two-requires/) prices the storage, lists the
three escapes from the tokenizer wall, and shows why that constraint makes
tokenizer similarity weak evidence when one lab accuses another of distilling
its model.

Everything below applies to path one — the path almost everyone is on.

## What a distillation gain is allowed to mean

Two effects get confused here, and they push in opposite directions.

**Within one teacher, the distribution beats the text.** More signal per token,
better sample efficiency. This is the result the distillation literature
reports, and it is measured with the teacher held fixed.

**Across teachers, teacher quality usually dominates signal richness.** A much
stronger black-box teacher's plain text will normally beat a weak local
teacher's full distribution. Which means the honest comparison for someone
choosing a path is not "logits versus text" — it is "the best teacher I can
reach, versus the best teacher whose weights I hold."

Either way, one control is mandatory. If the teacher is far stronger than the
student, an improvement measures *the teacher's* quality, not the method —
almost anything a much stronger model supervises will look like progress. The
control that isolates the method is generating targets from a model comparably
sized to the student and comparing against that. Without it, "distillation
helped" and "we borrowed a bigger model's competence" are the same number
wearing different labels.

## The measured version, and why it refuses to answer

That control was run. `core/generate_traces.py` holds one set of 3,000 prompts
fixed and varies only who wrote the assistant turn — the source dataset's own
annotators, a 0.5B instruct teacher, a 7B instruct teacher — then fine-tunes the
88M student on each corpus for an identical 102 steps. Step-matching is not
bookkeeping: model teachers write longer answers, so equal *epochs* would have
handed them 32% and 56% more gradient steps than the human arm.

Scoring all three students against all three authors' held-out answers to the
same test prompts gives this, averaged over three seeds:

| Trained on | ref: human | ref: teacher-small | ref: teacher-large |
|---|---|---|---|
| human | **2.9074** | 2.0181 | 2.3819 |
| teacher-small | 3.0263 | **1.8320** | 2.2925 |
| teacher-large | 2.9918 | 1.8878 | **2.2763** |
| base, no SFT | 3.1916 | 2.3649 | 2.6895 |

**Every arm wins on its own author, decisively.** So the experiment everybody
runs — teacher corpus against human corpus, judged by held-out loss — picks its
winner when it picks its reference set. Choose a human held-out set and human
data wins; choose the teacher's and the teacher's data wins, from the same code.
Held-out loss here measures author-matching, not answer quality, and one column
of that table would have supported whichever conclusion its author preferred.

Two things it does support. Every arm beats the base checkpoint on every
reference set, so learning the chat format does not depend on who wrote the
answers. And off the diagonal, on human reference text, the 7B teacher's data
transfers better than the 0.5B teacher's (2.9918 against 3.0263) — the one
quality signal in the run not confounded with the reference set's author.

Ranking the corpora needs an author-neutral metric, a judge or a downstream
task. This run has neither, and says so. Full boundary, commands and raw records
in [`runs/`](runs/2026-07-29-who-wrote-the-answer.md).

If held-out loss cannot rank the corpora, the obvious fallback is to measure
the corpora directly — length, formatting, entropy — and pick the teacher whose
output looks best. [Which teacher changes what](which-teacher-changes-what/)
runs that measurement across four teachers and finds the fallback is worse than
it looks: the differences it reports at p < 0.005 from one generation per arm
do not survive a second and third generation. Read it before choosing a teacher
on the strength of a sample corpus.

Path two remains unrun here, for the reason
[its requirements page](what-path-two-requires/) gives.

## Check your mental model

Answer each before opening it.

**1. Which question decides whether path two is available to you at all, and why
is it not "which signal is better"?**

<details>
<summary>Answer</summary>

Whether you own the teacher's weights or only have API access. An API emits
text, not logits, so no amount of signal richness matters if you can never
observe the distribution behind it — the constraint is structural, not a
judgment call about which signal is better. "Which signal is better" only
becomes a live question once you already have both options available, and for
most people who only hold API access, that second question never arrives at
all.

</details>

**2. What does a one-hot label destroy that a temperature-softened distribution
keeps, and why does the loss get rescaled by $T^2$?**

<details>
<summary>Answer</summary>

A one-hot label destroys the relative structure among the wrong answers —
that `Lyon` was a plausible near-miss and `banana` was not. It says `Paris`
and nothing else. A temperature-softened distribution keeps that shape: heavy
mass on `Paris`, real but smaller mass on `Lyon`, effectively none on
`banana`, which encodes which mistakes are plausible. The loss is rescaled by
$T^2$ because softening by $T$ shrinks the gradient by roughly $1/T$, so
without the $T^2$ factor a higher temperature would silently produce smaller
updates — the rescaling keeps update magnitude comparable as temperature
changes.

</details>

**3. Raising temperature reveals the teacher's ranking. What does it cost you at
the same time?**

<details>
<summary>Answer</summary>

It teaches the student that absurd continuations are ordinary. The worked
table makes this concrete: at $T{=}1$, `banana` holds 0.24% of the mass, but
at $T{=}4$ it holds 13.16% — more mass than the plausible alternative
(`Lyon`) held at $T{=}1$ (4.73%). Temperature is not a free magnifier of
useful structure; every bit of visibility it buys into the teacher's ranking
of plausible answers, it pays for by inflating the probability the student
assigns to implausible ones.

</details>

**4. Distribution beats text within one teacher, yet a stronger black-box teacher
often beats a weaker local one outright. What control separates those two
claims?**

<details>
<summary>Answer</summary>

Generating targets from a model comparably sized to the student and comparing
against that. Without it, an improvement from a much stronger teacher measures
the teacher's quality, not the distillation method — almost anything a
stronger model supervises will look like progress regardless of whether it
arrived as logits or text. Isolating the method's own contribution requires
holding teacher strength roughly fixed near the student's own scale, which is
the only way to separate "distillation helped" from "we borrowed a bigger
model's competence."

</details>

**5. Every arm in the measured run won on its own author's held-out answers. What
does that make held-out loss unable to decide, and what would you have to
measure instead?**

<details>
<summary>Answer</summary>

It makes held-out loss unable to decide which corpus produces genuinely
better answers — it measures author-matching, not answer quality, since
whichever reference set you choose is won by the arm trained on that same
author's data. Ranking the corpora on quality instead would require an
author-neutral metric: a judge that scores answers without knowing who wrote
them, or a downstream task whose score does not depend on matching one
author's phrasing. This run has neither, which is why it reports two things
it can support (every arm beats the base checkpoint; the 7B teacher's data
transfers better than the 0.5B teacher's, off-diagonal) instead of a ranking
it cannot.

</details>

## Next

Distillation compresses a fixed teacher into a policy the student can run
alone. [Reinforcement learning](../../04-rl/) is the
complementary move: instead of copying a teacher, the policy generates its own
attempts and improves from a reward computed on them. Continue there when the
ceiling is no longer "how much of this teacher can we keep" but "can the policy
beat any teacher we have."

Primary references: Hinton et al. (2015) for the original teacher-student
formulation; DistilBERT; MiniLLM and GKD for on-policy variants; ULD for
cross-tokenizer alignment; and the Gemma 2, Llama 3.2, Minitron and DeepSeek-R1
reports for how the two paths are used in practice.
