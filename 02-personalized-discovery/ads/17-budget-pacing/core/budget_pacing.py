"""Budget pacing: delivering a day's ad budget evenly, not instantly.

An advertiser has a daily budget, and the platform must deliver it across
the day — spend everything in the first hour and the campaign is gone
when the evening traffic arrives. Pacing controls how much of the budget
is spent per time slice. This stage simulates a budget under naive
spending versus a paced schedule.

Run:
    uv run python core/budget_pacing.py
"""

from __future__ import annotations


def main() -> None:
    budget = 100.0
    hours = 12
    # Impressions per hour, front-loaded: the morning spike is real demand,
    # but it is not the whole day.
    traffic = [6.0, 5.5, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
    # The budget is 100 total, but the day needs 200 impressions of delivery
    # to be fully served — the budget is *scarce relative to demand*.
    demand_value = 2 * budget
    cost_per_impression = demand_value / sum(traffic)

    # Naive: spend on every impression as it arrives, no cap. The morning
    # spike consumes the budget, so the campaign is dark by mid-day.
    naive_spent = []
    naive_total = 0.0
    remaining_naive = budget
    for t in traffic:
        cost = min(t * cost_per_impression, remaining_naive)
        naive_spent.append(cost)
        naive_total += cost
        remaining_naive -= cost
    naive_exhaust_hour = next(
        (h for h in range(hours) if naive_spent[h] < traffic[h] * cost_per_impression),
        None,
    )

    # Paced: cap per-hour spend at budget/hours so delivery survives the day.
    cap = budget / hours
    paced = []
    remaining_paced = budget
    for t in traffic:
        cost = min(t * cost_per_impression, cap, remaining_paced)
        paced.append(cost)
        remaining_paced -= cost

    print("budget pacing, read:")
    print("  hour    naive    paced")
    for h in range(hours):
        print(f"  {h:>3}   {naive_spent[h]:>6.1f}   {paced[h]:>6.1f}")
    print(f"  total  {naive_total:.1f}   {sum(paced):.1f} (budget {budget})")
    if naive_exhaust_hour is not None:
        print(f"  naive exhausts at hour {naive_exhaust_hour} "
              f"(spent {sum(naive_spent[:naive_exhaust_hour+1]):.0f} of {budget})")
    print(f"  paced survives the day: {sum(paced):.1f} spent, "
          f"{remaining_paced:.1f} unused")
    print("\nreading: naive spends as fast as impressions arrive, so a")
    print("morning spike exhausts the budget before the evening demand;")
    print("pacing caps the per-hour spend so delivery survives the whole day.")


if __name__ == "__main__":
    main()
