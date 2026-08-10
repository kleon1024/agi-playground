---
status: verified
level: frontier
base: scratch
label: What path two requires
---

# What does it take to actually run distribution distillation?

Two things, and one of them will probably stop you. You need somewhere to put
the teacher's distribution, and you need the student to speak the teacher's
vocabulary. The first is a bill. The second is a wall.

**Before this:** [what you can copy from a better model](../README.md), through
the temperature section. You need to know why a softened distribution carries
more than a one-hot label before it is worth pricing.

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

**Worked, at $k{=}16$:** 64 extra bytes per token. The 3.0B-token corpus this
repository pretrained on would therefore carry **192 GB** of teacher
distribution beside it, against 6 GB for the token stream itself — thirty-two
times the storage of the thing being annotated. Recompute it for whatever $k$ a
real run uses; the formula is the fact worth keeping, not the number.

Whether to store those arrays or regenerate them is a question about disk and
epochs, not about mechanism. If teacher and student both fit on one 24GB card,
run the teacher's forward pass live during the student's training step and keep
nothing: roughly a doubled step cost, and it never goes stale against a fixed
dataset snapshot. The loss is identical either way. Storage buys you the right
to reuse the annotation across many student runs; live inference buys you the
right to change the corpus tomorrow.

## The constraint that ends path two

A KL divergence between two vocabularies is meaningless unless they are the
*same* vocabulary. Index 4,211 might be `the` in one tokenizer and `ing` in
another; comparing the probability each model assigns to index 4,211 compares
two unrelated strings and calls the result a divergence.

This is not a detail — it is why the language-model system's student cannot
take path two at all. Its tokenizer was trained from scratch in
[stage 01](../../../01-tokenizer/), 16,512
entries, shared with no public model in existence. Any teacher you could reach
speaks a different vocabulary.

Three ways out, none free:

| Escape | What it costs |
|---|---|
| Retrain the student against the teacher's tokenizer | expensive, and it discards the student's own token statistics |
| Drop to path one | the whole distribution, which was the point |
| Cross-tokenizer alignment by rank and magnitude | the approximation that sorting introduces |

## Why this makes tokenizer similarity weak evidence

The same constraint settles a recurring public argument. When one model is
accused of having distilled another because their tokenizers look alike, the
inference does not hold. Tokenizers do not transfer across training runs by
default, and two independently trained tokenizers over similar corpora can
converge on similar merge tables without a single logit ever having crossed
between the models.

Shared vocabulary strings prove a shared corpus family at most. They cannot
substitute for a KL trace nobody recorded — and by the argument above, a
shared tokenizer is a *precondition* for distribution distillation, not
evidence that it happened.

## The fix and its trade

The fix is the two questions the chapter opens with, answered before any
training: where does the teacher's distribution live, and does the student
speak the teacher's vocabulary. For the first, the top-k format is the
production answer — 4k extra bytes per token (64 at top-16), with the
storage-versus-live trade named: storing buys reuse across many student
runs and goes stale with the dataset snapshot; live inference buys the
right to change the corpus tomorrow and costs roughly a doubled step every
run. The second question is the wall, and the trade is that all three
escapes are expensive: retraining the student against the teacher's
tokenizer discards the student's own token statistics, path one gives up
the distribution that was the point, and cross-tokenizer
rank-and-magnitude alignment keeps an approximation in place of a
divergence.

The third trade is in the evidence the format gives you. The 192 GB figure
is arithmetic over a declared format, not a measurement, and the tokenizer
constraint is an argument about what a divergence means — which is exactly
why the chapter's boundary says nothing here was run. That matters when the
same constraint is used as evidence in a public argument: two models with
similar merge tables prove a shared corpus family at most, because a shared
tokenizer is a precondition for distribution distillation, not evidence
that it happened — the KL trace nobody recorded cannot be substituted by
vocabulary similarity.

## Who owns the loop

- **The training-infrastructure team** owns the storage decision: the top-k
  format, the byte budget (192 GB at top-16 on a 3.0B-token corpus,
  thirty-two times the token stream), and the choice between stored
  annotation and a live teacher forward pass.
- **The model team** owns the path decision: whether the student may
  retrain its tokenizer, fall back to path one, or accept a
  rank-and-magnitude approximation — the constraint is structural, and the
  choice is made before training, not after a failed run.
- **The research and eval teams** own the inference boundary: a shared
  tokenizer is weak evidence of distillation, so an accusation or a
  capability claim rests on a recorded KL trace, and the absence of one is
  reported as such, not filled by vocabulary similarity.

## Check your mental model

Answer each before opening it.

**1. At $k{=}32$, how many extra bytes per token does the top-$k$ format cost,
and which of the three arrays did not change?**

<details>
<summary>Answer</summary>

$4k = 4 \times 32 = 128$ extra bytes per token. `input_ids` did not change —
it stays `uint16[N]`, the plain token stream already paid for by any
fine-tune regardless of $k$. Only `topk_ids` and `topk_logprobs` scale with
$k$; the token stream itself is independent of how many distribution entries
you decide to keep per position.

</details>

**2. When is storing the teacher's distribution worth more than recomputing it
live, and what does each choice buy you?**

<details>
<summary>Answer</summary>

Storing is worth it when the annotation will be reused across many student
runs against a fixed dataset snapshot — you pay the storage cost (192 GB at
$k{=}16$ on this repository's corpus) once and amortize it. Recomputing live
is worth it when teacher and student both fit on the same card and the corpus
might change — it costs roughly a doubled step cost on every run, but it
never goes stale, so you can change the corpus tomorrow without re-annotating
anything. Storage buys reuse; live inference buys the freedom to change the
data.

</details>

**3. Why is comparing two models' probabilities at index 4,211 meaningless
across tokenizers?**

<details>
<summary>Answer</summary>

Because the same index denotes different strings in different tokenizers —
index 4,211 might mean `the` in one vocabulary and `ing` in another. A KL
divergence between the two models' probabilities at that index is not
comparing two models' beliefs about the same token; it is comparing each
model's belief about a different string and calling the result a divergence
anyway. The comparison only means something when both models share the exact
same vocabulary, so the same index is guaranteed to denote the same string in
both.

</details>

**4. Two models share a suspiciously similar merge table. What does that
establish, and what would you need instead?**

<details>
<summary>Answer</summary>

At most, a shared corpus family — two independently trained tokenizers over
similar corpora can converge on similar merge tables without any logit ever
crossing between the models, since tokenizers do not transfer across training
runs by default. It does not establish that distribution distillation
happened. What you would need instead is a recorded KL trace — direct
evidence that one model's distribution was actually used as a training
target for the other — because a shared tokenizer is a *precondition* for
that kind of distillation, not evidence that it occurred.

</details>

## Evidence boundary and next step

Nothing on this page was run. The byte counts are arithmetic over a declared
format, and the tokenizer constraint is an argument about what a divergence
means, not a measurement. `core/distill.py` implements top-$k$ distillation
with a live teacher forward pass and `prod/distill_prod.py` runs the same job
through TRL's `GKDTrainer`, but the teacher in `core/` is randomly initialised,
so its loss is a mechanism demonstration and not a quality claim.

Return to [what a distillation gain is allowed to mean](../README.md#what-a-distillation-gain-is-allowed-to-mean),
which is the part of the parent chapter that was actually measured.
