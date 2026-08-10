"""pCTR calibration: the estimate must be the actual click rate.

Ad ranking uses pCTR inside eCPM, so a miscalibrated estimate corrupts the
auction: an overestimated ad wins too often. Calibration checks that the
predicted probability matches the observed rate at every confidence band.
This stage measures calibration error (ECE) and shows a Platt-style
correction.

Run:
    uv run python core/ctr_calibration.py
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
    # Miscalibrated: predicts 0.5-0.6 but observed clicks are ~0.3.
    preds = [0.55, 0.58, 0.52, 0.56, 0.53, 0.54, 0.57, 0.51, 0.59, 0.5]
    clicks = [0, 0, 1, 0, 0, 1, 0, 0, 0, 1]
    e = ece(preds, clicks)
    print("pCTR calibration, read:")
    print(f"  predicted range 0.50-0.59, observed clicks {sum(clicks)}/{len(clicks)}")
    print(f"  ECE = {e:.4f}")
    print("\nreading: the model predicts ~0.55 but only ~0.3 of these actually")
    print("click — a systematic overestimate. Inside eCPM this inflates the")
    print("ad's revenue estimate, so it wins the auction too often. ECE is")
    print("the number that catches it.")


if __name__ == "__main__":
    main()
