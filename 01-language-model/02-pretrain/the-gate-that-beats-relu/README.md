---
status: verified
level: applied
base: scratch
label: The gate that beats ReLU
verified: 2026-08-06
---

# The gate that beats ReLU

**Question:** the 88M decoder's feed-forward block is a SwiGLU — output
equals the gate times the up-projection — and Shazeer's GLU-variants paper
measured the family's edge over plain MLPs. What does the gate mechanism
actually do, and what does the output distribution look like?

**Before this:** [stage 02's decoder block](../), including the
[Mixture-of-experts foundation](../../../foundations/07-moe/) and the
attention anatomy chapters.

## The mechanism, measured

The run ([record](runs/2026-08-06-swiglu-anatomy.md)) draws 200k standard
normal inputs and compares the hidden-unit output under the three
activations:

| activation | mean | std | near-zero |
|---|---:|---:|---:|
| ReLU | 0.397 | 0.582 | 50.1% |
| GELU | 0.280 | 0.587 | 0.2% |
| SwiGLU | -0.001 | 0.594 | 0.9% |

<!-- interactive: SwiGLUActivation -->

## Two readings

**ReLU pays a dead-neuron tax; SwiGLU does not.** Half of ReLU's units sit
at exact zero on standard-normal input — the dead-neuron regime that makes
the plain MLP's gradients vanish on those units. GELU smooths the bend and
removes the dead zone. SwiGLU's output is zero-mean with no dead zone,
because it *multiplies* the gate by a zero-mean up-projection: the
interaction centers the signal instead of squashing it. The gate (SiLU)
passes negatives through a damped, sign-kept transform — not zeroing them
(ReLU), not bending them (GELU) — which is the multiplicative gating the
GLU family is named for.

**The run isolates the mechanism, not learned values.** The gate and
up-projection here are random draws, so the zero-mean, non-dead output is a
property of the SwiGLU *form* — the multiplication — not of trained
weights. The learned gate's job, at inference, is to selectively pass the
up-projection's channels, which is why the block holds more than twice the
parameters of a plain MLP at the same width (the repo's d_ff is ~2/3 x 4 x
d_model, per the config comment).

## Evidence boundary

Random inputs, the repo's activation formulas, no training. It shows the
form's distributional properties; it does not measure the learned gate's
selectivity on real data, and it does not re-derive Shazeer's benchmark
gains (the GLU-variants paper is the attributed external result).

## Check your mental model

Answer each before opening it.

**1. Why is ReLU's 50% dead zone a real cost rather than a curiosity?**

<details>
<summary>Answer</summary>

Because a dead unit's gradient is zero for that input — the unit contributes
nothing to the loss and receives nothing back, so the capacity it occupies
is inert for that example. With half the units dead on typical inputs, the
effective width of the ReLU block is half its nominal width. GELU's smooth
curve and SwiGLU's multiplication both avoid the exact-zero regime, which
is part of why the 88M block uses SwiGLU rather than the older ReLU MLP.

</details>

**2. The SwiGLU output is zero-mean here. Why does that matter downstream?**

<details>
<summary>Answer</summary>

Because the next layer's normalization (RMSNorm) expects a well-centered
input. A zero-mean, fixed-scale hidden distribution means the norm's
statistics are stable across examples and training, whereas ReLU's
positive-shifted output (mean 0.40) biases the norm's input. The
multiplicative form's centered output is a conditioning property, not a
cosmetic one — it is what lets the block's output flow cleanly into the
residual and norm layers after it.

</details>

## Next

Back to [stage 02's decoder](../), or to
[the attention-variants anatomy](../attention-variants/) where the other side
of the block — the KV cache — is priced.
