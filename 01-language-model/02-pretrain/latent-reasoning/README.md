---
status: verified
level: frontier
base: scratch
label: Latent reasoning
verified: 2026-07-30
---

# What if the model could think without choosing words?

**Question:** a chain of thought works because each step is written down and
read back. But writing a step forces the model to collapse a whole distribution
over what it might be thinking into one token. Is that collapse doing useful
work, or is it a tax the vocabulary charges?

You need one thing from [pretraining](../):
that a decoder maps token ids to vectors, transforms those vectors, and turns
the last one back into a distribution over tokens. This chapter changes exactly
one link in that loop and measures what happens.

**Before this:** [the decoder block](../../../foundations/00-attention/) and the
[RL stage](../../04-rl/). This
is an open question at the edge of both, not a mechanism either one settles.

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

Switch the arm below to see which boxes the state still has to pass through,
and what arrives at the next step in each case.

<!-- interactive: LatentThoughtCycle -->

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

## What a real run actually shows

The hypothesis below was written before any run, so it could not be adjusted
to match whatever came out:

- `cot` beats `direct`, because the task is built to require sequential steps
  and a single forward pass has a fixed depth to do them in.
- `latent` lands **between** them, and at this scale plausibly inside the seed
  spread. A thought at `d_model=128` carries more than a token in principle,
  and the curriculum has few stages and little capacity to learn how to use it.

The defaults above at full budget (6000 steps for `direct`/`cot`, five
1500-step curriculum stages for `latent`, 3 seeds each) first ran CPU-only,
where `direct` alone took 16-17 minutes per seed and the full sweep never
finished in one sitting — a partial `direct`-only result converged to **0.502
mean accuracy**, chance. The same command then ran to completion on an RTX
4090 (19.4 minutes total, all three arms, \$0, local lane):

```
direct   mean 0.502  spread 0.012   -- chance, matches the CPU-only result exactly
cot      mean 0.9993 spread 0.002   -- effectively solves the task
latent   mean 0.502  spread 0.012   -- chance, indistinguishable from direct
```

Half the hypothesis lands cleanly: `cot` crushes `direct`. `latent` does not
land between them — it lands on top of `direct`, and the curriculum log says
why. Each seed's per-stage accuracy climbs through the early stages and hits
**1.0 at the `n_latent=3` stage**, then collapses back to **0.5 at
`n_latent=4`** — the final stage, at the task's actual reasoning depth (4
hops) — with loss settling at 0.345-0.353, the same number `direct` converges
to. The model can clearly use three latent thoughts; going to four is where
training throws that away rather than extending it. That is a specific,
reportable failure mode, not "latent reasoning doesn't work" in general: a
longer curriculum, a smaller step per stage, or a wider latent channel are
the next things to vary, not run here. [Full GPU run, with the curriculum
log and the earlier CPU-only partial result.](runs/2026-07-30-arm-comparison-gpu.md)

Beyond that, this chapter will not establish anything about a model that has to
reason in natural language. The task is synthetic, the vocabulary is 51 tokens,
and both are chosen so the baseline works — which is exactly what makes the
comparison meaningful and exactly what stops it generalising.

## Reproduce it

```bash
cd 01-language-model/02-pretrain/latent-reasoning/core
python task.py                                     # inspect the generated data
python model.py                                    # parameter count, no training
python train.py --arms direct cot latent --seeds 3 --out result.json
```

[`prod/hf_latent.py`](prod/hf_latent.py) runs the identical loop against a real
`transformers` checkpoint through its `inputs_embeds` interface, which
demonstrates that nothing here needs a custom model — only custom training.

## Check your mental model

Answer each before opening it.

**1. A hidden state is hundreds of continuous numbers and a token is one choice
out of thousands. What exactly is lost at each step of a written chain of
thought, and why might that loss be useful rather than wasteful?**

<details>
<summary>Answer</summary>

