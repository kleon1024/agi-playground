# Run — scalar autodiff engine vs. hand-derived calculus vs. torch `.backward()`

**Date:** 2026-08-02
**Hardware:** any CPU (Apple M-series laptop used here) — check 1 needs no
framework; check 2 needs the optional `torch` dependency group.
**Software:** Python 3.12, stdlib only for check 1; torch 2.13.0 for check 2.
**Cost:** \$0. Wall-clock for both checks combined: under 10ms.

## Commands

```bash
uv run python core/verify_gradients.py
uv run --group torch python core/verify_torch.py
```

No arguments — the test expression and its inputs (`a=0.7, b=-0.5, c=1.2`)
are constants at the top of `core/verify_gradients.py`.

## Output

```
$ uv run python core/verify_gradients.py
a=0.7, b=-0.5, c=1.2
L               engine=0.533482128457  analytical=0.533482128457
dL/da           engine=0.357698409308  analytical=0.357698409308
dL/db           engine=0.350544441122  analytical=0.350544441122
dL/dc           engine=0.500777773032  analytical=0.500777773032
max_abs_diff=0.000e+00  (assert threshold 1e-12, passed)

$ uv run --group torch python core/verify_torch.py
torch version: 2.13.0
a=0.7, b=-0.5, c=1.2
L               engine=0.533482128457  torch=0.533482128457
dL/da           engine=0.357698409308  torch=0.357698409308
dL/db           engine=0.350544441122  torch=0.350544441122
dL/dc           engine=0.500777773032  torch=0.500777773032
max_abs_diff=1.110e-16  (assert threshold 1e-12, passed)
```

Full numbers: [`gradient-check.json`](gradient-check.json),
[`torch-cross-check.json`](torch-cross-check.json).

## Notes

- **The test expression is deliberately a diamond graph.** `a` is consumed
  twice (`d = a*b` and `f = e*a`), which is the case that breaks a backward
  pass using `self.grad = ...` instead of `self.grad += ...` — accumulation
  across every path to a reused node, not just a chain, is what this check
  actually exercises.
- **Check 1 is exact (`0.000e+00`)** because both sides — the graph-based
  engine and the hand-coded closed-form derivative — compute the same
  floating-point operations in the same order for this particular
  expression.
- **Check 2's `1.11e-16` gap is float64's own precision floor**, not
  disagreement: torch's `autograd` reduces the identical graph shape through
  a different internal operation order (dispatch, its own tensor
  representation), and this is the expected size of that rounding
  difference. Both checks pass their `1e-12` assertion threshold by many
  orders of magnitude.
- **Deterministic, not seed-dependent.** No randomness anywhere in either
  script — re-running reproduces these exact numbers.
