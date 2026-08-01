---
status: draft
level: foundation
label: The decoder block
---

# How does one token find the context it needs?

And transform it, and still leave a stable path for learning through dozens of
layers?

Come here if `Q`, `K`, `V`, residual streams, or normalization still feel like
names to memorize. We will follow one token through one decoder block:

```text
token
  -> query, key, value
  -> causal attention
  -> residual update
  -> normalization
  -> gated feed-forward update
  -> logits
```

**Before this:** nothing. This chapter explains the forward path. The
[first training loop](../01-first-training-loop/) supplies the backward path,
and [pretraining](../../platform/training/) later joins both to real data.

Every formula below is followed by its value in **the 88M model this repository
actually trained** — 12 layers, 12 query heads, 4 key-value heads, `d_model` 768,
`d_head` 64, `d_ff` 2048, 16,512 vocabulary entries, 1,024-token context. No
formula here is left symbolic; each one is evaluated on a real configuration so
you can see what it is worth. [What a block costs](what-it-costs/) then
reconstructs the model's exact parameter count and cache size from those same
formulas.

## 1. Begin with a retrieval question

Suppose the current token is `it` in:

```text
the cat sat on the mat because it ...
```

The model needs information from earlier positions, but it cannot perform a
dictionary lookup for `it`. Each token instead projects into three roles:

- a **query**: what information this position needs;
- a **key**: what each earlier position advertises;
- a **value**: what each earlier position contributes if selected.

The query-key dot product measures compatibility. Softmax turns all compatible
scores into weights, and the weighted values become the retrieved message:

$$
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}+M\right)V
$$

**Worked, at $d_k=64$:** the scale factor is $1/\sqrt{64} = 0.125$, and $QK^\top$
is a $1024 \times 1024$ matrix — 1,048,576 scores for one head, one layer, one
sequence. Across 12 heads and 12 layers that is 150,994,944 scores computed to
predict one batch of tokens. Attention is cheap per score and expensive in
aggregate, and that aggregate is what
[what a block costs](what-it-costs/) prices.

That equation contains two failure-prevention mechanisms. We will isolate them
before adding anything else.

## 2. Keep softmax in a learnable range

A dot product of two unit-variance vectors sums $d_k$ terms, so its variance
grows with $d_k$ — and a saturated softmax hands the winning position almost
all the probability, leaving the others with almost no gradient.

**Worked, at $d_k=64$:** unscaled scores have standard deviation $\sqrt{64}=8$,
so a typical spread of three deviations runs from $-24$ to $+24$. Softmax
compares $e^{24}$ against $e^{-24}$ — a ratio of about $7 \times 10^{20}$, which
is one-hot for every practical purpose, and one-hot means no gradient reaches
the positions that lost. Divide by $\sqrt{64}$ and the standard deviation
becomes 1, the spread becomes $-3$ to $+3$, and the ratio falls to
$e^{6} \approx 403$. Sharp enough to select, soft enough to learn.

Before continuing, predict what happens as `d_k` grows with scaling disabled.
Then test the prediction below.

<!-- interactive: SoftmaxScaling -->

Division by $\sqrt{d_k}$ is therefore not a convention. It holds score variance
constant as head width changes, which is what keeps the retrieval distribution
trainable at all.

## 3. Prevent the model from reading the answer

Language modeling predicts the next token. During training the full sequence
is present, so unrestricted attention could read future positions and produce
an artificially low loss. The causal mask sets every future score to
$-\infty$ before softmax.

Move the query position in the next view. For any selected row, only the
current and earlier columns may receive weight.

<!-- interactive: AttentionPattern -->

Now the weighted values form a legal message: relevant past context, with no
future leakage. This message is the first update written to the residual
stream.

## 4. Let different heads ask different questions

One head owns one similarity function, and syntax, local continuity, entity
reference and long-range structure should not all compete in the same score
space. So the model splits `d_model` across several heads, each running the
same retrieval mechanism in a different learned subspace, then concatenates
their outputs and projects back to `d_model`.

