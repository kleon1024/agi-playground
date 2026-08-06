"""The backward pass, verified three ways, read from the recorded JSONs.

The backpropagation chapter checked one small expression's gradients three
ways: its own scalar autodiff engine, hand-derived calculus, and torch's
.backward(). This script reads both recorded JSONs and lays out what each
comparison establishes — engine vs analytical validates the implementation,
engine vs torch validates it against the framework everyone else uses.

Inputs (recorded, unchanged): ../runs/gradient-check.json and
../runs/torch-cross-check.json

Run:
    uv run python core/three_way_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    gc = json.loads((runs / "gradient-check.json").read_text())
    tc = json.loads((runs / "torch-cross-check.json").read_text())
    print(f"expression: L = tanh(a^2 b + ac), a={gc['inputs']['a']}, "
          f"b={gc['inputs']['b']}, c={gc['inputs']['c']}")
    print("  engine vs analytical (hand calculus): "
          f"max diff {gc['max_abs_diff_engine_vs_analytical']:.1e}")
    print("  engine vs torch (.backward()): "
          f"max diff {tc['max_abs_diff_engine_vs_torch']:.1e}")
    print("\nreading: the two checks answer different questions. The first says")
    print("the engine computes the right gradient for the math; the second says")
    print("torch's black box computes the same thing — so the engine is both")
    print("correct and interchangeable with the framework's.")


if __name__ == "__main__":
    main()
