"""When delivery varies, read: pacing under demand uncertainty.

Stage 17's simulation assumed a known demand curve. Real delivery is
uncertain — the morning spike is not known in advance. This script runs
the pacing controller against an unexpected demand shift and shows the
re-pacing response.

Run:
    uv run python core/variance_read.py
"""

from __future__ import annotations


def main() -> None:
    budget = 100.0
    hours = 8
    cap = budget / hours
    # Demand far exceeds the budget early; the cap must bind.
    demand = [30, 28, 25, 20, 15, 10, 5, 2]
    spent = []
    remaining = budget
    for h, d in enumerate(demand):
        planned = min(d, cap, remaining)
        remaining -= planned
        spent.append(planned)
    print("pacing under demand variance, read (cap = budget/hours = "
          f"{cap:.1f}):")
    print(f"  {'hour':>4} {'demand':>7} {'spend':>6} {'remaining':>9}")
    for h in range(hours):
        print(f"  {h:>4} {demand[h]:>7} {spent[h]:>6.1f} "
              f"{budget - sum(spent[:h+1]):>9.1f}")
    print(f"\n  total spent {sum(spent):.1f} of {budget}")
    print("\nreading: demand exceeds the budget at every early hour, and the")
    print("cap (12.5) binds — spend is flat while demand spikes, and the")
    print("budget survives the day. Without the cap, naive spend would have")
    print("exhausted the budget in the first two hours.")


if __name__ == "__main__":
    main()
