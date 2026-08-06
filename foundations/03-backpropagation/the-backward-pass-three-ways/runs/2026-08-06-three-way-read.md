# Run — the backward pass, verified three ways

**Date:** 2026-08-06
**Command:** `uv run python core/three_way_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads two committed JSONs).
**Cost:** \$0 (local lane; the gradients were the chapter's recorded
2026-08-02 checks).

## Purpose

The backpropagation chapter checked one expression's gradients three ways.
This run reads both recorded JSONs and lays out what each comparison
establishes.

## Output

```
expression: L = tanh(a^2 b + ac), a=0.7, b=-0.5, c=1.2
  engine vs analytical (hand calculus): max diff 0.0e+00
  engine vs torch (.backward()): max diff 1.1e-16
```

## Notes

- The two checks answer different questions: engine vs analytical says the
  implementation computes the right gradient for the math; engine vs torch
  says the framework's black box computes the same thing.
- Together they make the engine both correct and interchangeable with the
  framework everyone else uses.