The split is not free. Every generated token needs cached keys and values for
every layer, so grouped-query attention keeps many query heads while sharing
fewer key-value heads.

Twelve query heads either way, but a third of the cache — the trade is priced
in [what a block costs](what-it-costs/), along with everything else this
chapter builds.

## 5. Make position affect compatibility

Without positional information, swapping two earlier tokens leaves the
attention calculation unchanged. Rotary position embeddings solve this by
rotating query and key pairs by a position-dependent angle before the dot
product:

$$
q'_m=q_m e^{im\theta}, \qquad k'_n=k_n e^{in\theta}
$$

Their compatibility depends on the rotation difference:

$$
q'_m{k'_n}^{\top}\propto e^{i(m-n)\theta}
$$

Relative distance is therefore exposed directly, rather than as an absolute
position vector the model must later reinterpret.

**Worked:** each dimension pair $i$ gets its own frequency,
$\theta_i = 10000^{-2i/d_{\text{head}}}$. With $d_{\text{head}}=64$ there are 32
pairs, and the two ends of that range behave completely differently:

| pair | $\theta$ (radians/position) | one full rotation takes |
|---|---|---|
| $i=0$, fastest | 1.0 | ~6.3 positions |
| $i=31$, slowest | $1.33 \times 10^{-4}$ | ~47,000 positions |

Over the model's entire 1,024-token context the slowest pair turns through only
0.136 radians — about 8 degrees. It cannot distinguish adjacent tokens at all,
and that is the point: it is the dimension that still carries signal at
distance 900, when the fastest pair has wrapped around 145 times and is
useless.

The important boundary is also clear: RoPE makes positions *computable* beyond
the training length, but it does not prove the model learned to use those
distances. Context extension still needs data and evaluation.

## 6. Preserve a path that gradients can follow

Attention produces a message, not a replacement for the token state. A
pre-norm decoder writes:

```text
x = x + Attention(Norm(x))
x = x + FFN(Norm(x))
```

The identity term in each `x +` gives information and gradients a direct path
through depth. Post-norm instead places normalization after the addition, so
every backward path must cross a normalization Jacobian. That difference is
minor in a shallow network and load-bearing in a deep one.

RMSNorm keeps the property needed here: rescale a vector by its root mean
square so its magnitude is controlled.

$$
\operatorname{RMSNorm}(x)
=
\gamma\frac{x}{\sqrt{\frac{1}{d}\sum_i x_i^2+\epsilon}}
$$

**Worked:** the only learned part is $\gamma$, one scale per dimension — 768
numbers. Two norms per block across 12 blocks, plus one before the output
projection, is $25 \times 768 = 19{,}200$ parameters: **0.02% of the model**.
It drops mean subtraction because stable rescaling, not recentering, is the
essential contribution, and the whole mechanism is close to free.

## 7. Transform the retrieved message

Attention moves information between positions. The feed-forward network
changes the representation at each position independently. In a modern
decoder, SwiGLU uses one projection as a gate over another:

$$
\operatorname{FFN}(x)
=
W_{\text{down}}
\left[
\operatorname{SiLU}(W_{\text{gate}}x)\odot W_{\text{up}}x
\right]
$$

**Worked:** three matrices, each $768 \times 2048$, is $3 \times 768 \times 2048
= 4{,}718{,}592$ parameters per block — and that single number turns out to
settle where the model keeps everything it knows.
[What a block costs](what-it-costs/) does the accounting.

After the second residual addition, the block's output can enter the next
block or the vocabulary projection. That is the whole forward path.

## Build the block in this order

1. Run [the first training loop](../01-first-training-loop/) to see a complete
   forward, loss, backward, and update cycle on a small model.
2. Implement scaled dot-product attention and compare it with a naive numeric
   reference.
3. Add the causal mask, multi-head split, grouped-query sharing, and RoPE.
4. Assemble RMSNorm, attention, residual, SwiGLU, and the second residual into
   one decoder block.
