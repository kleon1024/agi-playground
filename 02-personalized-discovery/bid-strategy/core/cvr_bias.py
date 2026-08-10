"""The winner's-log audit: won auctions overstate CVR.

Stage 27 derives the bid as value times conversion rate. The audit
asks the case-finding question at production scale: what CVR does the
bidder actually see? A bidder only logs the auctions it won, and it
wins the auctions where its bid — hence its conversion estimate — was
high. If the estimate tracks true propensity, the won set is skewed to
high-propensity impressions, and the naive CVR from the winner's log
overstates the CVR the campaign will actually experience.

Simulation: 100,000 auctions (fixed seed). 90 percent of impressions
have propensity 0.012, 10 percent have propensity 0.08. The bidder's
estimate equals the true propensity (perfect discrimination), it bids
value ($5) times the estimate, and the auction price is uniform on
[0.058, 0.065] — so the low-propensity bid ($0.06) wins only the cheap
tail while the high-propensity bid ($0.40) wins everything.

Run:
    uv run python core/cvr_bias.py
"""

from __future__ import annotations

import random

N_AUCTIONS = 100_000
CONVERSION_VALUE = 5.0
LOW_P, HIGH_P = 0.012, 0.08
HIGH_SHARE = 0.10
PRICE_LO, PRICE_HI = 0.058, 0.065


def main() -> None:
    rng = random.Random(20260808)

    true_sum = 0.0
    wins = 0
    conv_naive = 0
    ipw_numerator = 0.0
    ipw_denominator = 0.0

    for _ in range(N_AUCTIONS):
        p = HIGH_P if rng.random() < HIGH_SHARE else LOW_P
        true_sum += p
        bid = CONVERSION_VALUE * p
        price = PRICE_LO + (PRICE_HI - PRICE_LO) * rng.random()
        if bid <= price:
            continue
        wins += 1
        converted = int(rng.random() < p)
        conv_naive += converted
        # Inverse-propensity correction: reweight each won observation
        # by 1 / P(win | impression). The bid is deterministic in p, so
        # the win probability is the price mass below the bid.
        if p == HIGH_P:
            win_prob = 1.0
        else:
            win_prob = max(0.0, (bid - PRICE_LO) / (PRICE_HI - PRICE_LO))
        ipw_numerator += converted / win_prob
        ipw_denominator += 1.0 / win_prob

    true_cvr = true_sum / N_AUCTIONS
    naive_cvr = conv_naive / wins
    corrected_cvr = ipw_numerator / ipw_denominator

    print("winner's-log audit: 100,000 auctions, fixed seed")
    print("90% of impressions convert at 0.012, 10% at 0.08;")
    print("the bidder wins where its bid — its estimate — was high\n")
    print(f"  {'CVR read':>22} {'CVR':>8} {'bid ($5 x CVR)':>15}")
    print(f"  {'true (all auctions)':>22} {true_cvr:>8.4f} "
          f"{CONVERSION_VALUE * true_cvr:>15.2f}")
    print(f"  {'naive (won auctions)':>22} {naive_cvr:>8.4f} "
          f"{CONVERSION_VALUE * naive_cvr:>15.2f}")
    print(f"  {'IPW-corrected':>22} {corrected_cvr:>8.4f} "
          f"{CONVERSION_VALUE * corrected_cvr:>15.2f}")
    print(f"\nwins logged: {wins} of {N_AUCTIONS}")
    print(
        f"overbid from naive CVR: "
        f"{CONVERSION_VALUE * naive_cvr / (CONVERSION_VALUE * true_cvr):.2f}x"
    )

    print("\nreading: the winner's log is a biased sample. The bidder")
    print("wins where its estimate was high, so the won set converts")
    print("better than the market — naive CVR overstates the campaign's")
    print("real rate, and the target-CPA bid overpays every auction it")
    print("actually wins. The fix is a selection correction (inverse")
    print("propensity by win rate) or a CVR model fit on the full")
    print("impression space, not just wins.")


if __name__ == "__main__":
    main()
