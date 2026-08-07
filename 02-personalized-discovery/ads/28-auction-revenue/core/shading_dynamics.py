"""The shading-dynamics audit: first-price revenue learns its way down.

Stage 28 compares first- and second-price revenue under one bid set.
The audit asks the dynamic question: what happens to first-price
revenue as bidders learn to shade? Bidders play a first-price auction
repeatedly; each round they move their bid function partway toward the
best response to the last round's observed competition, shading toward
the bid that maximizes (value - bid) x P(win). Truthful round 1 pays
the naive first-price revenue; as the shading learns, revenue falls
toward the symmetric equilibrium — for three uniform bidders, the
same expected revenue the second-price auction pays.

Simulation: 12 rounds of 300 auctions, three bidders, values iid
U(0,1), fixed seed, damping 0.4 on the bid function. Round 1 bids
truthfully.

Run:
    uv run python core/shading_dynamics.py
"""

from __future__ import annotations

import bisect
import random

T_ROUNDS = 12
R_AUCTIONS = 300
K_BIDDERS = 3
GRID = 100
DAMPING = 0.4


def best_response(value: float, sorted_hist: list[float]) -> float:
    """Maximize (v - b) * P(highest competing bid < b) over a bid grid."""
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


def main() -> None:
    rng = random.Random(20260808)
    value_grid = [(i + 0.5) / GRID for i in range(GRID)]
    bid_grid = list(value_grid)  # round 1 bids truthfully
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

    print("shading-dynamics audit: 12 rounds x 300 auctions, fixed seed")
    print("three bidders, values iid U(0,1); round 1 bids truthfully,")
    print("later rounds damped best responses to observed competition\n")
    print(f"  {'round':>6} {'mean revenue':>13}")
    for i, rev in enumerate(revenue_by_round, start=1):
        print(f"  {i:>6} {rev:>13.4f}")
    converged = sum(revenue_by_round[-3:]) / 3
    print(f"\nnaive round 1:       {revenue_by_round[0]:.4f}")
    print(f"converged (avg 10-12): {converged:.4f}")
    print("second-price revenue:   0.5000 (theoretical)")
    print(f"erosion: {(revenue_by_round[0] - converged) / revenue_by_round[0]:.0%}")

    print("\nreading: first-price revenue is a moving target. The naive")
    print("round pays the winner's value; as bidders learn the competition")
    print("they shade, and revenue falls toward the symmetric equilibrium —")
    print("for three uniform bidders, the same expected revenue the")
    print("second-price auction pays. The first-price advantage is a")
    print("transient, not a property: it exists only while bidders stay")
    print("naive.")


def bid_from_grid(value: float, bid_grid: list[float], value_grid: list[float]) -> float:
    """Nearest-grid-value bid for an auction draw."""
    idx = min(range(len(value_grid)), key=lambda i: abs(value_grid[i] - value))
    return bid_grid[idx]


if __name__ == "__main__":
    main()