5. Stack blocks and project to vocabulary logits.

Do not start by copying a complete transformer class. Each step should preserve
the behavior established by the previous step.

## Check your mental model

You are ready to move on when you can answer these without reciting a library
API:

**1. Why does score scaling depend on head width rather than model width?**

<details>
<summary>Answer</summary>

Because the variance blow-up comes from the dot product summing $d_k$
terms — the width of one head's own subspace, not the model's full width.
Each head computes its own independent $QK^\top$ over only its own
`d_head` dimensions, so the correction has to normalize per-head. Dividing
by $\sqrt{d_{\text{model}}}$ instead would over- or under-correct depending
on how many heads that width is split across.

</details>

**2. Which operation prevents training-time future leakage?**

<details>
<summary>Answer</summary>

The causal mask — setting every future position's score to $-\infty$ before
softmax, so after softmax those positions receive exactly zero weight no
matter what their value is. Without it, the full sequence is visible during
training and the model could read the answer it's supposed to be predicting.

</details>

**3. Why can grouped-query attention reduce serving memory without reducing
   the number of query heads?**

<details>
<summary>Answer</summary>

Because query heads and key-value heads pay for different things: query
heads determine retrieval expressiveness (how many independent similarity
functions the model can compute), while KV heads determine how much state
must be cached and read back per generated token. Sharing fewer KV heads
across many query heads keeps all 12 query heads' retrieval power intact
while only storing and reading 4 heads' worth of keys and values — shrinking
the cache to a third of plain multi-head attention without touching how many
distinct queries the model can ask.

</details>

**4. What path remains when an attention or FFN sublayer initially
   contributes almost nothing?**

<details>
<summary>Answer</summary>

The residual identity path — `x = x + sublayer(...)`. Even when the
sublayer's output starts near zero, `x` still passes through unchanged, so
information and gradients keep flowing through depth while that sublayer is
still learning to contribute anything. That's the whole point of writing the
update as an addition rather than a replacement.

</details>

**5. Which part of a block retrieves context, and which part transforms it?**

<details>
<summary>Answer</summary>

Attention retrieves context — it moves information between positions via the
query-key-value mechanism. The feed-forward network (SwiGLU) transforms the
representation at each position independently afterward, changing what's
there rather than fetching it from anywhere else. Retrieval and
transformation are two separate jobs, done by two separate sublayers.

</details>

## Evidence boundary and next step

This chapter explains a decoder block; it does not establish that a model
learned language. That requires a corpus, an optimization budget, and a run.

Continue to [what a block costs](what-it-costs/) to price everything above and
find out where a transformer really keeps what it knows. Then to
[data](../../platform/data/) to construct the input distribution, or to
[pretraining](../../platform/training/) if you already have a clean shard.

Primary references, in the order the mechanism actually accumulated:
Vaswani et al., "Attention Is All You Need" (2017) introduces the scaled
dot-product form this chapter opens with; Zhang and Sennrich, "Root Mean
Square Layer Normalization" (2019) is the RMSNorm this chapter uses in place
of the original paper's LayerNorm; Shazeer, "GLU Variants Improve Transformer"
(2020) proposes the gated feed-forward this chapter uses instead of a plain
ReLU MLP; Su et al., "RoFormer" (2021) introduces RoPE; Dao et al.,
"FlashAttention" (2022) makes the exact softmax-attention computation above
IO-aware rather than changing what it computes; and Ainslie et al., "GQA"
(2023) is the grouped-query-attention scheme this chapter's 12-query/4-key-
value-head split follows. Six years separate the first paper from the last,
and every mechanism named here still appears, unmodified in substance, in the
block this chapter builds by hand.

Every mechanism above has a production implementation that computes the same
thing faster. [The foundations landscape](../LANDSCAPE.md) pairs them off, so
you know which of these files you would keep and which you would delete the
moment the model has to be fast.
