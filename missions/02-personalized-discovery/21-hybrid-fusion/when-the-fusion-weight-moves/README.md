---
status: verified
level: applied
base: scratch
label: When the fusion weight moves
verified: 2026-08-07
---

# The fusion weight is a trust decision

**Question:** [stage 21's hybrid fusion](../) combines lexical and
dense scores. This chapter reads the executed weight sweep and asks
what the fusion weight actually decides.

**Before this:** [stage 21 — hybrid fusion](../) and its executed
reciprocal-rank-fusion model.

## The sweep, executed

The run ([record](runs/2026-08-07-fusion-weight-read.md)) varies the
weight w in score = w·lex + (1−w)·dense:

| weight | winner | score |
|---|---:|---:|
| 0.0 | d2 | 0.90 |
| 0.5 | d1 | 0.65 |
| 1.0 | d1 | 0.90 |

## The reading

At w=0 the dense-only winner (d2, 0.90) takes the top slot; at w=1 the
lexical-only winner (d1, 0.90) does; at w=0.5 the blend edges to d1 by
0.05. The weight is the product decision: how much the platform trusts
meaning versus exact terms. It is not a tuning constant to be
minimized — it is the platform stating which retrieval failure it
trusts less, and the sweep is how that statement changes the result.

## Evidence boundary

The executed sweep over three hand-built score pairs (illustrative,
deterministic). It demonstrates the decision surface; real fusion
weights are set against measured downstream quality per query class,
not against the fused list alone.

## Check your mental model

Answer each before opening it.

**1. Why is the weight a product decision rather than a tuning knob?**

<details>
<summary>Answer</summary>

Because it encodes which failure the platform tolerates. Leaning lexical
trusts exact terms and accepts vocabulary misses; leaning dense trusts
meaning and accepts exactness misses. Neither is "right" — the weight
states the product's judgment about which error costs more, which is a
decision about what search is for.

</details>

**2. What does the 0.5 case add to the reading?**

<details>
<summary>Answer</summary>

It shows the blend is not a compromise that satisfies both — at w=0.5
the winner is d1 by a narrow 0.05 margin, because the blend's ranking
is a new order neither matcher produced alone. The intermediate weight
is where the platform's trust is genuinely split, and the winner there
is the answer the blend commits to.

</details>

## Next

Back to [stage 21](../), which fuses the two sets. The
[empty-set detour](../when-one-set-is-empty/) shows the failure side:
the hybrid degrades silently when one matcher returns nothing.
