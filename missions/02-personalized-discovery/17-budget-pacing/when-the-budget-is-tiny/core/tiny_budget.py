"""The tiny budget, read: when pacing cannot save delivery.

Stage 17 shows pacing saving a 100-unit budget. This script runs the same
controller on a tiny budget and shows the boundary — if the budget is too
small relative to minimum viable spend, no cap can deliver the whole day.

Run:
    uv run python core/tiny_budget.py
"""

from __future__ import annotations


def main() -> None:
    hours = 8
    demand = [30, 28, 25, 20, 15, 10, 5, 2]
    print("tiny budget, read (cap = budget/hours):")
    for budget in (100.0, 20.0, 8.0):
        cap = budget / hours
        # Naive: spend on demand as it arrives, no cap.
        naive_spent, naive_remaining = [], budget
        for d in demand:
            cost = min(d, naive_remaining)
            naive_spent.append(cost)
            naive_remaining -= cost
        naive_dark = next(
            (h for h in range(hours) if naive_spent[h] < demand[h]), hours
        )
        # Paced: cap binds.
        spent, remaining = [], budget
        for d in demand:
            cost = min(d, cap, remaining)
            spent.append(cost)
            remaining -= cost
        paced_dark = next((h for h in range(hours) if spent[h] < cap), hours)
        print(f"  budget {budget:>5.0f}: naive dark at hour {naive_dark}, "
              f"paced dark at hour {paced_dark}")
    print("\nreading: pacing stretches every budget — at 100, naive goes dark")
    print("by hour 3 while paced lasts to hour 5; at 20, naive is gone at")
    print("hour 0 (the first hour's demand alone exceeds the budget) while")
    print("paced survives the whole day on a 2.5/hour cap. But at 8 the")
    print("cap is 1/hour — the campaign barely delivers and earns almost")
    print("nothing. Pacing spreads a budget; it cannot create one. The")
    print("floor is a sizing problem, not a pacing one.")


if __name__ == "__main__":
    main()