Everything the model was considering and didn't pick is destroyed the moment
a hidden state collapses into one sampled token — 768 continuous numbers
reduced to a single choice out of 16,512, with nothing recoverable at the
next step. That loss could still be useful, not merely wasteful, because
forcing a decision at each step is also what makes the reasoning legible and
auditable: `cot`'s written chain can be read, checked, and scored on its own,
and the curriculum in this chapter only works *because* early stages can
supervise against those written tokens. The chapter's actual result is
consistent with the collapse mattering less at shallow depth (three latent
thoughts trained fine) and more at the task's full depth (four thoughts
collapsed to chance) — so the tax is real, but this run doesn't establish
that it's *always* wasteful, only that this curriculum couldn't pay it past
three steps.

</details>

**2. Unreachable questions are built from a decoy chain of the same length. What
would a model learn to do if they were built by picking a random entity
instead?**

<details>
<summary>Answer</summary>

It would learn a shortcut that has nothing to do with reasoning: entities
reachable from the source tend to appear "close" to it in whatever the model
picks up on from the input structure, so a randomly-picked unreachable target
would often be trivially distinguishable by depth or position alone, without
tracing the path at all. By instead building the decoy from a chain of the
*same length*, both the reachable and unreachable targets are equally deep
and equally present in the input — the only way to tell them apart is to
actually walk the graph. This is what makes the task test reasoning rather
than pattern-matching on superficial position.

</details>

**3. The written chain is identical for `yes` and `no` answers. Why is that
necessary for the token-chain arm to be a fair baseline?**

<details>
<summary>Answer</summary>

If the written chain differed systematically between `yes` and `no` cases —
say, reachable chains looking structurally different from unreachable ones —
then writing the chain would leak information about the label itself, and
`cot`'s advantage over `direct` could just be "the model learned to recognize
the shape of a `yes`-chain" rather than "writing intermediate steps helps
reasoning." Making the written walk identical in form for both answers means
the chain conveys the same kind of information regardless of the true label,
so any accuracy gain from writing it has to come from the reasoning process
itself, not from a hidden shortcut in how the chain was constructed.

</details>

**4. Why can a latent thought not be supervised directly, and what does the
curriculum substitute for that missing supervision?**

<details>
<summary>Answer</summary>

A latent thought has no token, so there's nothing to score it against
directly — at initialization, a thought is whatever the untrained network
happens to emit, and its only gradient signal arrives indirectly, through the
final answer several positions later. The curriculum substitutes a staged
transition: stage 0 writes every reasoning step as tokens (identical to the
`cot` arm, fully supervised), and each later stage replaces one more written
step with a latent thought while the rest remain visible as tokens. This lets
the model learn what a thought needs to carry while it can still see the
token it is replacing, rather than trying to learn that from the sparse,
delayed answer-only signal alone.

</details>

**5. Latent thoughts emit fewer tokens and cost more forward passes. Under what
serving conditions would that still be the better trade?**

<details>
<summary>Answer</summary>

When output length, not forward-pass count, is the binding cost — for
example, if a serving system is billed or bounded by tokens generated (context
window pressure, per-token API cost, or a strict output-length budget) rather
than by wall-clock compute, then fewer emitted tokens can be worth extra
forward passes even though each thought depends on the one before it and so
cannot be parallelized, and even though overwriting a sequence slot
invalidates the KV cache from that point forward. This chapter's own numbers
don't establish that such conditions exist in practice for this method — it
only establishes the trade's shape (cheap in tokens, expensive in passes),
leaving the "when is that actually the better trade" question open.

</details>

## Next

This chapter hands nothing back to a mission stage yet, and that is the honest
statement of its position: it is an open question kept beside the curriculum
rather than a decision any mission currently makes. It becomes a detour worth
taking only if the run below produces a separation.

Meanwhile, [architecture ablations](../architecture-ablations/) is where a
result like this one gets its budget definition, and
[the throughput ladder](../throughput/) is where the extra forward passes
this method needs turn into wall-clock you can measure.
