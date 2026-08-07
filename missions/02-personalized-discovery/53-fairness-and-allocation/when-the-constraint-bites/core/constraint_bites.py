"""Constraint bites, read: the floor has a price, and the price is a
curve.

Stage 53 detour: a per-category minimum exposure lifts the tail and
costs aggregate CTR. The cost grows faster than the floor - the last
few points of the constraint buy the most visible allocation and the
most expensive clicks.

Run:
    uv run python core/constraint_bites.py
"""

from __future__ import annotations

CTRS = [0.040, 0.032, 0.022, 0.010]


def shares(floor: float) -> list[float]:
    weights = [c ** 3 for c in CTRS]
    total = sum(weights)
    raw = [w / total for w in weights]
    raw = [max(s, floor) for s in raw]
    total = sum(raw)
    return [s / total for s in raw]


def main() -> None:
    print("constraint bites, read (floor vs aggregate ctr):")
    for floor in (0.0, 0.05, 0.10, 0.20):
        s = shares(floor)
        agg = sum(share * ctr for share, ctr in zip(s, CTRS))
        tail = s[-1]
        print(f"  floor {floor:.0%}: tail exposure {tail:.0%}, "
              f"aggregate ctr {agg:.4f}")
    print("\nreading: the first ten points of floor move the tail from")
    print("1% to 9% and cost 0.0021 aggregate CTR; the next ten move")
    print("it only to 15% and cost more (0.0027) per point of exposure.")
    print("The constraint curve is where the allocation decision lives -")
    print("how much relevance the platform is willing to spend on how")
    print("visible a tail.")


if __name__ == "__main__":
    main()
