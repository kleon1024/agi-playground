"""Marginal versus average ROAS, audited: does the average hide the margin?

Stage 54's executed lifecycle shows ROAS decaying as spend stays flat.
This audit asks the industrial question that average ROAS skips: the
advertiser scales at the margin, and the average return can clear the
target while the marginal dollar is already below it. It splits spend
into increments, measures average and marginal ROAS at each spend
level, and reads where the two disagree with the budget decision.

Run:
    uv run python core/marginal_roas.py
"""

from __future__ import annotations

SPEND_LEVELS = [1000.0, 1500.0, 2000.0, 2500.0, 3000.0]
CONVERSIONS = [310, 403, 473, 523, 558]
AOV = 28.0
TARGET_ROAS = 5.0


def average_roas(spend: float, conversions: int) -> float:
    return AOV * conversions / spend


def marginal_roas(prev_spend: float, spend: float, prev_conv: int, conv: int) -> float:
    return AOV * (conv - prev_conv) / (spend - prev_spend)


def main() -> None:
    print("marginal versus average ROAS, audited (aov $28, target 5.0):")
    print(" spend | conversions | average ROAS | marginal ROAS over last increment")
    for i, spend in enumerate(SPEND_LEVELS):
        avg = average_roas(spend, CONVERSIONS[i])
        if i == 0:
            marg = float("nan")
            marg_str = "    -"
        else:
            marg = marginal_roas(SPEND_LEVELS[i - 1], spend, CONVERSIONS[i - 1],
                                 CONVERSIONS[i])
            marg_str = f"{marg:7.2f}"
        print(f" ${spend:5.0f} |        {CONVERSIONS[i]:3d} |        {avg:7.2f} | "
              f"{marg_str}")
    last_avg = average_roas(SPEND_LEVELS[-1], CONVERSIONS[-1])
    last_marg = marginal_roas(SPEND_LEVELS[-2], SPEND_LEVELS[-1],
                              CONVERSIONS[-2], CONVERSIONS[-1])
    print()
    print(f"reading: average ROAS stays above the target of {TARGET_ROAS:.1f} at")
    print(f"every spend level ({last_avg:.2f} at $3,000), while the marginal")
    print(f"dollar falls below it after the first increment (marginal {last_marg:.2f}")
    print("on the last $500). The average hides the margin: a budget")
    print("decided on average ROAS keeps spending where the next dollar")
    print("already loses against the target.")


if __name__ == "__main__":
    main()
