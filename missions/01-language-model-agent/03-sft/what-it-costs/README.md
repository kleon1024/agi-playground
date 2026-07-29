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
2. The learning rate drops thirtyfold going from pretraining to SFT. Is that
   about numerical stability, and if not, what is it about?
3. A fine-tuned model gives a fluent, confident, wrong answer. Which of the
   four limits above is responsible, and how would you tell it apart from the
   others?
4. LIMA trained on about 1,000 examples. What does that license you to reduce,
   and what does it not?
5. Catastrophic forgetting produces text that reads well. What would you
   measure to detect it, given that loss on the fine-tuning set will look fine?

## Next

Return to [stage 03](../) for the before-and-after behaviour, then
[stage 04](../../04-rl/) addresses the third limit on this page directly: it is
the stage that can express a preference between two responses, which is exactly
what supervised fine-tuning has no way to say.
