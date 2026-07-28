---
status: draft
base: scratch
label: Latent reasoning
---

# What if the model could think without choosing words?

**Question:** a chain of thought works because each step is written down and
read back. But writing a step forces the model to collapse a whole distribution
over what it might be thinking into one token. Is that collapse doing useful
work, or is it a tax the vocabulary charges?

You need one thing from [pretraining](../../../missions/01-language-model-agent/02-pretrain/):
that a decoder maps token ids to vectors, transforms those vectors, and turns
the last one back into a distribution over tokens. This chapter changes exactly
one link in that loop and measures what happens.

## The loop, and the one link this chapter cuts

Generating a chain of thought is a cycle. The model produces a hidden state, the
head turns it into logits, sampling picks a token, and the embedding table turns
that token back into a vector for the next step. Round and round, once per word.

Look at what that cycle does to information. The hidden state is 768 continuous
numbers. The token is one choice out of 16,512. Everything the model was
considering and did not pick is destroyed at that step and cannot be recovered
at the next one.

A **continuous thought** removes two links from the cycle. Instead of
`hidden -> logits -> token -> embedding`, it does `hidden -> embedding`,
directly:

```python
hidden, _ = model(embeds)             # run the network
embeds[:, slot] = hidden[:, slot - 1]  # the state becomes the next input
```

That is the entire mechanism. Same weights, same attention, same objective. The
model still takes a sequence of vectors and still predicts a next token at the
end. Some of the vectors in the middle were simply never words.

## A task where the answer can mean something

Testing this on a general small language model would answer nothing. A model
that cannot reason in tokens either would show no difference, and "no
difference" would be indistinguishable between "latent thoughts do not help"
and "there was no reasoning here to move".

So `core/task.py` generates a task where the token-chain baseline genuinely
works: reachability in a small directed graph, the same shape as the ProsQA
benchmark the continuous-thought paper used, shrunk until a six-layer model
trains on it in minutes.

```
<edges> e11>e27 e2>e3 e13>e14 e34>e18 ... <q> e11 ? e23 <cot> e11>e27 e27>e4 e4>e24 e24>e23 <a> yes
```

Three properties make it a reasoning task rather than a lookup. The edge list is
shuffled, so the path is never contiguous. Half the questions are unreachable,
and an unreachable one is built from a *decoy chain of the same length*, so both
entities are equally present and equally deep in the input. And the written
chain is the walk out from the source, identical for both answers — so writing
it leaks nothing about the label, and the token-chain arm is a fair baseline
rather than a hint.

## Three arms, differing only in what sits between question and answer

| Arm | Between `<q>` and `<a>` | Scored on |
|---|---|---|
| `direct` | nothing | the answer token |
| `cot` | the walk, as tokens | the answer token |
| `latent` | the walk, as hidden states | the answer token |

Every arm is scored the same way, on the same held-out problems: the model's
score for `yes` against its score for `no` at the position after `<a>`. A
difference between arms is a difference in reasoning, not in how generously the
output was read.

## Why the curriculum is part of the method

Training the latent arm from scratch does not work, and it is worth
understanding why before treating that as a detail. At initialization a thought
is whatever the untrained network happens to emit. There is no supervision on it
— nothing says what a thought should contain, because it has no token to be
scored against. Its only gradient arrives through the answer several positions
later.

The fix is a curriculum, and `core/train.py` implements it as a single sweeping
parameter. Stage 0 writes every reasoning step as tokens, which is *exactly* the
`cot` arm. Stage 1 replaces the first step with one thought and leaves the rest
written. Stage 2 replaces two. By the last stage nothing is written. The model
learns what a thought must carry while it can still see the tokens that thought
is replacing.

## What a thought costs

Each thought depends on the one before it, so they cannot be computed in
parallel: a training step with `n` thoughts is `n + 1` forward passes.

Worse, this does not compose with a KV cache during training. *Appending* a
computed embedding is fine — the prefix is unchanged and the cache stays valid.
*Overwriting* a slot inside the sequence invalidates every cached key and value
after it. Latent thoughts are cheap in tokens and expensive in passes, which is
the opposite trade from the one the name suggests.

## What this chapter does not yet establish

**No run has been recorded.** The three arms are implemented and each trains end
to end, but this lesson stays `draft` until `runs/` contains a measured
comparison across seeds. The hypothesis is stated here in advance, so it cannot
be adjusted afterwards to match whatever comes out:

- `cot` beats `direct`, because the task is built to require sequential steps
  and a single forward pass has a fixed depth to do them in.
- `latent` lands **between** them, and at this scale plausibly inside the seed
  spread. A thought at `d_model=128` carries more than a token in principle,
  and the curriculum has few stages and little capacity to learn how to use it.

A result inside the seed spread is a reportable result here, not a failed
experiment. The instrument that makes that claim legitimate is three seeds per
arm and the spread reported beside every mean.

Beyond that, this chapter will not establish anything about a model that has to
reason in natural language. The task is synthetic, the vocabulary is 51 tokens,
and both are chosen so the baseline works — which is exactly what makes the
comparison meaningful and exactly what stops it generalising.

## Reproduce it

```bash
cd platform/training/04-latent-reasoning/core
python task.py                                     # inspect the generated data
python model.py                                    # parameter count, no training
python train.py --arms direct cot latent --seeds 3 --out result.json
```

[`prod/hf_latent.py`](prod/hf_latent.py) runs the identical loop against a real
`transformers` checkpoint through its `inputs_embeds` interface, which
demonstrates that nothing here needs a custom model — only custom training.

## Check your mental model

1. A hidden state is hundreds of continuous numbers and a token is one choice
   out of thousands. What exactly is lost at each step of a written chain of
   thought, and why might that loss be useful rather than wasteful?
2. Unreachable questions are built from a decoy chain of the same length. What
   would a model learn to do if they were built by picking a random entity
   instead?
3. The written chain is identical for `yes` and `no` answers. Why is that
   necessary for the token-chain arm to be a fair baseline?
4. Why can a latent thought not be supervised directly, and what does the
   curriculum substitute for that missing supervision?
5. Latent thoughts emit fewer tokens and cost more forward passes. Under what
   serving conditions would that still be the better trade?

## Next

[Architecture ablations](../02-architecture-ablations/) is where a result like
this one gets its budget definition, and
[the throughput ladder](../03-throughput/) is where the extra forward passes
this method needs turn into wall-clock you can measure.
