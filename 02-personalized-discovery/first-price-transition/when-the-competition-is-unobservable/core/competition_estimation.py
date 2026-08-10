"""Competition unobservable: estimating the shade from censored wins.

Stage 39's audit priced a mis-estimated competitor distribution
(belief error d costs d^2 / 4 per auction). This detour asks where the
estimate comes from in the first place. In a second-price auction the
winner's payment reveals the competitor's bid on every win, so the
log estimates the distribution for free. In a first-price auction the
winner pays its own bid and learns nothing about the competitor — the
only signal is the win-rate curve, which the bidder must probe with
real bids, and each probe is an impression it risks overpaying for.

This script measures that estimation cost: the bidder probes K bids
with n trials each, fits a piecewise-linear CDF, and bids the optimum
against its estimate. The realized net is compared with the 0.25 the
truth (uniform competitor on [0, 1], value 1.0) allows.

Run:
    uv run python core/competition_estimation.py
"""

from __future__ import annotations

import random
from collections.abc import Callable

VALUE = 1.0
PROBES = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90)


def win_rate(rng: random.Random, bid: float, trials: int) -> float:
    """Fraction of trials where a uniform-on-[0,1] competitor bids lower."""
    wins = sum(1 for _ in range(trials) if rng.random() < bid)
    return wins / trials


def estimated_cdf(probe_bids: list[float], rates: list[float]) -> Callable[[float], float]:
    """Piecewise-linear CDF through the probed win rates."""

    def cdf(bid: float) -> float:
        if bid <= probe_bids[0]:
            return rates[0] * bid / probe_bids[0]
        for lo, hi, r_lo, r_hi in zip(
            probe_bids, probe_bids[1:], rates, rates[1:]
        ):
            if lo <= bid <= hi:
                frac = (bid - lo) / (hi - lo)
                return r_lo + frac * (r_hi - r_lo)
        return 1.0

    return cdf


def optimal_bid(cdf: Callable[[float], float]) -> float:
    """Bid that maximizes (value - bid) * win-prob on a fine grid."""
    best_bid, best_net = 0.0, 0.0
    for bid in (i / 1000 for i in range(1, 1001)):
        net = (VALUE - bid) * cdf(bid)
        if net > best_net:
            best_bid, best_net = bid, net
    return best_bid


def realized_net(rng: random.Random, bid: float, sessions: int) -> float:
    total = 0.0
    for _ in range(sessions):
        if rng.random() < bid:
            total += VALUE - bid
    return total / sessions


def main() -> None:
    print("competition unobservable: estimating the shade from censored wins")
    print(f"  value {VALUE:.2f}; truth: competitor uniform on [0, 1]")
    print("  second-price reveals the competitor bid on every win;")
    print("  first-price reveals nothing, so the bidder probes win rates")
    print()

    print("probe budget | estimated optimum | realized net | loss vs 0.25")
    for trials in (100, 1_000, 10_000, 100_000):
        rng = random.Random(21)
        rates = [win_rate(rng, bid, trials) for bid in PROBES]
        cdf = estimated_cdf(list(PROBES), rates)
        b_hat = optimal_bid(cdf)
        rng2 = random.Random(22)
        net = realized_net(rng2, b_hat, 200_000)
        print(f"  {trials:>10} | {b_hat:.2f}              | {net:.3f}      "
              f"| {0.25 - net:.3f}")
    print()

    print("second-price comparison (winner's log reveals competitor bids):")
    rng = random.Random(13)
    revealed = [rng.random() for _ in range(10_000)]
    truth_est = sum(1.0 for r in revealed if r < 0.50) / len(revealed)
    print("  second-price wins reveal the competitor bid directly;")
    print(f"  10,000 wins estimate P(competitor < 0.50) at "
          f"{truth_est:.4f} against truth 0.5000")
    print()

    print("reading: the estimate is the bottleneck, and first-price")
    print("makes it censored. Every probe bid is an impression the")
    print("bidder risks overpaying for, so probing is rationed and the")
    print("fitted curve carries noise — at 1,000 trials per probe the")
    print("estimated optimum wanders and the realized net loses to the")
    print("0.25 truth allows. The trade is probe traffic against")
    print("estimation error, and it is the audit's d^2 / 4 loss curve")
    print("measured from where the d actually comes from.")


if __name__ == "__main__":
    main()
