---
status: draft
level: foundation
---

> **[Read this online](https://rehearse.maestro.onl/playground/foundations)**.

# How does one token find the context it needs?

And transform it, and still leave a stable path for learning through dozens of
layers?

These are **language-model foundations**, not prerequisites for intelligence in
general. Attention, decoder blocks, and a first training loop are what you need
to reason about the next decision in
[the language-model system](../missions/01-language-model-agent/) — nothing
here claims to be the base of a broader pyramid, and nothing here has to be
read before you start a mission.

Come here if `Q`, `K`, `V`, residual streams, or normalization still feel
like names to memorize. We will follow one token through one decoder block.
At the end, the block will no longer be a black box:

```text
token
  -> query, key, value
  -> causal attention
  -> residual update
  -> normalization
  -> gated feed-forward update
  -> logits
```

This chapter explains the forward path. The
[first training loop](01-first-training-loop/) supplies the backward path,
and [pretraining](../platform/training/) later joins both to real data.

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

That equation contains two failure-prevention mechanisms. We will isolate them
before adding anything else.

## 2. Keep softmax in a learnable range

If entries of a query and key have unit variance, their dot product sums
$d_k$ terms and has variance proportional to $d_k$. At $d_k=64$, unscaled
scores are already large enough to make softmax nearly one-hot. A saturated
softmax gives the winning position almost all probability and leaves the
others with almost no gradient.

Before continuing, predict what happens as `d_k` grows with scaling disabled.
Then test the prediction below.

<!-- interactive: SoftmaxScaling -->

The result to carry forward is precise: division by $\sqrt{d_k}$ is not a
convention. It keeps score variance roughly constant as head width changes, so
the retrieval distribution remains trainable.

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

One head owns one similarity function. Syntax, local continuity, entity
reference, and long-range structure should not all compete in the same score
space, so the model splits `d_model` across several heads. Each head performs
the same retrieval mechanism in a different learned subspace; their outputs
are concatenated and projected back to `d_model`.

The split does not make attention free. At inference time, every generated
token needs cached keys and values for every layer. Grouped-query attention
keeps many query heads but shares fewer key-value heads, trading a small amount
of flexibility for a smaller serving cache. This is an architecture decision
whose cost appears later in [serving](../platform/serving/).

Carry forward this distinction:

```text
more query heads -> more retrieval patterns
more KV heads    -> more cache memory
```

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

The mechanism therefore exposes relative distance directly. It does not add
an absolute position vector that the model must later reinterpret. Different
dimension pairs rotate at different frequencies, giving the score both local
and coarse distance information.

The important boundary is also clear: RoPE makes positions computable beyond
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

It drops mean subtraction because stable rescaling, not recentering, is the
essential contribution for this architecture.

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

This stage owns most of a block's parameters. Reading attention as the whole
model misses the division of labor:

```text
attention -> choose and combine context
FFN       -> transform the combined representation
residual  -> preserve and accumulate both updates
```

After the second residual addition, the block's output can enter the next
block or the vocabulary projection.

## 8. Identify the first scaling wall

The attention score matrix has shape `sequence x sequence`. Doubling context
therefore quadruples score computation and the naive intermediate storage.
FlashAttention does not change the mathematical result or the quadratic
arithmetic. It tiles the operation so the full matrix is not repeatedly
written to slower memory.

This is the first example of a pattern used throughout the curriculum:
preserve the invariant, change the system boundary. The invariant is exact
attention; the changed boundary is where intermediate state lives.

## Build the block in this order

1. Run [the first training loop](01-first-training-loop/) to see a complete
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

1. Why does score scaling depend on head width rather than model width?
2. Which operation prevents training-time future leakage?
3. Why can grouped-query attention reduce serving memory without reducing the
   number of query heads?
4. What path remains when an attention or FFN sublayer initially contributes
   almost nothing?
5. Which part of a block retrieves context, and which part transforms it?

## Evidence boundary and next step

This chapter explains a decoder block; it does not establish that a model
learned language. That requires a corpus, an optimization budget, and a run.
Continue to [data](../platform/data/) to construct the input distribution, or
to [pretraining](../platform/training/) if you already have a clean shard.

Primary references: Vaswani et al. (attention), Su et al. (RoPE), Zhang and
Sennrich (RMSNorm), Shazeer (GLU variants), Dao et al. (FlashAttention), and
Ainslie et al. (grouped-query attention).
