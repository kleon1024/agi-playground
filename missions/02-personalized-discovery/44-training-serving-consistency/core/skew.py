"""Training-serving skew, read: the price the server sees is not the
price the model trained on.

Stage 44 introduces training-serving consistency. The training set is
built from logged features - what the world looked like when the
decision was made. Serving reads live features. When a logged feature
stops matching the live one, the offline ranking is honest for a world
that no longer exists.

Run:
    uv run python core/skew.py
"""

from __future__ import annotations

# Logged at decision time: what the model trained on.
LOGGED = [
    {"id": "P1001", "price": 49.0, "ctr": 0.042},
    {"id": "P1002", "price": 89.0, "ctr": 0.023},
    {"id": "P1003", "price": 19.0, "ctr": 0.018},
]

# Live at serve time, after a promo ends and prices rise.
LIVE_PRICE = {"P1001": 56.0, "P1002": 89.0, "P1003": 24.0}


def true_ctr(price: float) -> float:
    """The real click rate as a function of the price actually shown."""
    if price <= 20.0:
        return 0.018
    if price <= 30.0:
        return 0.030
    if price <= 55.0:
        return 0.042
    return 0.026


def main() -> None:
    print("training-serving skew, read:")
    print("  offline order (logged CTR):")
    offline = sorted(LOGGED, key=lambda row: row["ctr"], reverse=True)
    for row in offline:
        print(f"    {row['id']}: logged ctr {row['ctr']:.3f}")
    print("  live truth (CTR at the price actually served):")
    live = [
        {"id": row["id"], "ctr": true_ctr(LIVE_PRICE[row["id"]])}
        for row in LOGGED
    ]
    for row in sorted(live, key=lambda r: r["ctr"], reverse=True):
        print(f"    {row['id']}: live ctr {row['ctr']:.3f}")
    offline_winner = offline[0]["id"]
    live_winner = max(live, key=lambda r: r["ctr"])["id"]
    print(f"\nreading: offline says {offline_winner} wins; live reality")
    print(f"says {live_winner} wins. The logged price is the model's")
    print("world, and that world ended. Serving-time feature logging and")
    print("re-validation on live features are the fix, not a better model.")


if __name__ == "__main__":
    main()
