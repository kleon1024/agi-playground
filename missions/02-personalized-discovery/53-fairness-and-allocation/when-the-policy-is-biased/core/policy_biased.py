"""Policy is biased, read: the label carries the position it was
collected in.

Stage 53 detour: CTR logged at the top of the page is inflated by
position. Ranking on the raw estimate entrenches the position bias;
correcting for it reallocates exposure toward the items the raw
numbers starved.

Run:
    uv run python core/policy_biased.py
"""

from __future__ import annotations

# (item, logged ctr at its usual position, position-adjusted ctr)
ITEMS = [
    ("P1001", 0.048, 0.036),
    ("P1002", 0.041, 0.034),
    ("P1003", 0.026, 0.030),
    ("P1004", 0.022, 0.028),
]


def shares(ctrs: list[float]) -> list[float]:
    weights = [c ** 3 for c in ctrs]
    total = sum(weights)
    return [w / total for w in weights]


def main() -> None:
    raw = [item[1] for item in ITEMS]
    adjusted = [item[2] for item in ITEMS]
    raw_shares = shares(raw)
    adj_shares = shares(adjusted)
    print("policy is biased, read (exposure by item, raw vs adjusted ctr):")
    for item, raw_s, adj_s in zip(ITEMS, raw_shares, adj_shares):
        print(f"  {item[0]}: raw ctr {item[1]:.3f} exposure {raw_s:.0%} -> "
              f"adjusted ctr {item[2]:.3f} exposure {adj_s:.0%}")
    raw_tail = raw_shares[2] + raw_shares[3]
    adj_tail = adj_shares[2] + adj_shares[3]
    print("\nreading: the raw numbers hand most exposure to the items")
    print("that sat at the top of the page; the position-adjusted")
    print(f"numbers move the tail from {raw_tail:.0%} to {adj_tail:.0%} of")
    print("exposure. The bias is in the collection policy, and")
    print("correcting it is not fairness - it is measurement.")


if __name__ == "__main__":
    main()
