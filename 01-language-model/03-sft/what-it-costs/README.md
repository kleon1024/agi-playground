---
status: draft
level: applied
base: scratch
label: What it costs
---

# It answers questions now. What did that cost?

[The previous chapter](../) took the 88M base model and, in 92.5 seconds over
9,500 conversations, turned a text continuer into something that answers. The
chat template and the loss mask are the whole mechanism, and both are cheap.

The costs are elsewhere, and none of them is visible in the loss curve that
went from 3.1829 to 2.7828. This chapter covers three: what packing quietly
gives up to be fast, why the learning rate has to drop roughly thirtyfold, and
the class of problem fine-tuning cannot touch no matter how good the data is.

You need the loss mask and the template from the previous chapter. You leave
able to say which complaints about a fine-tuned model are fixable with better
data and which are not.

## Packing is fast because it stops isolating conversations

A curated instruct set is short and length-variable: `no_robots` averages a few
hundred tokens per example against a 1024-token block. Padding each example out
to the block size spends most of a batch's forward pass on tokens carrying no
signal.

Packing concatenates several short examples back-to-back, closing a block only
once the next example no longer fits, so a large majority of positions hold a
real token from some conversation. The speedup is most of why this stage
finishes in ninety seconds.

The cost is a correctness subtlety. **Once two unrelated conversations share a
sequence, a plain causal mask lets late tokens in conversation B attend to all
of conversation A.** Production trainers fix this with a block-diagonal
attention mask, giving each packed example causal attention only within itself;
TRL and torchtune both do.

`core/sft.py` does not. It reuses stage 02's `Attention.forward` unmodified,
which always calls `scaled_dot_product_attention(..., is_causal=True)` over the
whole sequence, and building a custom mask would mean editing a file this stage
is scoped not to touch. So the leak is disclosed rather than hidden.

Its blast radius is worth being precise about, because it is smaller than it
sounds: **loss masking depends only on `labels`, never on attention.** The model
is never taught to predict a token from the wrong conversation. It occasionally
spends a little attention capacity on an irrelevant neighbor.
[`prod/trl_sft.py`](../prod/trl_sft.py) runs the identical recipe through
`SFTConfig(packing=True)`, which does not have this limitation, and says so in
its header.

## The learning rate drops thirtyfold, and not for stability

Stage 02 pretrained from a random initialization, where a large learning rate
is safe because there is nothing yet to disturb. SFT starts from a model that
already computes something useful, and the fine-tuning objective can easily
out-compete it.

A peak learning rate anywhere near pretraining's `6e-4`, applied to a converged
model, does not adjust it — **it re-randomizes large parts of it** before the
objective has any chance to specialize gently. `core/sft.py` defaults to `2e-5`,
roughly thirty times lower, for exactly that reason, with a 30-step warmup
against pretraining's 500 because there are far fewer total steps to warm up
across.

The same reasoning decides the epoch structure. With roughly 10,000 examples
rather than billions of tokens, running once would barely move the model, so
SFT runs a handful of epochs over a small set. Running many epochs at a
pretraining-scale learning rate is precisely how you get catastrophic
forgetting — which presents as fluent, grammatical, well-formatted text that
has lost whatever the base model previously knew. It looks like success until
you ask it something.

## Four things better data will not fix

Easy to lose sight of once a model starts producing chat-shaped output:

- **No new knowledge.** If it was not in the pretraining corpus, formatting the
  question as a chat turn does not put it there.
- **No ground truth.** SFT imitates the *style* of its examples, not their
  correctness. A confidently-worded wrong answer in the training set teaches
  the model to be confidently wrong, and does it efficiently.
- **No preference signal.** SFT has one response per prompt to imitate and no
  way to express "this reply is better than that one." That comparison is what
  [stage 04](../../04-rl/) exists for.
- **No capacity.** A small model given excellent data still has a small model's
  capacity. Zhou et al. (2023)'s ~1,000-example LIMA result — the Superficial
  Alignment Hypothesis, that pretraining holds almost all the knowledge and SFT
  mostly teaches format and style — is an argument for curation over volume,
  **not** evidence that curation substitutes for scale.

That last distinction is the one most often misread. LIMA says you need less
data than you thought. It does not say you need less model.

## Does a stronger base need fewer examples? LIMA doesn't test that

LIMA's own numbers are narrower than the folklore that's grown up around them.
Zhou et al. fine-tuned a single 65B base on 1,000 curated examples and found
that **doubling that training set did not improve response quality** — more
data aimed at the same target distribution hit diminishing returns fast.
Separately, adding a modest number of examples aimed at a genuinely new
distribution (multi-turn dialogue, which the original 1,000 barely covered)
raised the rate of "excellent" responses from 45.2% to 76.1%. Read together:
volume stops helping once it's answering a question the model already knows
how to answer; volume helps again when it's teaching something the curated set
never covered.

None of that is a claim about *base-model scale*. LIMA ran one 65B model —
there is no second, weaker or stronger base in the paper to compare it against,
so the study cannot show whether a stronger base needs fewer SFT examples than
a weaker one. The idea that it would is a reasonable **inference** from the
Superficial Alignment Hypothesis, not something LIMA measured: if pretraining
is where the knowledge and most of the capability come from, and SFT's job is
mainly to select a format and a response distribution out of what's already
there, then a base model that arrives with a sharper distribution should need
less correction to reach the same target. That's a chain of reasoning from the
hypothesis, stated here as inference, and it stays unmeasured until someone
runs the same curated set across bases of different capability and reports
what changes.

