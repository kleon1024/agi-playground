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

## The fix and its trade

The failure this chapter prices is the dead-neuron tax: on 200k standard
normal inputs, 50.1% of ReLU's hidden units sit at exact zero — a dead
unit's gradient is zero for that input, so it contributes nothing to the
loss and receives nothing back, and the effective width of the block is
half its nominal width. The fix is the SwiGLU form itself: the gate (SiLU)
passes negatives through a damped, sign-kept transform and the block
*multiplies* gate times up-projection, which centers the output (mean
-0.001 vs ReLU's 0.397, no dead zone at 0.9% vs 50.1%) — and the zero-mean
output is a conditioning property, not a cosmetic one, because the next
layer's RMSNorm expects a well-centered input and ReLU's positive-shifted
distribution (mean 0.40) biases the norm's statistics.

The trade is stated in the same table that shows the fix working. The run
isolates the mechanism, not learned values — the gate and up-projection are
random draws, so the zero-mean, non-dead output is a property of the
multiplicative *form*, not of trained weights, which means the chapter can
claim the form's distributional properties and nothing about the learned
gate's selectivity on real data. And the form is not free: the block holds
more than twice the parameters of a plain MLP at the same width (this
repo's d_ff is about 2/3 x 4 x d_model), so the fix trades parameter count
for a centered, non-dead activation — the same budget-definition question
the architecture ladder makes explicit, where equal-parameter comparisons
flatter whatever spends more compute per stored parameter. The benchmark
edge over plain MLPs is attributed to Shazeer's GLU-variants paper (2020),
not re-derived here.

## Who owns the loop

- **The architecture team** owns the block form: choosing SwiGLU over a
  ReLU MLP is a parameter-budget decision (2x the parameters at the same
  width) made in exchange for a zero-mean, non-dead activation, and the
  form's property is what this chapter's measured table licenses them to
  claim.
- **The training team** owns the conditioning consequence: the zero-mean,
  fixed-scale hidden distribution is what keeps the following RMSNorm's
  statistics stable across examples and training, and a norm-shifted
  activation (ReLU's 0.397 mean) is a training-stability failure they
  inherit from the block above.
- **The evaluation team** owns the boundary: the learned gate's selectivity
  on real data and the benchmark gains are not measured here, and a claim
  that SwiGLU "beats" ReLU on this chapter's evidence alone would overreach
  its random-input boundary.

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
