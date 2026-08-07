"""The hidden-slice audit: aggregate ECE passes, one slice fails.

The stage run measures ECE on ten impressions. The audit asks the
case-finding question at production scale: which slices carry the
calibration error? It draws 20,000 impressions (fixed seed): 18,000 on a
calibrated desktop slice, 2,000 on a mobile slice whose click rate is
half the prediction. Aggregate ECE looks acceptable; the mobile slice
is badly miscalibrated and diluted by the majority.

Run:
    uv run python core/slice_calibration.py
"""

from __future__ import annotations

import random


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


def draw_slice(
    rng: random.Random,
    n: int,
    obs_multiplier: float,
) -> tuple[list[float], list[int]]:
    """Predictions ~ U(0.1, 0.9); observed click rate = pred * multiplier."""
    preds: list[float] = []
    clicks: list[int] = []
    for _ in range(n):
        p = rng.uniform(0.1, 0.9)
        preds.append(p)
        clicks.append(1 if rng.random() < p * obs_multiplier else 0)
    return preds, clicks


def main() -> None:
    rng = random.Random(20260807)
    desktop_n, mobile_n = 18_000, 2_000
    desktop_preds, desktop_clicks = draw_slice(rng, desktop_n, 1.0)
    mobile_preds, mobile_clicks = draw_slice(rng, mobile_n, 0.5)

    preds = desktop_preds + mobile_preds
    clicks = desktop_clicks + mobile_clicks
    agg = ece(preds, clicks)
    desk = ece(desktop_preds, desktop_clicks)
    mob = ece(mobile_preds, mobile_clicks)

    print("hidden-slice audit: 20,000 impressions, fixed seed")
    print("desktop slice: calibrated (click rate = prediction)")
    print("mobile slice:  click rate = half the prediction\n")
    print(f"  {'slice':>8} {'share':>7} {'ECE':>8} {'mean pred':>10} "
          f"{'mean obs':>9}")
    print(f"  {'desktop':>8} {desktop_n / len(preds):>7.1%} {desk:>8.4f} "
          f"{sum(desktop_preds) / desktop_n:>10.4f} "
          f"{sum(desktop_clicks) / desktop_n:>9.4f}")
    print(f"  {'mobile':>8} {mobile_n / len(preds):>7.1%} {mob:>8.4f} "
          f"{sum(mobile_preds) / mobile_n:>10.4f} "
          f"{sum(mobile_clicks) / mobile_n:>9.4f}")
    print(f"  {'aggregate':>8} {'100%':>7} {agg:>8.4f} "
          f"{sum(preds) / len(preds):>10.4f} "
          f"{sum(clicks) / len(clicks):>9.4f}")

    print("\nreading: the aggregate ECE looks acceptable while the mobile")
    print("slice overstates clicks by half. Stratifying by slice is how the")
    print("case is found -- the aggregate passes, the slice fails, and the")
    print("mobile slice keeps overpaying eCPM until someone looks per slice.")


if __name__ == "__main__":
    main()