This repo's own run is a curation-over-volume illustration at a much smaller
scale, not a test of that scaling question either. The 9,500-conversation
`no_robots` corpus packs into 3,305 blocks of 1,025 tokens at 80.4% real
tokens (see [stage 03's run record](../runs/)), and three epochs over it
measurably changed the 88M-parameter base's output shape in 92.5 seconds. That
shows curated data working at this repo's scale — it says nothing about
whether a larger base pretrained on more data would need a smaller version of
that same 9,500-example set to reach an equivalent result. Testing that would
mean training multiple bases of different capability against matched SFT data
and comparing how much each needs, which is a cross-base-model comparison this
repo has no way to run.

## What the recorded run does and does not show

The 92.5-second run and its 2.7828 validation loss are measured, in
[stage 03's run record](../runs/). Nothing on this page is: the attention leak
is a property of the code that was read, not an effect that was quantified, and
no ablation was run at a higher learning rate to observe forgetting directly.
Both are stated as mechanisms with named consequences, not as results.

## Measure the packing win yourself

Before calling `pack()`, compute what padding every example individually to
`block_size` would cost in wasted positions, then compare that against
`pack()`'s actual fill rate on the same data. The gap is a property of your
data's length distribution, not a constant — the 19.6% recorded here belongs to
no_robots at a 1,024-token block and to nothing else. Confirm it for yourself
rather than trusting a quoted number, which is the same discipline every other
figure in this repository is held to.

## Check your mental model

1. Packing lets conversation B attend to conversation A. Why does that not
   corrupt the training signal, and what exactly does it cost instead?

<details>
<summary>Answer</summary>

The training signal is the loss mask, and the loss mask depends only on
`labels` — never on attention. The model is never taught to *predict* a
token from the wrong conversation, because the loss simply never asks it to
predict those positions at all. What it costs instead is attention capacity:
a late token in conversation B can attend to conversation A's irrelevant
tokens, spending some of its representational budget on a neighbor that has
nothing to do with the answer it's forming. It's wasted computation, not a
corrupted target.

</details>

2. The learning rate drops thirtyfold going from pretraining to SFT. Is that
   about numerical stability, and if not, what is it about?

<details>
<summary>Answer</summary>

Not stability — the pretraining rate (`6e-4`) was already numerically stable
for training the same architecture from scratch. The real reason is what the
optimizer step lands on: pretraining starts from random weights where there
is nothing yet to disturb, so a large step is safe. SFT starts from a
converged model that already computes something useful, and a step that size
applied to it doesn't gently adjust that knowledge — it re-randomizes large
parts of it before the new objective has any chance to specialize. The
thirtyfold drop to `2e-5` is protecting the pretrained knowledge from being
overwritten, not protecting the training loop from diverging numerically.

</details>

3. A fine-tuned model gives a fluent, confident, wrong answer. Which of the
   four limits above is responsible, and how would you tell it apart from the
   others?

<details>
<summary>Answer</summary>

Most likely "no ground truth" — SFT imitates the style of its training
examples, not their correctness, so a confidently-worded wrong answer in the
training set teaches the model to be confidently wrong just as efficiently as
a correct one would teach it to be confidently right. You'd tell it apart
from "no new knowledge" by checking whether the correct answer was ever in
the pretraining corpus at all: if it was, and the model still gets it wrong
confidently, the training data's own correctness is the more likely culprit,
not a gap in what the base model ever saw.

</details>

4. LIMA trained on about 1,000 examples. What does that license you to reduce,
   and what does it not?

<details>
<summary>Answer</summary>

It licenses reducing data *volume* — the Superficial Alignment Hypothesis
argues pretraining already holds almost all the knowledge, so SFT needs only
enough curated examples to teach format and style, not thousands more. It
does not license reducing model *capacity*. That's the distinction the
chapter calls "the one most often misread": LIMA says you need less data than
you thought, not that curation substitutes for scale — a small model given
LIMA-quality data still has a small model's capacity, and no amount of data
curation changes that.

</details>

5. Catastrophic forgetting produces text that reads well. What would you
   measure to detect it, given that loss on the fine-tuning set will look fine?

<details>
<summary>Answer</summary>

Since forgetting presents as fluent, grammatical output that has quietly lost
knowledge the base model previously had, the fine-tuning set's own loss
curve can't reveal it — that loss only measures fit to the new objective, not
retention of the old one. You'd need to probe the model on facts or
capabilities it demonstrably had *before* SFT (something checkable against
the base checkpoint) and compare, rather than trusting that a low, well-
behaved SFT loss means nothing was lost — exactly the ablation this page
states was not run here: no higher-learning-rate run was done to observe
forgetting directly, so this is a named mechanism with a stated consequence,
not a measured result.

</details>

## Next

Return to [stage 03](../) for the before-and-after behaviour, then
[stage 04](../../04-rl/) addresses the third limit on this page directly: it is
the stage that can express a preference between two responses, which is exactly
what supervised fine-tuning has no way to say.
