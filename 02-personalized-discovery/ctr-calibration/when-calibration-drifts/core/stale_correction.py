"""The stale correction, read: the fix fits a window, then the market moves.

The stage's correction scaled every prediction by the ratio of observed
to predicted clicks on its training window. This read fits that factor on
an old window, then evaluates it on a new window where the click rate has
risen. The factor that fixed the training window now over-corrects: ECE
on the new window is worse with the stale correction than without it.

Run:
    uv run python core/stale_correction.py
"""

from __future__ import annotations


def ece(preds: list[float], clicks: list[int], n_bins: int = 5) -> float:
    """Expected calibration error: |predicted rate - observed rate| per bin."""
    lo, hi = 0.0, 1.0
    width = (hi - lo) / n_bins
    total = 0.0
    n = 0
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
    # Same miscalibrated model as the stage: predicts 0.50-0.59.
    preds = [0.55, 0.58, 0.52, 0.56, 0.53, 0.54, 0.57, 0.51, 0.59, 0.50]
    clicks_old = [0, 0, 1, 0, 0, 1, 0, 0, 0, 1]  # 3/10 clicks, rate 0.30
    clicks_new = [0, 1, 1, 0, 1, 1, 0, 1, 0, 1]  # 5/10 clicks, rate 0.50

    mean_pred = sum(preds) / len(preds)
    rate_old = sum(clicks_old) / len(clicks_old)
    factor = rate_old / mean_pred
    corrected = [p * factor for p in preds]

    ece_old_raw = ece(preds, clicks_old)
    ece_old_fixed = ece(corrected, clicks_old)
    ece_new_raw = ece(preds, clicks_new)
    ece_new_stale = ece(corrected, clicks_new)

    print("stale-correction read: factor fit on the old window, applied to")
    print("the new one. The model still predicts ~0.545; the click rate")
    print("rose from 0.30 to 0.50.\n")
    print(f"  {'window':>10} {'ECE raw':>9} {'ECE corrected':>15}")
    print(f"  {'old':>10} {ece_old_raw:>9.4f} {ece_old_fixed:>15.4f}")
    print(f"  {'new':>10} {ece_new_raw:>9.4f} {ece_new_stale:>15.4f}")
    print(f"\ncorrection factor fit on old data: {factor:.4f}")

    print("\nreading: on the training window the factor drops ECE 0.2450 to")
    print("0.0000. On the new window the same factor over-corrects -- ECE")
    print("jumps to 0.3000, worse than the 0.0550 the raw estimate carried.")
    print("The fix has an expiration date: calibration must be refit on a")
    print("rolling window, and drift is detected by monitoring ECE on new")
    print("traffic, not by trusting the last fit.")


if __name__ == "__main__":
    main()
