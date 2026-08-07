---
status: verified
level: foundation
base: none
label: Rotary position encoding
verified: 2026-08-06
---

# How does a position encoding that never adds a vector work?

**Question:** [the decoder block](../) says positions must be told apart, but
the repo's 88M model never adds a position vector — it rotates queries and
keys by an angle that grows with position. What does that rotation actually
give you, and what does `rope_theta = 10_000` in the config control?

**Before this:** [the decoder block's attention](../), up to the point where
attention needs position information.

## The rotation, once

For a query at position m and a key at position n, dimension i of each vector
is rotated by `m * rope_theta^(-2i/d_head)` and `n * rope_theta^(-2i/d_head)`
radians respectively. Two things follow from that one formula:

- The score between the two depends only on the difference m - n, because
  rotating q by m and k by n is the same as rotating q by m - n relative to
  an unrotated k.
- Each dimension rotates at a different speed: dim 0 at one radian per
  position, dim i at rope_theta^(-2i/d) radians per position.

<!-- interactive: RoPEDecay -->

## The three measured properties

The run ([record](runs/2026-08-06-rope-mechanics.md)) measures them at the
repo's geometry — d_head 64, rope_theta 10k:

**Translational invariance, to machine precision.** Delta 3 scores
-0.100784 at positions (5,2), (100,97), and (1000,997). The same pattern
shifted anywhere in the sequence scores identically. Absolute position
embeddings cannot do this: their score depends on the positions themselves,
not the gap.

**The wavelength ladder.** Positions per full rotation climb geometrically
across dimensions: dim 0 at 6.3, dim 8 at 62.8, dim 16 at 628, dim 24 at
6,283, dim 31 at 47,117. The high-frequency dims change their phase every
few positions (fine-grained locality); the low-frequency dims change almost
never (long-range order). The model reads both from the same vector because
they occupy different dimensions.

**rope_theta is the long-context knob.** Raise it to 500k and dim 16's
wavelength stretches 628 to 4,443 positions, dim 31 from 47,117 to 2.08
million. Only dim 0 is immune — its exponent is zero, so its speed is
theta-independent. A model that needs to tell positions 50,000 apart keeps
the low-frequency dims from having wrapped around, which is why long-context
models raise the base.

## What the fixed-pair curve is not

The score-vs-distance curve oscillates for any fixed query-key pair, and the
run reports the trajectory rather than an average because an average over
random pairs would be flat — an orthogonal rotation preserves the
distribution of an isotropic inner product. The oscillation shape is what
theta changes: at 10k the high-frequency dims complete several cycles within
64 positions, at 500k the same window holds fewer, longer cycles. Whether
the model uses that oscillation to attend to near or far tokens is learned;
the encoding only supplies the geometry.

## Evidence boundary

This chapter computes the rotation arithmetic on one fixed random (q, k)
pair at the repo's d_head; it does not train a model, does not measure how a
trained head uses the geometry, and does not claim any theta is optimal. The
invariance and wavelength numbers are exact arithmetic from the config; the
score curve is one pair's trajectory.

## Check your mental model

Answer each before opening it.

**1. Why is the delta-3 score identical at positions 5 and 1,000?**

<details>
<summary>Answer</summary>

Because rotating q by m and k by n is equivalent to rotating q by m - n
against an unrotated k: both rotations cancel the absolute positions and
leave only the gap. Any pair with the same delta has the same relative
geometry, so the score is a function of the gap alone.

</details>

**2. Raising rope_theta from 10k to 500k barely changes dim 0 but stretches
dim 31 by a factor of 44. Why?**

<details>
<summary>Answer</summary>

Because dim i rotates at rope_theta^(-2i/d) radians per position. Dim 0's
exponent is zero, so its speed is exactly one radian per position for any
theta; dim 31's exponent is -62/64, so it scales with theta^0.97 — nearly
linear in the base. The stretch is geometric in dimension and roughly linear
in theta.

</details>

## Next

Back to [the decoder block](../), or forward to
[mission 01's architecture](../../../01-language-model/02-pretrain/)
where this rotation is one config line in the 88M model.
