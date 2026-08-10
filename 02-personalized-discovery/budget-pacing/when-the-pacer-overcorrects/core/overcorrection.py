"""The overcorrecting pacer, read: feedback gain turns pacing into oscillation.

The variance detour shows a fixed cap. This read replaces the fixed cap
with a feedback controller that re-paces against cumulative deviation
from plan: cap_next = target + gain x (planned - actual). With a low
gain the controller is smooth; with a high gain it alternates between
flooding the auction and starving it — the campaign goes dark on hours
that still have demand.

Run:
    uv run python core/overcorrection.py
"""

from __future__ import annotations


def main() -> None:
    budget = 100.0
    hours = 12
    target = budget / hours
    # Demand alternates: a high hour that saturates the cap, then a low
    # hour the campaign should buy cheaply.
    traffic = [20.0, 2.0, 20.0, 2.0, 20.0, 2.0, 20.0, 2.0, 20.0, 2.0, 20.0, 2.0]

    def run(gain: float) -> tuple[list[float], int, float]:
        spent: list[float] = []
        cumulative = 0.0
        remaining = budget
        for h in range(hours):
            planned = target * (h + 1)
            cap = target + gain * (planned - cumulative)
            cap = max(0.0, min(cap, traffic[h]))
            cost = min(traffic[h], cap, remaining)
            spent.append(cost)
            cumulative += cost
            remaining -= cost
        dark = sum(1 for h in range(hours) if traffic[h] > 0.01 and spent[h] < 0.01)
        return spent, dark, cumulative

    print("overcorrection read: cap_next = target + gain x (planned - actual);")
    print("demand alternates 20 / 2. target per hour = 8.33\n")
    print(f"  {'gain':>5} {'total':>7} {'dark hrs':>9} {'hourly spend':>14}")
    for gain in (0.5, 1.0, 3.0):
        spent, dark, total = run(gain)
        row = " ".join(f"{s:>4.0f}" for s in spent)
        print(f"  {gain:>5.1f} {total:>7.1f} {dark:>9d} {row:>14}")

    print("\nreading: at gain 0.5 the controller spends something every hour")
    print("and buys the cheap low-demand hours. At gain 3.0 the correction")
    print("overshoots: the cap floods to 20 after any deficit, then clamps")
    print("to 0 after any surplus -- the campaign is dark six hours and")
    print("flooding six, oscillating around the plan it should track.")


if __name__ == "__main__":
    main()
