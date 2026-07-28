---
status: draft
base: scratch
---

# Distillation

**Question:** you can afford to *generate* from a good model but not to
*train* one. What exactly can you copy from it, and what silently fails?

We will follow one question — "What is the capital of France?" — through
three widening views of a teacher model's output:

```text
teacher's chosen words   -> sequence-level distillation
teacher's full distribution -> logit-level distillation
teacher run live during training -> on-the-fly distillation
```

Each view exposes more of what the teacher knows, and each costs more to
obtain than the one before it.

[Post-training's distillation section](../post-training/README.md#6-use-distillation-when-the-teacher-supplies-a-richer-target)
already separated distillation by *whose trajectory is scored* — off-policy on
teacher-generated text, on-policy on the student's own generations. This
chapter asks the orthogonal question: whose *signal* is scored — the
teacher's one chosen token, or the teacher's whole distribution over every
token — and what that signal costs to store and to compare once teacher and
student are different sizes.

## 1. Distill on text alone when the teacher is a black box

If you only have API access to a teacher, you see text, not logits. Sequence-
level distillation generates completions from the teacher and trains the
student on them with ordinary next-token cross-entropy. There is no new
mechanism here: this is plain SFT, in the same chat-JSONL shape [stage 03's
loss masking](../../../missions/01-language-model-agent/03-sft/README.md#loss-masking-worked)
already covers — the only difference is that a model, not a human annotator,
wrote the assistant turn. Everything that lesson says about masking the
prompt, training only the assistant tokens, and imitating style rather than
correctness applies unchanged; the labels' source changed, not the contract.

This is also the fallback whenever logit access disappears — a proprietary
teacher behind an API, or a student that will not share the teacher's
tokenizer (section 4 below).

## 2. Distill on the distribution when you can see it — the wrong answers carry information

A one-hot label says "Paris" and nothing else. Asked the same question, a
teacher model's logits carry a full distribution: heavy mass on Paris, real
but smaller mass on Lyon and Marseille, and effectively none on "banana." That
spread is information — it encodes which mistakes are plausible and which are
absurd — and cross-entropy against a one-hot label throws all of it away. A KL
divergence between the teacher's and student's distributions keeps it.

Temperature controls how much of that structure survives comparison. Both
distributions are softened by the same $T$ before the divergence is taken:

$$
p_i(T) = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}
$$

At $T{=}1$ this is the teacher's raw call. Raising $T$ flattens the
distribution so every wrong answer looks more equally plausible — useful for
*seeing* the shape, useless as a final training target. Softening by $T$ also
shrinks the loss's gradient by roughly $1/T$, so the loss is rescaled by
$T^2$ to keep update magnitude comparable as temperature changes:

$$
L_{\text{KD}} = -T^2 \sum_{i} p_i^{\text{teacher}}(T)\,\log p_i^{\text{student}}(T)
$$

Move temperature below and watch the one-hot label sit still while the
teacher's softened distribution stretches and collapses around it — that gap
is the information sequence-level distillation cannot transmit.

<!-- interactive: DistillationTargets -->

## 3. Price the distribution before you store it

Nobody stores the full 16,512-wide distribution for every token of a training
corpus — most of that vocabulary carries negligible probability. Production
recipes keep only the top-$k$ entries per position:

- `input_ids`: `uint16[N]` — the token stream, already paid for by any SFT run
- `topk_ids`: `uint16[N, k]` — which vocabulary entries were kept
- `topk_logprobs`: `bfloat16[N, k]` — the teacher's log-probability at each

`input_ids` is a cost every fine-tune already carries. What distillation adds
is the other two arrays, two bytes per entry each:

$$
\text{bytes/token (extra)} = k \cdot (\underbrace{2}_{\text{topk\_ids}} + \underbrace{2}_{\text{topk\_logprobs}}) = 4k
$$

At $k{=}16$: $4 \times 16 = 64$ extra bytes per token. At $k{=}8$ that is 32
bytes; at $k{=}64$, 256. Recompute it for whatever $k$ a real run uses — the
formula, not the number, is the fact worth keeping. `uint16` is large enough
for an index here for the same reason [the pretraining token
files](../../../missions/01-language-model-agent/02-pretrain/core/prepare_data.py)
use it: this vocabulary has fewer than 65,536 entries, so a 2-byte index loses
nothing a 4-byte one would have kept.

## 4. Check the tokenizer before you compute a KL divergence

A KL divergence between two vocabularies is meaningless unless the vocabularies
are the *same* vocabulary. Index 4,211 in one tokenizer might be "the" and in
another "ing" — comparing "the probability student assigns to index 4,211"
against "the probability teacher assigns to index 4,211" compares two unrelated
strings and calls the result a divergence. Logit-level distillation therefore
forces a shared tokenizer between teacher and student, which sequence-level
distillation never required — text is text regardless of how either model
happened to encode it internally.

There are three ways out when the teacher and the desired student do not share
one: retrain the student against the teacher's tokenizer before distilling
(expensive, and it discards the student's own token statistics); drop to
sequence-level distillation and accept the smaller transferred signal; or use a
cross-tokenizer method that aligns *sorted* logit distributions — by rank and
magnitude — rather than by index, sidestepping the identity requirement at the
cost of the extra approximation that sorting introduces.

This is also why tokenizer similarity is weak evidence in public disputes over
whether one model distilled another. Tokenizers do not transfer across
training runs by default, and two independently trained tokenizers over
similar corpora can converge on similar merge tables without any logit ever
having crossed between the two models. Shared vocabulary strings prove a
shared corpus family at most — they cannot substitute for a KL trace no one
recorded.

## 5. Decide whether to store the distribution or regenerate it

Storing top-$k$ targets is a bet that training will revisit the same data
enough times to amortize writing it once. If a small teacher and this
student both fit on a 24GB card, that bet is unnecessary: run the teacher's
forward pass live, during the student's training step, and keep nothing on
disk. The on-the-fly path trades the arithmetic in section 3 for compute —
roughly a doubled step cost, one forward pass for the frozen teacher and a
forward-plus-backward pass for the student — and it never goes stale relative
to whatever prompts the student happens to train on, since nothing was
precomputed against a fixed dataset snapshot.

Which side of that trade wins is a question about disk, epochs, and card
memory, not about the mechanism — the loss in section 2 is identical either
way; only where `topk_ids` and `topk_logprobs` come from changes.

## 6. Bound what a distillation gain is allowed to mean

If the teacher is far stronger than the student, an improvement after
distillation measures the *teacher's* quality, not the distillation method —
almost anything a much stronger model supervises will look like progress. The
control that isolates the method is generating targets with a model
comparably sized to the student, not the strong one, and comparing against
that instead. Without it, "distillation helped" and "we borrowed a bigger
model's competence" are indistinguishable claims wearing the same number.

## Run the working path

`core/distill.py` runs top-$k$ logit distillation with a live teacher forward
pass end to end: it builds [the 88,197,888-parameter student](../../../missions/01-language-model-agent/02-pretrain/core/model.py)
from mission 01's pretraining stage, a larger stand-in teacher of the same
architecture family and vocabulary, and trains the student against the
teacher's top-$k$ log-probabilities at a chosen temperature — plus a small
utility that writes an example shard in the section 3 format and checks its
byte size against the stated formula. `prod/distill_prod.py` runs the same
on-the-fly job through TRL's `GKDTrainer` on two real, same-tokenizer public
checkpoints.

Both scripts can be executed today. Neither has run on real hardware yet —
there is no teacher checkpoint worth distilling from in this repository, so
the teacher in `core/` is randomly initialized and the loss it produces is not
a quality claim about anything. Running either script establishes that the
mechanism executes: top-$k$ extraction, temperature scaling, the storage
arithmetic, and a live teacher forward pass during a student's training step.
It establishes nothing about response quality, and this chapter stays
`status: draft` until a `runs/` entry exists with a real teacher, a command,
hardware, and metrics.

## Check your mental model

1. Why does sequence-level distillation need no new loss function beyond SFT's?
2. What does a one-hot label destroy that a temperature-softened teacher
   distribution keeps, and why does the loss get rescaled by $T^2$?
3. At $k{=}32$, how many extra bytes per token does the top-$k$ format cost,
   and which of the three arrays did not change?
4. Why does logit-level distillation require a shared tokenizer when
   sequence-level distillation does not?
5. What does a distillation gain against a much stronger teacher fail to
   prove, and what control isolates the method from the teacher's quality?

## Next

Distillation compresses a fixed teacher's knowledge into a policy the student
can run alone. [Reinforcement learning](../reinforcement-learning/) is the
complementary move: instead of copying a teacher's distribution, the policy
generates its own attempts and improves from a reward computed on them.
Continue there when the ceiling is not "how much of this teacher can we keep"
but "can the policy get better than any teacher we have."

Primary references: Hinton et al. (2015) on the original teacher-student
formulation, DistilBERT, MiniLLM, GKD, and cross-tokenizer alignment methods
such as ULD (Universal Logit Distillation).
