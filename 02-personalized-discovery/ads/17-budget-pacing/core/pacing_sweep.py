"""The cap-tightness audit: under-delivery vs late-day loss.

The stage run paces with cap = budget/hours. The audit asks the
case-finding question: how tight should that cap be? It sweeps a
multiplier on the cap over a demand curve with a front-loaded morning and
an evening burst, and reports total spend, late-window spend, and dark
hours per multiplier. A cap that is too tight under-delivers; a cap that
is too loose exhausts the budget before the evening demand arrives.

Run:
    uv run python core/pacing_sweep.py
"""

from __future__ import annotations


def main() -> None:
    budget = 100.0
    hours = 12
    # Demand per hour: front-loaded morning, then an evening burst at
    # hours 9-10. The burst is where the loose cap loses.
    traffic = [5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 3.5, 3.0, 2.0]
    demand_value = 2 * budget
    cost_per_impression = demand_value / sum(traffic)
    late_start = 9

    def run(mult: float) -> list[float]:
        cap = mult * budget / hours
        spent: list[float] = []
        remaining = budget
        for t in traffic:
            cost = min(t * cost_per_impression, cap, remaining)
            spent.append(cost)
            remaining -= cost
        return spent

    print("cap-tightness audit: budget 100, 12 hours, demand front-loaded")
    print("with an evening burst (hours 9-10). cap = multiplier x budget/hours\n")
    print(f"  {'mult':>5} {'total':>7} {'late 9-11':>10} {'dark hrs':>9}")
    for mult in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
        spent = run(mult)
        total = sum(spent)
        late = sum(spent[late_start:])
        dark = sum(
            1
            for h in range(hours)
            if traffic[h] * cost_per_impression > 0.01 and spent[h] < 0.01
        )
        print(f"  {mult:>5.2f} {total:>7.1f} {late:>10.1f} {dark:>9d}")

    print("\nreading: at mult 0.5 the cap is so tight that half the budget")
    print("is never spent (under-delivery). At mult 1.5+ the budget dies")
    print("before the evening burst, and late-window delivery collapses to")
    print("0.0 with dark hours at the end of the day. The trade -- unspent")
    print("budget against missed evening demand -- is what cap tuning")
    print("optimizes, and late-window delivery is the metric that catches")
    print("the loose cap before the advertiser does.")


if __name__ == "__main__":
    main()
