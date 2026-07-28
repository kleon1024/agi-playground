---
status: verified
verified: 2026-07-28
base: scratch
label: Upcycling
---

# Can you keep the weights and change the architecture?

**Question:** five hours of a 24GB card produced an 88M-parameter checkpoint.
You now want a different feed-forward design. Do you have to start over?

You need one thing from
[pretraining](../../../missions/01-language-model-agent/02-pretrain/): that a
decoder is an embedding table, a stack of blocks, and a tied output head, and
that its weights are just named tensors in a file. This chapter changes the
shape of one component in that stack while keeping every trained tensor, and
measures whether the result is still the same model.

## What a checkpoint actually is, and what "compatible" means

A checkpoint is a dictionary from tensor names to numbers. Loading one into a
different class is only sensible when each tensor still *means* the same thing
on the other side. Row 4,102 of the embedding table means "the token the
tokenizer assigns id 4,102", and the attention output matrix means "a map from
768 concatenated head outputs back into the residual stream".

That gives a precise precondition, and it is narrower than "similar
architecture":

> The tokenizer is unchanged, so every embedding row still denotes the same
> token, and `d_model` is unchanged, so every tensor that reads or writes the
> residual stream still has something to read or write.

Change the tokenizer and row 4,102 denotes a different string; the embedding
table is now a table of wrong answers. Change `d_model` and the tensors do not
even have compatible shapes. Everything in this chapter lives inside that
precondition, and the interesting part is how much freedom is left once you
respect it — quite a lot, as it turns out.

## The surgery: one feed-forward becomes four experts

The change is to the feed-forward block. The dense model has one; the
mixture-of-experts variant from
[architecture ablations](../02-architecture-ablations/) has four routed
experts and picks two per token. Attention, norms, and embeddings are untouched.

`core/upcycle.py` maps the parent's tensors into the new layout:

| Tensor | What happens |
|---|---|
| embedding, tied head, every norm, every attention matrix | copied verbatim |
| `mlp.{gate,up,down}` | copied into **every** routed expert, identically |
| router | random, small |
| shared expert `down` (when present) | zero |

Nothing is averaged, interpolated, or resized. A tensor whose meaning would
have to change is not copied at all — the router has no parent tensor, so it is
invented, and it is the only thing that is.

## Why replication makes the new model start at the old model's loss

Copying one feed-forward into four identical experts looks wasteful. It is what
makes the whole thing checkable.

Top-k routing renormalises its weights to sum to one. So if every expert
computes the same function `F`, the block computes `w1*F(x) + w2*F(x) = F(x)`
for *any* weights the router happens to produce. The routing is irrelevant to
the output at step 0. The 258M-parameter model is, arithmetically, the 88M
model.

That converts a hope into a test. Stage 02 checked its untrained model against
`ln(vocab_size)`, the loss of a model that knows nothing. This chapter has the
mirror-image check: **the upcycled model must start at its parent's validation
loss, not at that floor.** On the 4090:

```
max |logit difference| dense vs upcycled: 1.261e-04
validation loss over 20 batches of 8x1024 tokens
  parent   3.0498
  upcycled 3.0499
  untrained floor would be ln(16512) = 9.7118
```

A 258M model scored 3.0499 having done no training. The remaining 0.0001 is
floating-point accumulation order — two weighted expert outputs summed where
the dense path summed one — not a difference in the function.

The number that gives the test its power is 9.7118. A transposed attention
matrix, an expert wired to the wrong layer, or a shared expert quietly adding a
second copy of the feed-forward would all land somewhere between 3.05 and 9.71.
Recovering the parent's loss to four decimals is a far stronger statement than
"it loaded without an exception".

Two details follow from the same arithmetic and both look like bugs:

- **The router is random, not zero.** Zero would leave every expert equally
  likely forever. Random breaks the symmetry, so from step 1 each expert sees a
  different subset of tokens, receives a different gradient, and the four copies
  diverge into four different functions. That divergence is the entire point;
  without it you have paid 2.93x the storage for nothing.
