"""Blend bias, measured: what does the random start cost?

Stage 38's audit showed the naive blend credits team A with 59.2 percent
of clicked sessions even though the teams are equal, and the random
start lands at 49.7/50.3. This detour quantifies the trade instead of
asserting it: how the credited share spreads across repeated
experiments, where the interval centers at scale, and how many more
sessions the balanced design needs for the same confidence-interval
width. The inner loop draws one uniform per session and compares it
against the model's click mass, so thousands of experiments fit in the
run.

Run:
    uv run python core/blend_variance.py
"""

from __future__ import annotations

import math
import random

POSITION_PROBS = (0.30, 0.20, 0.14, 0.10, 0.07, 0.05)
TEAM_A = ("d1", "d3", "d5")
TEAM_B = ("d2", "d4", "d6")
NO_CLICK = 6


def blend(a_start: bool) -> list[str]:
    if a_start:
        return ["d1", "d2", "d3", "d4", "d5", "d6"]
    return ["d2", "d1", "d4", "d3", "d6", "d5"]


def credited_a_share(sessions: int, seed: int, balanced: bool) -> float:
    """Fraction of clicked sessions credited to team A.

    One uniform draw per session: below 0.14 is a no-click session, and
    the click mass above it is split between the two teams by which
    list was shown. With the A-start list, A's positions 1, 3, 5 carry
    click mass 0.51 and B's 0.35; with the B-start list the masses
    swap. The two lists are disjoint, so every click is unambiguous.
    """
    rng = random.Random(seed)
    a_credits = 0
    clicked = 0
    for _ in range(sessions):
        a_start = (not balanced) or rng.random() < 0.5
        a_mass = 0.51 if a_start else 0.35
        r = rng.random()
        if r < 0.14:
            continue  # no click: the mass beyond position 6
        clicked += 1
        if r < 0.14 + a_mass:
            a_credits += 1
    return a_credits / clicked


def summarize(name: str, shares: list[float], sessions: int) -> tuple[float, float]:
    mean = sum(shares) / len(shares)
    sd = math.sqrt(sum((s - mean) ** 2 for s in shares) / len(shares))
    lo, hi = mean - 1.96 * sd, mean + 1.96 * sd
    print(f"{name}: mean {mean:.1%} across {len(shares)} experiments of "
          f"{sessions} sessions each")
    print(f"  spread: SD {sd:.2%}, 95% of experiments land in "
          f"[{lo:.1%}, {hi:.1%}]")
    return mean, sd


def main() -> None:
    experiments, sessions = 2_000, 3_000
    print("blend bias, measured: what does the random start cost?")
    print(f"  position click probs: {' '.join(f'{p:.2f}' for p in POSITION_PROBS)}")
    print(f"  teams equal; proposals disjoint; {experiments} experiments x "
          f"{sessions} sessions, seed per experiment")
    print()

    naive_shares = [credited_a_share(sessions, seed, balanced=False)
                    for seed in range(experiments)]
    balanced_shares = [credited_a_share(sessions, seed, balanced=True)
                       for seed in range(experiments)]

    _, naive_sd = summarize("naive blend (team A starts every session)",
                            naive_shares, sessions)
    _, bal_sd = summarize("balanced blend (random start per session)",
                          balanced_shares, sessions)
    print()

    var_ratio = bal_sd**2 / naive_sd**2
    # Per-session outcome variance, exact from the model: a clicked
    # session credits A with probability 0.51/0.86 = 0.593 under the
    # A-start list and 0.35/0.86 = 0.407 under the B-start list.
    p_a_naive = 0.51 / 0.86
    var_naive = p_a_naive * (1.0 - p_a_naive)
    p_a_bal = 0.5 * p_a_naive + 0.5 * (1.0 - p_a_naive)
    var_bal = p_a_bal - p_a_bal**2
    var_ratio = var_bal / var_naive
    print("per-session outcome variance, exact from the model:")
    print(f"  naive {var_naive:.4f} vs balanced {var_bal:.4f}; the random")
    print(f"  start raises it by {var_ratio - 1.0:.1%}, so the same CI")
    print(f"  width needs {var_ratio - 1.0:.1%} more sessions "
          f"(empirical SDs above: {naive_sd:.2%} vs {bal_sd:.2%})")
    print()

    big = 200_000
    naive_big = credited_a_share(big, 11, balanced=False)
    bal_big = credited_a_share(big, 11, balanced=True)
    naive_ci = 1.96 * math.sqrt(var_naive / (big * 0.86))
    bal_ci = 1.96 * math.sqrt(var_bal / (big * 0.86))
    naive_sigma = (naive_big - 0.5) / math.sqrt(var_naive / (big * 0.86))
    print(f"bias at scale ({big} sessions, seed 11):")
    print(f"  naive: credited A share {naive_big:.1%} (95% CI "
          f"+/-{naive_ci:.2%})")
    print(f"  balanced: credited A share {bal_big:.1%} (95% CI "
          f"+/-{bal_ci:.2%})")
    print(f"  the naive interval excludes the true 50/50 by "
          f"{naive_sigma:.0f} standard errors — more traffic only pins")
    print("  the wrong center down more tightly")
    print()

    print("verdict: the random start removes a fixed bias the naive")
    print(f"blend cannot see — {naive_big - 0.5:.1%} of credited share")
    print("that more traffic pins down more tightly. The price is")
    print(f"small: {var_ratio - 1.0:.1%} more sessions for the same")
    print("interval width. Bias is dominant: a tight interval around")
    print("the wrong center is a confident wrong answer (Chapelle")
    print("et al., 2012, TOIS; Joachims et al., 2005, SIGIR; Radlinski")
    print("& Craswell, 2010, SIGIR).")


if __name__ == "__main__":
    main()
