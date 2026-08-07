---
status: verified
level: frontier
verified: 2026-07-28
base: scratch
label: Upcycling
---

# Can you keep the weights and change the architecture?

**Question:** five hours of a 24GB card produced an 88M-parameter checkpoint.
You now want a different feed-forward design. Do you have to start over?

You need one thing from
[pretraining](../): that a
decoder is an embedding table, a stack of blocks, and a tied output head, and
that its weights are just named tensors in a file. This chapter changes the
shape of one component in that stack while keeping every trained tensor, and
measures whether the result is still the same model.

**Before this:** [architecture ablations](../architecture-ablations/) for what
a mixture-of-experts block is and which budget it should be judged under. This
chapter converts one; that chapter decides whether it is worth converting.

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

The change is to the feed-forward block. The dense model has one; this chapter
reuses the mixture-of-experts block from
[architecture ablations](../architecture-ablations/) and configures it with
four routed experts, picking two per token. Attention, norms, and embeddings
are untouched.

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
[architecture ablations](../architecture-ablations/) argues.

Measured wall-clock is worse than either number suggests. Over 200M tokens the
upcycled model sustained **55,069 tokens per second** against the dense model's
**106,369** on the same data in the same script: 1.93x slower for 1.64x the
arithmetic. The gap is not the architecture — it is that `core/` dispatches
experts with a Python loop rather than a grouped kernel, the same distinction
[serving](../../05-serve/why-concurrency-pays/)
had to draw between a scheduling policy and a fused kernel.

## Does the extra capacity pay for itself?

Only if you keep training, and the run that answers it begins by getting worse.
Raising the learning rate to continue lifts *both* arms' loss for the first 53M
tokens before either recovers, which is why the comparison is run as a pair
rather than against the parent's remembered number.

[Does it pay off?](does-it-pay-off/) has that pair: the upcycled arm behind at
32.8M tokens, crossing over, and ending 0.0088 nats ahead at 200M with the gap
still widening — plus the reason an experiment stopped at 30M tokens would have
reported the opposite with a straight face, and the wall-clock budget under
which the ranking reopens.

## Reproduce it

```bash
cd 01-language-model/02-pretrain/upcycling/core
python upcycle.py convert ckpt.pt moe.pt --experts 4 --active 2
python upcycle.py verify moe.pt --parent ckpt.pt --data ~/tokens
python continue_training.py --arm moe --checkpoint moe.pt --data ~/tokens --tokens 2e8
```

[`prod/upcycle_hf.py`](prod/upcycle_hf.py) performs the identical remap on a
real `safetensors` checkpoint, which shows that none of this needs a custom
model class — only a correct reading of what each tensor means.

## What this chapter establishes and what it does not

Established, and recorded in [`runs/`](runs/2026-07-28-upcycle-88m.md): the
surgery preserves the function exactly, under a stated precondition, with a
test that would have caught the mistakes.

Not established here: **that the converted model is better than the one it came
from.** Conversion is free and exact; whether the capacity earns its cost is a
separate run with its own boundary, in
[does it pay off?](does-it-pay-off/).

## Check your mental model

Answer each before opening it.

**1. The precondition is a shared tokenizer and a shared `d_model`. Which one
breaks the embedding table, and which one breaks the attention matrices?**

<details>
<summary>Answer</summary>

Changing the tokenizer breaks the embedding table: row 4,102 only means "the
token the tokenizer assigns id 4,102" as long as that assignment stays fixed
— swap tokenizers and the same row now denotes a different string, turning
the table into a table of wrong answers, even though its shape is unchanged.
Changing `d_model` breaks the attention matrices (and every other tensor that
reads or writes the residual stream): those tensors' shapes are defined in
terms of `d_model`, so a different width makes them incompatible outright,
not just semantically wrong — they wouldn't even multiply.

</details>

**2. Why does replicating one feed-forward into four identical experts produce
*exactly* the parent's output, rather than approximately?**

<details>
<summary>Answer</summary>

Because top-k routing renormalizes its weights to sum to one, and if every
expert computes the same function `F`, the weighted combination
`w1*F(x) + w2*F(x) + ...` always equals `F(x)` regardless of what the router's
weights actually are — the routing becomes mathematically irrelevant to the
output when all routed experts are identical copies. This isn't an
approximation that happens to be close; it's an algebraic identity, which is
exactly why the chapter can test for it to four decimal places (3.0498 vs
3.0499) rather than merely checking that the output looks "similar."

</details>

**3. The untrained floor is 9.7118 and the parent scores 3.0498. What would you
conclude from an upcycled loss of 4.2, and what from a loss of 3.0501?**

<details>
<summary>Answer</summary>

A loss of 4.2 — between the parent's 3.0498 and the untrained floor of
9.7118 — would mean the surgery is wrong somewhere: a transposed attention
matrix, an expert wired to the wrong layer, or a shared expert quietly
double-counting the feed-forward would all land in that middle range, because
the conversion preserved the parent's function only partially. A loss of
3.0501, essentially identical to the parent's 3.0498 within floating-point
noise, is exactly what a correct conversion should produce — the tiny 0.0001
remaining gap is attributable to accumulation-order differences (summing two
weighted expert outputs instead of one path), not to a difference in what the
model computes.

</details>

**4. The router's gradient is zero at step 0. Why does that not make the router
permanently untrainable?**

<details>
<summary>Answer</summary>

The router's gradient is zero at step 0 specifically because all four experts
are still identical at that point — the output doesn't depend on which expert
gets more routing weight when every expert computes the same function, so
there's nothing for the router's gradient to respond to yet. But the router
itself is initialized randomly (not zero), which breaks the symmetry between
experts from the very first step: each expert starts seeing a slightly
different subset of tokens and receives a slightly different gradient, so by
step 1 the four experts have already begun to diverge into different
functions. Once they differ even slightly, routing between them does affect
the output, and the router's gradient becomes non-zero from that point on.

</details>

**5. Storage went up 2.93x and compute 1.64x, but sustained throughput fell only
1.93x. Which of those numbers is a property of the architecture, and which
of the kernel?**

<details>
<summary>Answer</summary>

Storage (2.93x) and active-parameter compute (1.64x) are properties of the
architecture itself — they follow directly from having four experts instead
of one feed-forward, with two active per token, independent of how the
experts are executed. The measured 1.93x throughput slowdown is a property of
the kernel, not the architecture: it doesn't match either architectural
number because `core/` dispatches experts with a Python loop rather than a
fused, grouped kernel. The same architecture run through a proper grouped
kernel would be expected to land closer to the 1.64x compute ratio — the gap
between 1.64x and 1.93x is implementation overhead, the same
scheduling-policy-vs-fused-kernel distinction the serving chapter draws
elsewhere in this curriculum.

</details>

## Next

What this chapter hands back to
[stage 02 of the language-model system](../)
is a decision that stage cannot otherwise make: once the checkpoint exists,
changing the architecture is no longer all-or-nothing, and the precondition for
keeping the weights is a shared tokenizer and a shared `d_model` rather than a
similar-looking design.

[Architecture ablations](../architecture-ablations/) trains that same block
from scratch against a dense control, and reports the result this chapter
cannot: at 33M parameters, matched on active parameters, the mixture wins by
0.0901 nats — and matched on total parameters, it does not win at all.
[The throughput ladder](../throughput/) is where the expert-dispatch gap
above turns into a number you can attribute to a kernel.
