---
status: verified
level: foundation
base: scratch
verified: 2026-08-02
---

# What does `.backward()` actually do?

[The first training loop](../01-first-training-loop/) calls `loss.backward()`
once and every weight in a real GPT gets an update. That call is treated as a
black box there, on purpose — the chapter's job was the loop, not the
mechanism inside one line of it. This chapter opens that line.

**Before this:** [the first training loop](../01-first-training-loop/), so
you have already seen one `.backward()` call change real weights. This
chapter needs no neural network — three numbers and four operations expose
the same mechanism with nothing else in the way.

Run it first. Understand it second. Both checks together take under ten
milliseconds.

```bash
uv run python core/verify_gradients.py
uv run --group torch python core/verify_torch.py
```

## 1. A chain of operations, not a single formula

Take a small expression with three inputs, reusing one of them:

```text
a, b, c            (leaves)
d = a * b
e = d + c
f = e * a           <- 'a' again
L = tanh(f)
```

Written as one formula, $L = \tanh(a^2 b + ac)$, this is differentiable by
hand in a few lines of calculus. Real training loops never get this luxury —
a transformer's loss is a composition of thousands of matrix multiplies,
additions, and nonlinearities, far too many for anyone to write out a single
closed-form derivative for the whole thing. The question this chapter answers
is how a machine differentiates a composition it has never seen a symbolic
form for, using only the derivative of each individual operation.

## 2. Build the graph forward, walk it backward

Wrap every number in a `Value` that remembers what produced it:

```python
class Value:
    def __init__(self, data, children=(), op=""):
        self.data = data
        self.grad = 0.0
        self._backward = lambda: None   # how to push gradient to children
        self._prev = set(children)
```

Each operation returns a new `Value` and attaches a `_backward` closure that
knows only its own local derivative — `__mul__`'s backward rule is "each
factor's gradient contribution is the *other* factor's value, times whatever
gradient arrived from above," nothing more global than that:

```python
def __mul__(self, other):
    out = Value(self.data * other.data, (self, other), "*")
    def _backward():
        self.grad  += other.data * out.grad
        other.grad += self.data  * out.grad
    out._backward = _backward
    return out
```

`backward()` topologically sorts the graph built during the forward pass,
then visits nodes in reverse order, calling each one's local `_backward`.
Every node needs only the operations immediately touching it — the chain rule
is applied one link at a time, and the "global" derivative of a value nine
operations upstream falls out of nine local multiplications, never a symbolic
expression anyone had to derive for the whole graph at once.

## 3. Why `+=`, never `=`

`a` is consumed twice above: once in `d = a * b`, once in `f = e * a`. A
backward pass that *assigns* `a.grad` instead of *accumulating* into it would
silently keep only the second contribution and drop the first — a real,
easy-to-write bug, not a hypothetical one.

The multivariate chain rule says a value's total gradient is the **sum** of
its contributions along every path to the output. Every `_backward` closure
above writes `self.grad += ...`, never `self.grad = ...`, for exactly this
reason: each of `a`'s two consumers pushes its own contribution, and the
final `a.grad` is correct only because both additions land in the same
accumulator.

Step the walk below and watch where `a`'s two contributions arrive, then flip
the operator and run it again.

<!-- interactive: GradientFlow -->

Flipping it changes one number. `b` comes out at 0.3505 and `c` at 0.5008
either way, because each is consumed once and a single write is a correct
write. Only `a` moves — from **0.3577** to **−0.2504**, because `d`'s push
arrives second and overwrites `f`'s. The magnitude is wrong, but the sign is
what makes this expensive: `a` would be pushed in the opposite direction on
every step, and the backward pass would complete, report no error, and produce
gradients that look entirely plausible for the other two leaves.

That is the shape of the failure to expect. A dropped contribution does not
crash a training run; it quietly corrupts the parameters that happen to be
reused, which in a transformer means every tied embedding and every weight
shared across positions.

## 4. Two independent checks, not one

**Check 1 — does the engine agree with calculus done by hand?** Write
$f(a,b,c) = a^2b + ac$ directly (skipping the graph entirely) and its
derivative $\partial L/\partial a = (1-\tanh^2 f)(2ab+c)$ the same way. Run
both the graph-based engine and this closed form on identical inputs
($a=0.7$, $b=-0.5$, $c=1.2$):

```
L               engine=0.533482128457  analytical=0.533482128457
dL/da           engine=0.357698409308  analytical=0.357698409308
dL/db           engine=0.350544441122  analytical=0.350544441122
dL/dc           engine=0.500777773032  analytical=0.500777773032
max_abs_diff=0.000e+00
```

Exact agreement — not close, identical to the last printed digit. Full data:
[`runs/gradient-check.json`](runs/gradient-check.json).

**Check 2 — does the engine agree with the `.backward()` this repository
already calls?** Build the identical graph a second time with torch tensors
(`requires_grad=True`), call torch's own `.backward()`, and compare:

```
torch version: 2.13.0
L               engine=0.533482128457  torch=0.533482128457
dL/da           engine=0.357698409308  torch=0.357698409308
dL/db           engine=0.350544441122  torch=0.350544441122
dL/dc           engine=0.500777773032  torch=0.500777773032
max_abs_diff=1.110e-16
```

The one-bit-of-machine-epsilon difference (`1.11e-16`, float64's own
precision floor) is float rounding, not disagreement — this is the same
mechanism, not a coincidence: torch's `autograd` builds the identical kind of
graph on the forward pass and reduces it in reverse the same way, with
dispatch, device placement, and fused kernels layered on top of the same
core idea. Full data: [`runs/torch-cross-check.json`](runs/torch-cross-check.json).

