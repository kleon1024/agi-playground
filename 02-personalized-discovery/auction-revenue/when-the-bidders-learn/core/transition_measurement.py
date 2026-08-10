"""The bidders-learn detour: revenue measured during the transition
is not the revenue that settles.

Stage 28's audit shows first-price revenue erodes as bidders learn to
shade. This detour asks the measurement question a platform faces
after a rule change: when do you sample revenue? It runs the same
learning dynamics for 20 rounds and reads what a platform would
measure at each point after the transition to first price — round 1
(day one), the learning period, and the settled state — against the
second-price revenue the market returns to.

Run:
    uv run python core/transition_measurement.py
"""

from __future__ import annotations

import bisect
import random

T_ROUNDS = 20
R_AUCTIONS = 300
K_BIDDERS = 3
GRID = 100
DAMPING = 0.4
SECOND_PRICE_REVENUE = 0.5


def best_response(value: float, sorted_hist: list[float]) -> float:
    n = len(sorted_hist)
    best_bid = 0.0
    best_profit = 0.0
    for i in range(1, GRID + 1):
        b = value * i / GRID
        win_prob = bisect.bisect_left(sorted_hist, b) / n
        profit = (value - b) * win_prob
        if profit > best_profit:
            best_profit = profit
            best_bid = b
    return best_bid


def bid_from_grid(value: float, bid_grid: list[float], value_grid: list[float]) -> float:
    idx = min(range(len(value_grid)), key=lambda i: abs(value_grid[i] - value))
    return bid_grid[idx]


def main() -> None:
    rng = random.Random(20260808)
    value_grid = [(i + 0.5) / GRID for i in range(GRID)]
    bid_grid = list(value_grid)
    revenue_by_round: list[float] = []

    for round_idx in range(T_ROUNDS):
        round_revenue = 0.0
        round_competing: list[float] = []
        for _ in range(R_AUCTIONS):
            values = [rng.random() for _ in range(K_BIDDERS)]
            bids = [bid_from_grid(v, bid_grid, value_grid) for v in values]
            winner = max(range(K_BIDDERS), key=lambda i: bids[i])
            round_revenue += bids[winner]
            for i in range(K_BIDDERS):
                round_competing.append(
                    max(bids[j] for j in range(K_BIDDERS) if j != i)
                )
        revenue_by_round.append(round_revenue / R_AUCTIONS)
        sorted_hist = sorted(round_competing)
        if round_idx < T_ROUNDS - 1:
            bid_grid = [
                (1 - DAMPING) * old + DAMPING * best_response(v, sorted_hist)
                for v, old in zip(value_grid, bid_grid)
            ]

    print("transition-measurement audit: 20 rounds x 300 auctions, fixed seed")
    print("the market just moved to first price; bidders learn to shade\n")
    print(f"  {'measure at':>12} {'revenue read':>13} {'vs second price':>16}")
    for r in (1, 2, 4, 8, 14, 20):
        rev = revenue_by_round[r - 1]
        print(f"  {r:>12} {rev:>13.4f} "
              f"{'%+.1f' % ((rev - SECOND_PRICE_REVENUE) / SECOND_PRICE_REVENUE * 100):>15}%")
    settled = sum(revenue_by_round[-3:]) / 3
    print(f"\nsettled revenue (avg rounds 18-20): {settled:.4f}")
    print(f"second-price revenue: {SECOND_PRICE_REVENUE:.4f}")
    early_advantage = (revenue_by_round[0] - settled) / settled
    print(
        f"day-one read overstates settled revenue by "
        f"{early_advantage:.0%}"
    )

    print("\nreading: after a rule change, revenue is a function of when")
    print("you measure it. The day-one read (0.75) is the naive market;")
    print("the settled read is the equilibrium the bidders learn to. A")
    print("platform that decides on the early number over-invests in the")
    print("new rule; one that waits sees the erosion to second-price")
    print("revenue. The measurement window is part of the market-design")
    print("decision, not a reporting detail.")


if __name__ == "__main__":
    main()
