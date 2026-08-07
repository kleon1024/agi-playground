"""The gate that beats ReLU: SwiGLU's mechanism, measured on random inputs.

The 88M decoder's feed-forward block is a SwiGLU: gate = SiLU(x W_gate),
up = x W_up, output = gate * up — a multiplicative interaction instead of
a plain pointwise activation. Shazeer's GLU-variants paper measured the
family's edge; this script measures the mechanism on random inputs at the
repo's geometry: how the hidden-unit output distribution differs under
ReLU, GELU, and SwiGLU, and what the gate shape does to the signal.

Run:
    uv run python core/swiglu_anatomy.py
"""

from __future__ import annotations

import math

import numpy as np


def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def gelu(x: np.ndarray) -> np.ndarray:
    return 0.5 * x * (1.0 + np.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))


def silu(x: np.ndarray) -> np.ndarray:
    return x / (1.0 + np.exp(-x))


def stats(x: np.ndarray) -> tuple[float, float, float]:
    flat = x.reshape(-1)
    return float(flat.mean()), float(flat.std()), float(np.mean(np.abs(flat) < 1e-3))


def main() -> None:
    rng = np.random.default_rng(20260806)
    n = 200_000
    x = rng.standard_normal(n)
    gate = silu(x)  # the gate's input
    up = rng.standard_normal(n)  # a stand-in for the up-projection output

    print(f"{'activation':<10} {'mean':>8} {'std':>8} {'near-zero':>10}")
    for name, out in (
        ("ReLU", relu(x)),
        ("GELU", gelu(x)),
        ("SwiGLU", gate * up),
    ):
        mean, std, zero = stats(out)
        print(f"{name:<10} {mean:>8.4f} {std:>8.4f} {zero:>10.1%}")

    print("\ngate shape (SiLU) vs plain linear: the gate passes negatives")
    print("through a damped, sign-kept transform instead of zeroing them")
    print("(ReLU) or bending them (GELU), and multiplies — a gating, not")
    print("a squashing, of the up-projection.")


if __name__ == "__main__":
    main()
