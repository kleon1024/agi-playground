"""Drift is silent, read: the offline metric stays flat while the
online world moves.

Stage 47 detour: the offline eval reuses the training distribution,
so a serving-time break leaves it unchanged. The prediction-versus-
observation gap is the panel that shows what the offline number hides.

Run:
    uv run python core/silent_drift.py
"""

from __future__ import annotations

# (hour, offline ndcg, predicted ctr, observed ctr)
ROWS = [
    (0, 0.712, 0.040, 0.039),
    (4, 0.712, 0.040, 0.036),
    (8, 0.712, 0.040, 0.023),
    (12, 0.711, 0.040, 0.020),
]


def main() -> None:
    print("drift is silent, read (offline vs online by hour):")
    print("  hour  offline ndcg  predicted  observed  gap")
    for hour, ndcg, pred, obs in ROWS:
        print(f"  {hour:>3}  {ndcg:.3f}        {pred:.3f}     {obs:.3f}     {pred - obs:.3f}")
    print("\nreading: offline NDCG is flat at 0.712 across all twelve")
    print("hours while observed CTR halves. The offline number is not")
    print("lying - it is blind: its labels come from the same broken")
    print("feed. The gap panel is the one that changes, which is why")
    print("monitoring lives online, not in the eval harness.")


if __name__ == "__main__":
    main()
