"""Retrain flips the metric, read: the offline win is not the online
outcome.

Stage 46 detour: retraining on fresh data raises offline NDCG, but
the new model serves a different slate, and the exposure shift moves
the online CTR the other way. The metric that decided the retrain
and the metric the business sees can disagree.

Run:
    uv run python core/retrain_flips.py
"""

from __future__ import annotations

# Offline eval: five items with logged relevance labels, scored by the
# old and the retrained model. NDCG@5 over the score order.
LABELS = [1, 1, 0, 0, 1]
OLD_SCORES = [3.0, 2.5, 2.0, 1.5, 1.0]
NEW_SCORES = [2.9, 2.5, 2.0, 1.0, 2.4]

# Online slate: observed CTR at each served position, old vs new model.
# Position one carries the most exposure.
EXPOSURE = [0.30, 0.20, 0.15, 0.12, 0.10]
OLD_SLATE = [0.045, 0.036, 0.028, 0.021, 0.015]
NEW_SLATE = [0.036, 0.033, 0.032, 0.030, 0.024]


def ndcg(scores: list[float], labels: list[int]) -> float:
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    gain = 0.0
    ideal = 0.0
    relevant = sum(labels)
    for pos, idx in enumerate(order):
        discount = 1.0 if pos == 0 else 1.0 / (pos + 1).bit_length()
        if labels[idx]:
            gain += discount
    for pos in range(relevant):
        discount = 1.0 if pos == 0 else 1.0 / (pos + 1).bit_length()
        ideal += discount
    return gain / ideal if ideal else 0.0


def exposure_ctr(slate: list[float], weights: list[float]) -> float:
    return sum(c * w for c, w in zip(slate, weights))


def main() -> None:
    print("retrain flips the metric, read (old model vs retrained):")
    print(f"  offline ndcg@5: old {ndcg(OLD_SCORES, LABELS):.3f} -> "
          f"new {ndcg(NEW_SCORES, LABELS):.3f}")
    print(f"  exposure-weighted ctr: old {exposure_ctr(OLD_SLATE, EXPOSURE):.4f} "
          f"-> new {exposure_ctr(NEW_SLATE, EXPOSURE):.4f}")
    print("\nreading: the retrained model scores higher on the offline")
    print("list, but the slate it serves clicks less where it matters.")
    print("The offline labels were logged under the old policy, where")
    print("the top position inflated its own clicks; NDCG believes")
    print("that log, and the online page does not. The retrain decision")
    print("needs the metric that matches the goal - and an A/B, because")
    print("the exposure shift is only visible online.")


if __name__ == "__main__":
    main()
