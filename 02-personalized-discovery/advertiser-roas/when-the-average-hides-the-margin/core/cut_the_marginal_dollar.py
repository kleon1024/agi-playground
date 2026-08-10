"""Cut the marginal dollar first, audited: which dollar returns the least?

The stage audit shows average ROAS clearing the target while marginal
ROAS falls below it. This detour asks the decision consequence: when
the budget must be cut, which dollar goes first? Each dollar of spend
does not return the same revenue — the marginal dollar returns the
least, so a cut that prunes from the top saves the same money while
losing the least revenue, and lifts the average ROAS that remains.

Run:
    uv run python core/cut_the_marginal_dollar.py
"""

from __future__ import annotations

SPEND_LEVELS = [1000.0, 1500.0, 2000.0, 2500.0, 3000.0]
CONVERSIONS = [310, 403, 473, 523, 558]
AOV = 28.0


def main() -> None:
    print("cut the marginal dollar first, audited (aov $28, $500 increments):")
    print(" cut | spend cut | conversions lost | revenue lost | return per $ cut")
    for i in range(1, len(SPEND_LEVELS)):
        conv_lost = CONVERSIONS[i] - CONVERSIONS[i - 1]
        revenue_lost = conv_lost * AOV
        per_dollar = revenue_lost / (SPEND_LEVELS[i] - SPEND_LEVELS[i - 1])
        label = f"${SPEND_LEVELS[i-1]:.0f}-{SPEND_LEVELS[i]:.0f}"
        print(f" {label:>9} |        $500 |           {conv_lost:3d} | "
              f"       ${revenue_lost:5.0f} |            {per_dollar:5.2f}")
    total_lost = CONVERSIONS[-1] * AOV
    print(f" all 3000 |        $3000 |           558 |       ${total_lost:5.0f} | "
          f"            {total_lost / 3000.0:5.2f}")
    print()
    print("reading: cutting the top increment returns $1.96 per dollar")
    print("saved; cutting the first increment returns $5.21, and cutting")
    print("the whole budget returns the 5.21 average. The marginal dollar")
    print("is the first to go: a $500 cut from the top loses the least")
    print("revenue and lifts the average ROAS that remains, because the")
    print("dollar that returns the least is the one the budget should")
    print("have stopped at first.")


if __name__ == "__main__":
    main()