## What this does not establish

A five-node scalar graph says nothing about tensor-shaped autodiff's actual
engineering difficulty: real frameworks batch operations, place them on
specific devices, fuse chains of them into single kernels, and must do all of
this while keeping memory bounded across models with billions of parameters
— none of that is touched here. It says nothing about higher-order
derivatives (gradients of gradients), which real optimizers occasionally need
and this engine cannot compute. And it is not a claim that this toy is fast:
`core/engine.py` builds one Python object per scalar operation, which does
not remotely resemble how a real training step executes. What it does
establish is the mechanism itself — local derivatives, applied one link at a
time in reverse topological order, with accumulation at every reused node —
which is unchanged between this five-node toy and the multi-billion-operation
graph [pretraining](../../missions/01-language-model-agent/02-pretrain/) actually walks.

## A brief, dated history

The `Value` class above is not a modern idea implemented simply. It is a 1970
mechanism that spent decades waiting for anyone to need it at this scale.

<!-- interactive: AutodiffLineage -->

## Check your mental model

**1. Why does reverse-mode autodiff need only one backward pass to get every
parameter's gradient, when forward-mode differentiation would need one pass
per input?**

<details>
<summary>Answer</summary>

Reverse mode computes, in one backward walk, how the single output (the
loss) depends on every input — exactly the "many inputs, one output" shape a
training loss has (millions of parameters, one scalar loss). Forward-mode
autodiff instead propagates "how does the output change if I perturb *this
one* input" — useful when there are few inputs and many outputs, but for a
model with millions of parameters it would mean one full forward-mode pass
per parameter to get the same information reverse mode produces in a single
backward pass.

</details>

**2. What would go wrong if `_backward` closures used `self.grad = ...`
instead of `self.grad += ...`?**

<details>
<summary>Answer</summary>

Any value consumed more than once (like `a` in the diamond expression, used
in both `d = a*b` and `f = e*a`) would have its gradient overwritten by
whichever consumer's contribution is processed last, silently discarding the
other contribution. The multivariate chain rule requires *summing*
contributions along every path from a value to the final output — assignment
instead of accumulation breaks exactly the case where a value's graph
position isn't a simple chain.

</details>

**3. This chapter's engine agreed with torch's `.backward()` to within
`1.11e-16`. What is that gap, and what would a much larger gap have implied?**

<details>
<summary>Answer</summary>

`1.11e-16` is at the precision floor of float64 arithmetic itself — the two
implementations are computing the same mathematical quantity through
slightly different orders of floating-point operations, and this is the
expected size of that rounding difference, not a disagreement. A much larger
gap (say, differing in the second or third digit) would mean the two
implementations were computing genuinely different quantities — evidence of
a real bug in one of the two backward-pass implementations, not floating-point
noise.

</details>

**4. Where does the "local derivative" idea break down as a description of
what a real framework like PyTorch does at scale?**

<details>
<summary>Answer</summary>

The *mechanism* — local derivatives applied in reverse topological order with
accumulation at reused nodes — does not break down; it is exactly what
PyTorch's `autograd` also does. What changes at scale is everything layered
on top: operations are batched across many examples at once instead of one
scalar at a time, placed on specific devices (GPU vs CPU), and often fused
into single kernels so the framework never materializes every intermediate
`Value`-like object the way this toy explicitly does. None of that changes
the reverse-mode mechanism itself — it changes how efficiently that mechanism
is executed.

</details>

## Reading the code

`core/engine.py` is under 100 lines: the `Value` class and the one test
expression (`diamond_expression`), no numpy, no torch. `core/verify_gradients.py`
cross-checks the engine against a hand-coded closed-form derivative (no torch
needed). `core/verify_torch.py` cross-checks the same engine against real
`torch.Tensor.backward()` on an identical graph (needs the optional `torch`
dependency group, same as this repository's other torch-dependent checks).

## Exercises

1. **Break the accumulation on purpose.** Change `self.grad += ...` to
   `self.grad = ...` in `__mul__` and `__add__`, then re-run
   `verify_gradients.py`. Only `dL/da` should now disagree with the
   analytical answer — `a` is the only leaf consumed twice.
2. **Add a fourth operation.** Extend `Value` with `__pow__` for integer
   exponents and rebuild the test expression using `a**2` instead of `a*a` in
   one place. The gradient check should still pass unchanged.
3. **Widen the graph.** Add a second output that also depends on `a`, `b`,
   `c` (for example `L2 = tanh(d)`), sum `L + L2` into one final scalar, and
   confirm `backward()` still accumulates every path correctly without any
   change to the engine itself.

## Next

[Optimization](../02-optimization/) picks up exactly where this chapter's
`.grad` values end: once every parameter has a gradient, an optimizer decides
how to turn it into an update. Or return to
[the first training loop](../01-first-training-loop/) and note that its
`loss.backward()` call is now this chapter's mechanism, not a black box.

Primary references: Linnainmaa (1970), Rumelhart/Hinton/Williams (1986), and
the Theano/Chainer/autograd/PyTorch lineage dated above.

[The foundations landscape](../LANDSCAPE.md) already pairs this mechanism
with PyTorch `autograd` and JAX `grad`/`vjp` as the production implementations
of the same idea.

A detour from here: [what each of the three gradient checks
establishes](the-backward-pass-three-ways/) — the recorded checks read:
engine-vs-analytical validates the implementation (0.0 diff), engine-vs-
torch validates compatibility (1.1e-16), two questions answered by two
reference points.
