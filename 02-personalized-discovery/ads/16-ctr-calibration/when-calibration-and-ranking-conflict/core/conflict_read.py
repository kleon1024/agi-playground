"""When calibration and ranking conflict, read.

A model can rank clicks perfectly while being miscalibrated — the
ordering is right, the values are wrong. This script builds such a model
and shows that ranking quality and calibration error are independent,
which is why the ads stack needs both.

Run:
    uv run python core/conflict_read.py
"""

from __future__ import annotations


def main() -> None:
    # True probabilities and a model that ranks them identically but
    # predicts every value shifted up by 0.2.
    true = [0.2, 0.4, 0.6, 0.8]
    pred = [p + 0.2 for p in true]
    order_true = sorted(range(4), key=lambda i: true[i], reverse=True)
    order_pred = sorted(range(4), key=lambda i: pred[i], reverse=True)
    print("calibration vs ranking independence, read:")
    print(f"  true:      {[f'{p:.2f}' for p in true]}")
    print(f"  predicted: {[f'{p:.2f}' for p in pred]}")
    print(f"  ranking match: {order_true == order_pred} "
          f"(order {order_true} == {order_pred})")
    err = sum(abs(p - t) for p, t in zip(pred, true)) / 4
    print(f"  mean calibration error: {err:.2f}")
    print("\nreading: the ranking is identical but every value is wrong by")
    print("0.2 — a ranker judged only by ordering passes, while eCPM and the")
    print("auction (which use the values) inherit the error. Calibration is")
    print("a separate property from ranking, and the ads stack needs both.")


if __name__ == "__main__":
    main()
