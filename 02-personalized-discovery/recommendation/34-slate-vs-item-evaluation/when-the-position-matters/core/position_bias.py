"""Position bias, read: clicks measure the slot, not the item.

Stage 34 evaluates slates, and clicks are the cheapest feedback a
served slate earns. This script reads why clicks lie about quality:
the probability of a click is the probability the user examines the
slot times the probability the item earns the click, so an item's
observed click rate depends on where it sits, not only on how good
it is.

The read serves three items in an order that is not relevance order
(a promoted item in slot one, the best item buried in slot three),
applies a per-slot examination probability, and compares the click
ranking against the relevance ranking.

Run:
    uv run python core/position_bias.py
"""

from __future__ import annotations


def main() -> None:
    # (item, relevance) and the served order plus per-slot examination.
    relevance = {"x": 0.95, "y": 0.90, "z": 0.80}
    served = ["y", "z", "x"]
    examine = [1.00, 0.60, 0.30]

    def click_prob(item: str, slot: int) -> float:
        return relevance[item] * examine[slot]

    print("position bias, read (click probability per served slot):")
    for slot, item in enumerate(served):
        print(
            f"  slot {slot + 1}: {item} relevance {relevance[item]:.2f} "
            f"x examine {examine[slot]:.2f} = click {click_prob(item, slot):.3f}"
        )
    click_order = sorted(served, key=lambda i: -click_prob(i, served.index(i)))
    relevance_order = sorted(served, key=lambda i: -relevance[i])
    print(f"  relevance best: {relevance_order[0]}; "
          f"most clicked: {click_order[0]}")
    print("\nreading: the best item (x, 0.95) sits in slot three and gets")
    print("clicked 0.285; the promoted item (y, 0.90) in slot one gets")
    print("clicked 0.900. Clicks rank y above x — an evaluation that")
    print("reads clicks as quality measures the slot, not the item.")
    print("De-bias for position (examination models, position-weighted")
    print("metrics) before clicks become labels or a verdict (Craswell")
    print("et al. 2008).")


if __name__ == "__main__":
    main()
