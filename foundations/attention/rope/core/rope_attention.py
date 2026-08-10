"""Rotary position encoding, measured on the repo's own head geometry.

The 88M decoder in mission 01 uses RoPE with `rope_theta = 10_000` on d_head
= 64 (see `02-pretrain/core/model.py`). This script measures three real
properties of that choice at the real geometry (no model trained):

1. **Translational invariance.** The score between a query at position m and
   a key at position n depends only on delta = m - n: q_m = R(m)q and
   k_n = R(n)k give q^T R(m-n) k. Two pairs with the same delta, far apart,
   must score identically. Measured directly.

2. **The wavelength of each dimension.** Dim i rotates by
   rope_theta^(-2i/d_head) radians per position, so the highest-frequency
   dims complete a full rotation in a handful of positions and the lowest in
   many. The wavelength per dim is positions-per-cycle; larger rope_theta
   stretches every wavelength, which is why it is the long-context knob.

3. **The fixed-pair oscillation.** For one fixed (q, k) pair, the score as a
   function of delta oscillates, and how fast it decorrelates is set by the
   rotation speeds. A flat average over random pairs would hide this (an
   orthogonal rotation preserves the distribution of an isotropic inner
   product), so the trajectory is measured on fixed pairs, not averaged.

Run:
    uv run --group torch python core/rope_attention.py
"""

from __future__ import annotations

import math

import numpy as np


def rope_angles(positions: np.ndarray, rope_theta: float, d_head: int) -> np.ndarray:
    """Per (position, dim) rotation angle: pos * theta^(-2i/d_head)."""
    dims = np.arange(d_head // 2, dtype=np.float64)
    freqs = 1.0 / (rope_theta ** (2 * dims / d_head))
    return positions[:, None] * freqs[None, :]  # (P, d/2)


def apply_rope(x: np.ndarray, angles: np.ndarray) -> np.ndarray:
    """Rotate the (..., d/2) pairs of x by the given angles."""
    x = x.reshape(x.shape[:-1] + (-1, 2))
    cos = np.cos(angles)
    sin = np.sin(angles)
    a, b = x[..., 0], x[..., 1]
    return np.concatenate([a * cos - b * sin, a * sin + b * cos], axis=-1)


def score(q: np.ndarray, k: np.ndarray, m: int, n: int, rope_theta: float, d_head: int) -> float:
    angles_q = rope_angles(np.array([m]), rope_theta, d_head)
    angles_k = rope_angles(np.array([n]), rope_theta, d_head)
    return float((apply_rope(q[None, :], angles_q) * apply_rope(k[None, :], angles_k)).sum())


def wavelength(dim: int, rope_theta: float, d_head: int) -> float:
    """Positions per full rotation for one dimension."""
    freq = rope_theta ** (-2 * dim / d_head)
    return 2 * math.pi / freq


def main() -> None:
    d_head = 64
    rng = np.random.default_rng(20260806)
    q = rng.standard_normal(d_head)
    q /= np.linalg.norm(q)
    k = rng.standard_normal(d_head)
    k /= np.linalg.norm(k)

    print(f"d_head={d_head}, rope_theta=10k (the repo's config)")

    print("\n1. translational invariance: same delta, far-apart positions")
    for m, n in ((5, 2), (100, 97), (1000, 997)):
        s = score(q, k, m, n, 10_000.0, d_head)
        print(f"  delta 3 at ({m},{n}): {s:+.6f}")

    print("\n2. wavelengths per dimension (positions per full rotation)")
    print(f"{'dim':>4} {'theta=10k':>12} {'theta=500k':>12}")
    for dim in (0, 8, 16, 24, 31):
        w10 = wavelength(dim, 10_000.0, d_head)
        w500 = wavelength(dim, 500_000.0, d_head)
        print(f"{dim:>4} {w10:>12.1f} {w500:>12.1f}")

    print("\n3. fixed-pair score vs delta, decorrelation")
    for theta, label in ((10_000.0, "10k"), (500_000.0, "500k")):
        scores = [abs(score(q, k, d, 0, theta, d_head)) for d in range(1, 65)]
        mean = sum(scores) / len(scores)
        lag1 = sum(scores[i] * scores[i + 1] for i in range(len(scores) - 1)) / (len(scores) - 1)
        print(f"  theta={label}: mean|score| over delta 1..64 = {mean:.4f}, "
              f"lag-1 autocorrelation = {lag1:.4f}")


if __name__ == "__main__":
    main()
