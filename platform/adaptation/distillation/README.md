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

[Stage 03 of the language-model system](../../../missions/01-language-model-agent/03-sft/)
arrives here when the question becomes where its supervision should come from.
Take back the target format and the tokenizer constraint; both decide what the
stage can and cannot buy.

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

So read the table, find your row, and the rest of this chapter tells you what
that row costs.

## Path one: copy the words

If you see text and not logits, you generate completions from the teacher and
train the student on them with ordinary next-token cross-entropy. There is no
new mechanism: this is the chat-JSONL shape and the loss masking that
[stage 03](../../../missions/01-language-model-agent/03-sft/README.md#loss-masking-worked)
already covers. Mask the prompt, train the assistant tokens, imitate style
rather than correctness. The only thing that changed is who wrote the assistant
turn.

This is also the fallback whenever a shared tokenizer is unavailable, which is
the constraint that ends path two before it starts — see below.

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
nothing. Softening also shrinks the gradient by roughly $1/T$, so the loss
carries a $T^2$ factor to keep update magnitudes comparable across
temperatures:

$$
L_{\text{KD}} = -T^2 \sum_{i} p_i^{\text{teacher}}(T)\,\log p_i^{\text{student}}(T)
$$

Move temperature below and watch the one-hot label sit still while the
teacher's softened distribution stretches and collapses around it. That gap is
what path one cannot transmit.

<!-- interactive: DistillationTargets -->

## What the distribution costs to keep

Nobody stores a full 16,512-wide distribution for every token of a corpus —
most of that vocabulary carries negligible probability. Production recipes keep
the top-$k$ entries per position:

- `input_ids`: `uint16[N]` — the token stream, already paid for by any fine-tune
- `topk_ids`: `uint16[N, k]` — which vocabulary entries were kept
- `topk_logprobs`: `bfloat16[N, k]` — the teacher's log-probability at each

Only the last two are new, at two bytes per entry:

$$
\text{bytes/token (extra)} = k \cdot (\underbrace{2}_{\text{topk\_ids}} + \underbrace{2}_{\text{topk\_logprobs}}) = 4k
$$

At $k{=}16$ that is 64 extra bytes per token. Recompute it for whatever $k$ a
real run uses — the formula is the fact worth keeping, not the number.

Whether to store those arrays or regenerate them is a question about disk and
epochs, not about mechanism. If teacher and student both fit on one 24GB card,
run the teacher's forward pass live during the student's training step and keep
nothing: roughly a doubled step cost, and it never goes stale against a fixed
dataset snapshot. The loss is identical either way.

## The constraint that ends path two

A KL divergence between two vocabularies is meaningless unless they are the
*same* vocabulary. Index 4,211 might be `the` in one tokenizer and `ing` in
another; comparing the probability each model assigns to index 4,211 compares
two unrelated strings and calls the result a divergence.

This is not a detail — it is why mission 01's student cannot take path two at
all. Its tokenizer was trained from scratch in
[stage 01](../../../missions/01-language-model-agent/01-tokenizer/), 16,512
entries, shared with no public model in existence. Any teacher you could reach
speaks a different vocabulary.

Three ways out, none free: retrain the student against the teacher's tokenizer
first (expensive, and it discards the student's own token statistics); drop to
path one; or use a cross-tokenizer method that aligns *sorted* distributions by
rank and magnitude rather than by index, paying for it with the approximation
that sorting introduces.

It is also why tokenizer similarity is weak evidence in public disputes over
whether one model distilled another. Tokenizers do not transfer across training
runs by default, and two independently trained tokenizers over similar corpora
can converge on similar merge tables without a single logit ever having crossed
between the models. Shared vocabulary strings prove a shared corpus family at
most; they cannot substitute for a KL trace nobody recorded.

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

Path two remains unrun here: `core/distill.py` performs top-$k$ logit
distillation with a live teacher forward pass, and `prod/distill_prod.py` runs
the same job through TRL's `GKDTrainer`, but the teacher in `core/` is randomly
initialised, so its loss is not a quality claim about anything.

## Check your mental model

1. Which question decides whether path two is available to you at all, and why
   is it not "which signal is better"?
2. What does a one-hot label destroy that a temperature-softened distribution
   keeps, and why does the loss get rescaled by $T^2$?
3. At $k{=}32$, how many extra bytes per token does the top-$k$ format cost,
   and which of the three arrays did not change?
4. Mission 01's student has a 16,512-entry tokenizer trained from scratch.
   Which path is closed to it, and what are the three escapes?
5. Distribution beats text within one teacher, yet a stronger black-box teacher
   often beats a weaker local one outright. What control separates those two
   claims?
6. Every arm in the measured run won on its own author's held-out answers. What
   does that make held-out loss unable to decide, and what would you have to
   measure instead?

## Next

Distillation compresses a fixed teacher into a policy the student can run
alone. [Reinforcement learning](../reinforcement-learning/) is the
complementary move: instead of copying a teacher, the policy generates its own
attempts and improves from a reward computed on them. Continue there when the
ceiling is no longer "how much of this teacher can we keep" but "can the policy
beat any teacher we have."

Primary references: Hinton et al. (2015) for the original teacher-student
formulation; DistilBERT; MiniLLM and GKD for on-policy variants; ULD for
cross-tokenizer alignment; and the Gemma 2, Llama 3.2, Minitron and DeepSeek-R1
reports for how the two paths are used in practice.