- **The router's own gradient is exactly zero at step 0.** Identical experts
  make the output independent of the routing weights, so nothing flows back.
  It becomes non-zero one step later, as soon as the experts differ.

<!-- interactive: UpcycleSurgery -->

## What it costs, in the two units that disagree

The upcycled model has 258,104,064 total parameters and 144,838,656 active per
token: **2.93x the storage, 1.64x the compute.** Both are reported because a
later quality claim means something different under each, exactly as
[architecture ablations](../02-architecture-ablations/) argues.

Measured wall-clock is worse than either number suggests. Continuing to train
the upcycled model ran at **16.6k tokens per second**, against the 161k the
dense parent reached during pretraining. That is roughly ten times slower for
1.64x the arithmetic. The gap is not the architecture — it is that `core/`
dispatches experts with a Python loop rather than a grouped kernel, the same
distinction [serving](../../../missions/01-language-model-agent/05-serve/why-concurrency-pays/)
had to draw between a scheduling policy and a fused kernel.

## The thing that surprised the first run

Continuing to train the upcycled model made it *worse* before it made it
better. Over the first 4M tokens at `lr=1e-4`, validation loss went 3.0847 →
3.1178 → 3.1044.

This is not the surgery failing. The parent finished a cosine schedule at
nearly zero learning rate, sitting in a minimum. Raising the rate to 1e-4 kicks
it back out, and the model has to re-descend before it can make progress the
old one could not. Any continued-training comparison shorter than that recovery
is measuring the disruption, not the architecture — which is why the run below
is budgeted at 2e8 tokens and not at the four minutes it took to see this.

## Reproduce it

```bash
cd platform/training/05-upcycling/core
python upcycle.py convert ckpt.pt moe.pt --experts 4 --active 2
python upcycle.py verify moe.pt --parent ckpt.pt --data ~/tokens
python continue_training.py --arm moe --checkpoint moe.pt --data ~/tokens --tokens 2e8
```

[`prod/upcycle_hf.py`](prod/upcycle_hf.py) performs the identical remap on a
real `safetensors` checkpoint, which shows that none of this needs a custom
model class — only a correct reading of what each tensor means.

## What this chapter establishes and what it does not

Established, and recorded in
[`runs/`](runs/2026-07-28-upcycle-88m.md): the surgery preserves the function
exactly, under a stated precondition, with a test that would have caught the
mistakes.

Not established: **that the upcycled model is better.** The honest comparison is
not against an untrained model but against spending the same GPU-hours
continuing to train the parent, because that is the alternative actually
available. `core/continue_training.py` runs both arms on identical batches in
identical order; the result is not yet in `runs/` and no claim is made here
until it is. Also untested: whether 4 experts at top-2 is a good shape — it was
chosen to make the identity check clean, not because it was tuned.

## Check your mental model

1. The precondition is a shared tokenizer and a shared `d_model`. Which one
   breaks the embedding table, and which one breaks the attention matrices?
2. Why does replicating one feed-forward into four identical experts produce
   *exactly* the parent's output, rather than approximately?
3. The untrained floor is 9.7118 and the parent scores 3.0498. What would you
   conclude from an upcycled loss of 4.2, and what from a loss of 3.0501?
4. The router's gradient is zero at step 0. Why does that not make the router
   permanently untrainable?
5. Storage went up 2.93x and compute 1.64x, but throughput fell about tenfold.
   Which of those three numbers is a property of the architecture?

## Next

What this chapter hands back to
[stage 02 of the language-model system](../../../missions/01-language-model-agent/02-pretrain/)
is a decision that stage cannot otherwise make: once the checkpoint exists,
changing the architecture is no longer all-or-nothing, and the precondition for
keeping the weights is a shared tokenizer and a shared `d_model` rather than a
similar-looking design.

[Architecture ablations](../02-architecture-ablations/) trains the same MoE
shape from scratch, which is the control this chapter's continued-training run
needs. [The throughput ladder](../03-throughput/) is where the expert-dispatch
gap above turns into a number you can attribute to a kernel.
