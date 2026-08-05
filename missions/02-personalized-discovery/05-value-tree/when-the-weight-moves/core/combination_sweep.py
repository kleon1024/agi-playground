"""The weight IS the strategy: combination functions, measured on one set.

Stage 05's recorded run swept one weight and showed the slate reordering.
This script quantifies the mechanism on the same item set: how the ranking
flips as the satisfaction weight sweeps 0 to 1 under both combination
functions, and how the two functions disagree — additive treats objectives
as substitutes (a click-shaped item can still win), multiplicative treats
them as requirements (a near-zero satisfaction collapses that item).

Everything is imported from the stage's core.

Run:
    uv run python core/combination_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from value_tree import combine_additive, combine_multiplicative, make_items


def main() -> None:
    items = make_items(12, seed=42)

    print("12 items, 4 archetypes (0 = click-shaped, 1 = quality-shaped, else mixed)")
    print(f"{'w_sat':>5} {'additive top-1':>16} {'multiplicative top-1':>20}")
    for w_sat in (0.0, 0.33, 0.67, 1.0):
        w = {"click": 1 - w_sat, "completion": 0.0, "satisfaction": w_sat}
        add_best = max(items, key=lambda it: combine_additive(it.predictions, w))
        mul_best = max(items, key=lambda it: combine_multiplicative(it.predictions, w))
        print(f"{w_sat:>5.2f} {add_best.item_id:>16} {mul_best.item_id:>20}")

    w_half = {"click": 0.5, "completion": 0.0, "satisfaction": 0.5}
    print("\nat w_sat=0.5, the click-shaped item's rank under each function:")
    add_order = sorted(items, key=lambda it: -combine_additive(it.predictions, w_half))
    mul_order = sorted(items, key=lambda it: -combine_multiplicative(it.predictions, w_half))
    click_item = next(it for it in items if it.item_id == "item_0")
    print(f"  additive: rank {add_order.index(click_item) + 1}/{len(items)} "
          f"(score {combine_additive(click_item.predictions, w_half):.3f})")
    print(f"  multiplicative: rank {mul_order.index(click_item) + 1}/{len(items)} "
          f"(score {combine_multiplicative(click_item.predictions, w_half):.3f})")


if __name__ == "__main__":
    main()
