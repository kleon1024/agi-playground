"""The correction, read: what calibration does to the overestimate.

Stage 16 measures ECE but the fix is a correction: scale the predictions
so predicted rate equals observed rate. This script applies a simple
multiplicative correction to the miscalibrated estimate and shows the
ECE drop.

Run:
    uv run python core/correction_read.py
"""

from __future__ import annotations


def ece(preds: list[float], clicks: list[int], n_bins: int = 5) -> float:
    lo, hi = 0.0, 1.0
    width = (hi - lo) / n_bins
    total, n = 0.0, 0
    for b in range(n_bins):
        b_lo, b_hi = lo + b * width, lo + (b + 1) * width
        idx = [i for i, p in enumerate(preds) if b_lo <= p < b_hi]
        if not idx:
            continue
        avg_pred = sum(preds[i] for i in idx) / len(idx)
        avg_obs = sum(clicks[i] for i in idx) / len(idx)
        total += len(idx) * abs(avg_pred - avg_obs)
        n += len(idx)
    return total / n if n else 0.0


def main() -> None:
    preds = [0.55, 0.58, 0.52, 0.56, 0.53, 0.54, 0.57, 0.51, 0.59, 0.5]
    clicks = [0, 0, 1, 0, 0, 1, 0, 0, 0, 1]
    obs_rate = sum(clicks) / len(clicks)
    mean_pred = sum(preds) / len(preds)
    scale = obs_rate / mean_pred
    corrected = [min(p * scale, 0.99) for p in preds]
    print("the calibration correction, read:")
    print(f"  mean predicted {mean_pred:.3f}, observed {obs_rate:.3f}")
    print(f"  correction factor {scale:.3f}")
    print(f"  ECE before {ece(preds, clicks):.4f} -> after "
          f"{ece(corrected, clicks):.4f}")
    print("\nreading: a single multiplicative correction — scale the")
    print("predictions by observed/predicted — removes the systematic")
    print("bias (ECE 0.245 -> ~0). The correction is the fix calibration")
    print("exists to apply, and the before/after is the measure.")


if __name__ == "__main__":
    main()
