"""Shading error, audited: the estimate decides the net.

Stage 39's shading sweep assumed a uniform competitor on [0, 1] and
found the optimum at half the value. This audit asks the industrial
question that sweep skips: the competitor distribution is unobservable,
so the bidder shades against a belief, and the belief can be wrong. It
measures what a mis-estimated competitor distribution costs — the
bidder keeps bidding its believed-optimum 0.50 while the true
competition shifts, and the realized net is compared with the optimum
under the true distribution.

Run:
    uv run python core/shading_error.py
"""

from __future__ import annotations

import random

VALUE = 1.0
BELLEVED_BID = 0.50


def win_prob(bid: float, lo: float, hi: float) -> float:
    """Win probability for a bid against a uniform competitor on [lo, hi]."""
    return max(0.0, min(1.0, (bid - lo) / (hi - lo)))


def net_at(bid: float, lo: float, hi: float) -> float:
    return (VALUE - bid) * win_prob(bid, lo, hi)


def optimal_bid(lo: float, hi: float) -> float:
    """Optimal first-price bid against a uniform competitor on [lo, hi]."""
    if hi <= 0.0:
        return 0.0
    candidate = (VALUE + lo) / 2.0
    if candidate < lo:
        return lo
    if candidate > hi:
        return hi
    return candidate


def simulate_net(sessions: int, seed: int, lo: float, hi: float) -> float:
    """Realized net when the bidder always bids the believed 0.50."""
    rng = random.Random(seed)
    total = 0.0
    for _ in range(sessions):
        comp = lo + (hi - lo) * rng.random()
        if comp < BELLEVED_BID:
            total += VALUE - BELLEVED_BID
    return total / sessions


def main() -> None:
    sessions = 200_000
    print("shading error, audited: does the estimate decide the net?")
    print(f"  value {VALUE:.2f}; the bidder believes competitors are "
          f"uniform on [0, 1] and bids {BELLEVED_BID:.2f}")
    print(f"  Monte Carlo: {sessions} sessions per world, fixed seed")
    print()

    print("mis-specified world | win | realized net | optimal bid | "
          "optimal net | loss")
    worlds = [(0.0, 1.0), (0.3, 1.3), (0.0, 0.4)]
    for lo, hi in worlds:
        w = win_prob(BELLEVED_BID, lo, hi)
        realized = simulate_net(sessions, 7, lo, hi)
        b_star = optimal_bid(lo, hi)
        opt = net_at(b_star, lo, hi)
        loss = opt - realized
        name = f"U[{lo:.1f}, {hi:.1f}]"
        print(f"  {name:18s} | {w:.2f} | {realized:9.3f} | "
              f"{b_star:9.2f} | {opt:9.3f} | {loss:.3f}")
    print()

    print("belief-error sweep (truth U[d, 1+d], bidder still bids 0.50):")
    print("  d    | win | realized net | optimal bid | optimal net | loss")
    for d in (-0.3, -0.1, 0.0, 0.1, 0.3):
        lo, hi = d, 1.0 + d
        w = win_prob(BELLEVED_BID, lo, hi)
        realized = simulate_net(sessions, 7, lo, hi)
        b_star = optimal_bid(lo, hi)
        opt = net_at(b_star, lo, hi)
        loss = opt - realized
        print(f"  {d:+5.1f} | {w:.2f} | {realized:9.3f} | "
              f"{b_star:9.2f} | {opt:9.3f} | {loss:.3f}")
    print()

    print("reading: the loss is the square of the belief error divided")
    print("by four — a belief error of 0.3 costs 0.0225 per auction,")
    print("9 percent of the stage's optimal net of 0.25. Under-shading")
    print("against stronger competition loses wins (win 0.20);")
    print("over-shading against weaker competition wins everything but")
    print("overpays (win 1.00, net 0.50 against an optimum of 0.60).")
    print("The competitor distribution is unobservable, so the shade is")
    print("an estimate and the estimate's error lands directly in net")
    print("value (Google moved Ad Manager to unified first price in")
    print("2019; Vickrey 1961, J. Finance; Edelman, Ostrovsky &")
    print("Schwarz 2007, AER; Varian 2007, IJIO).")


if __name__ == "__main__":
    main()
