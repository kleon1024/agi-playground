"""Fairness and allocation, read: exposure is a budget the ranker
allocates.

Stage 53 introduces allocation. A click-optimal ranker gives most
exposure to the categories that click best. A fairness constraint
reserves a minimum share for the rest. The constraint costs some
aggregate CTR; the question is what the exposure buys.

Run:
    uv run python core/allocation.py
"""

from __future__ import annotations

CATEGORIES = [
    {"name": "audio", "ctr": 0.040},
    {"name": "video", "ctr": 0.032},
    {"name": "cable", "ctr": 0.022},
    {"name": "accessories", "ctr": 0.010},
]


def exposure_share(ctrs: list[float]) -> list[float]:
    """Exposure under top-k click ranking: winner-take-most."""
    weights = [c ** 3 for c in ctrs]
    total = sum(weights)
    return [w / total for w in weights]


def constrained_share(ctrs: list[float], floor: float) -> list[float]:
    """Give each category at least `floor`, renormalised."""
    shares = exposure_share(ctrs)
    for i in range(len(shares)):
        shares[i] = max(shares[i], floor)
    total = sum(shares)
    return [s / total for s in shares]


def main() -> None:
    ctrs = [c["ctr"] for c in CATEGORIES]
    print("fairness and allocation, read (exposure by category):")
    plain = exposure_share(ctrs)
    floored = constrained_share(ctrs, 0.10)
    plain_ctr = sum(s * c for s, c in zip(plain, ctrs))
    floor_ctr = sum(s * c for s, c in zip(floored, ctrs))
    print("  unconstrained:")
    for cat, share in zip(CATEGORIES, plain):
        print(f"    {cat['name']:<12} ctr {cat['ctr']:.3f} exposure {share:.0%}")
    print(f"    aggregate ctr: {plain_ctr:.4f}")
    print("  with a 10% per-category floor:")
    for cat, share in zip(CATEGORIES, floored):
        print(f"    {cat['name']:<12} ctr {cat['ctr']:.3f} exposure {share:.0%}")
    print(f"    aggregate ctr: {floor_ctr:.4f}")
    print("\nreading: the floor moves accessories from near-invisible to")
    print("a real share and costs a little aggregate ctr. Allocation is")
    print("a constraint on the ranking objective, and the price of the")
    print("constraint is measured, not assumed.")


if __name__ == "__main__":
    main()
