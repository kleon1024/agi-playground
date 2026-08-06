---
status: verified
level: foundation
base: scratch
label: The backward pass, three ways
verified: 2026-08-06
---

# What each of the three gradient checks establishes

**Question:** [the backpropagation chapter](../) verified one expression's
gradients three ways: its own autodiff engine, hand-derived calculus, and
torch. This chapter reads the recorded checks and asks what each comparison
proves.

**Before this:** [the backpropagation chapter](../) and its recorded
gradient checks.

## The checks, read

The run ([record](runs/2026-08-06-three-way-read.md)) reads both recorded
JSONs:

| comparison | max abs diff | what it establishes |
|---|---:|---|
| engine vs analytical (hand calculus) | 0.0e+00 | the engine computes the right gradient for the math |
| engine vs torch (`.backward()`) | 1.1e-16 | torch's black box computes the same thing |

The expression: `L = tanh(a^2 b + ac)` with `a=0.7, b=-0.5, c=1.2`.

## Two readings

**The two checks answer different questions.** Engine-vs-analytical asks "is
my implementation correct?" — it compares the engine's gradients against
gradients derived by hand from the chain rule, and they agree to machine
precision (0.0 difference). Engine-vs-torch asks "is my implementation
compatible with the framework everyone else uses?" — and torch's black box
computes the same numbers (1.1e-16, floating-point noise). A naive autodiff
bug would fail the first check; a framework-mismatch would fail the second.

**Together they make the engine trustworthy enough to teach with.** The
engine is correct (matches calculus) and interchangeable (matches torch), so
the reader can trust its intermediate values — the very values the chapter
uses to show where each gradient term comes from. Without the checks, the
engine's numbers would be the chapter's claim; with them, they are verified
arithmetic.

## Evidence boundary

The two recorded checks (one expression, three inputs, stdlib engine and
torch 2.13.0). It reads those artifacts; it does not claim every autodiff
implementation is correct — only that this one matches both references on
this expression.

## Check your mental model

Answer each before opening it.

**1. Why are two reference checks needed instead of one?**

<details>
<summary>Answer</summary>

Because "right" and "compatible" are different properties. Calculus says
what the true gradient is — the first check validates the engine against
truth. Torch says what the standard implementation computes — the second
check validates the engine against the framework. A bug could pass one and
fail the other, and knowing which one failed tells you whether the problem
is the engine or the framework.

</details>

**2. Why is the engine-vs-torch difference 1.1e-16 instead of exactly
zero?**

<details>
<summary>Answer</summary>

Because the two implementations evaluate operations in slightly different
orders, and floating-point addition is not associative. The 1.1e-16 gap is
machine-epsilon-scale noise — the signature of agreement, not a real
difference. A real bug shows up at 1e-8 or larger, which is why the
chapter's assert threshold (1e-12) sits far above the noise floor.

</details>

## Next

Back to [the backpropagation chapter](../), or to
[the optimization chapter](../../02-optimization/) which uses the gradients
this chapter verified.
