"""Two-sided feedback, audited: does the cut chase both sides away?

Stage 42's executed sweep prices the take rate against one
volume-response curve: volume falls as the rate rises, and revenue
peaks. This audit asks what that curve misses. A marketplace has two
sides, and the side that does not pay still responds. When the platform
raises the fee it charges sellers, sellers leave; the thinner selection
is worth less to buyers; buyers leave too; and transactions fall twice
over. The one-sided peak is not the two-sided peak.

Run:
    uv run python core/two_sided_feedback.py
"""

from __future__ import annotations

RATES = [rate / 100 for rate in range(1, 71)]


def one_sided_volume(rate: float) -> float:
    # Stage 42's curve: k = 1.6.
    return max(0.0, 1000 * (1.0 - 1.6 * rate))


def two_sided_volume(rate: float) -> float:
    # Sellers leave as the fee rises, with the same price sensitivity.
    sellers = max(0.0, 1000 * (1.0 - 1.6 * rate))
    # Buyers value the marketplace's selection: half the sellers keeps
    # half the buyers, which is the cross-side feedback the one-sided
    # curve skips.
    buyers = sellers
    # Transactions are the matches between the two sides.
    return sellers * buyers / 1000.0


def main() -> None:
    print("two-sided feedback, audited: does the cut chase both sides away?")
    print("  one-sided volume = 1000 x (1 - 1.6 x rate), stage 42's curve")
    print("  two-sided: sellers leave with the fee; buyers = sellers;")
    print("  transactions = sellers x buyers / 1000")
    print()
    print(" rate | one-sided volume | two-sided volume | two-sided revenue")
    for rate in (0.05, 0.15, 0.25, 0.35, 0.45):
        one = one_sided_volume(rate)
        two = two_sided_volume(rate)
        print(f" {rate:5.0%} |        {one:6.0f} |        {two:6.0f} | "
              f"          ${two * rate:6.1f}")
    print()
    one_peak = max(RATES, key=lambda r: r * one_sided_volume(r))
    two_peak = max(RATES, key=lambda r: r * two_sided_volume(r))
    print(f" one-sided revenue peak:   {one_peak:5.1%} / "
          f"${one_peak * one_sided_volume(one_peak):6.1f}")
    print(f" two-sided revenue peak:   {two_peak:5.1%} / "
          f"${two_peak * two_sided_volume(two_peak):6.1f}")
    at_one_peak = two_peak and two_sided_volume(one_peak) * one_peak
    print(f" two-sided revenue at the one-sided peak rate ({one_peak:4.1%}): "
          f"${at_one_peak:6.1f} "
          f"({(two_peak * two_sided_volume(two_peak) - at_one_peak)
              / (two_peak * two_sided_volume(two_peak)):5.1%} below peak)")
    print()
    print("reading: the one-sided curve prices the fee as if only the")
    print("paying side responds. The two-sided model lets the thinner")
    print("selection shrink the other side too, and the revenue peak")
    print(f"falls from {one_peak:4.1%} to {two_peak:4.1%} while revenue")
    print("at the old peak rate sits below the new one. The cut is a")
    print("two-sided price even when only one side pays it.")


if __name__ == "__main__":
    main()
