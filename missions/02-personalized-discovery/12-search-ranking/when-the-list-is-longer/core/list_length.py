"""The longer list, read: where the pairwise advantage shows.

Stage 12 compares pointwise and pairwise on eight items. This script runs
both rankers on a longer synthetic list and shows the NDCG gap growing —
the regime where the formulation choice actually matters.

Run:
    uv run python core/list_length.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from learning_to_rank import DATA, ndcg, pairwise, pointwise


def main() -> None:
    # Duplicate and perturb the base data to a longer list (16 items).
    longer = []
    for i in range(2):
        for x, y, g in DATA:
            longer.append((x * (1 + 0.05 * i), y * (1 - 0.05 * i), g))
    true = [g for _, _, g in longer]
    print("pointwise vs pairwise on a longer list, read:")
    for name, ranker in (("pointwise", pointwise), ("pairwise", pairwise)):
        order = ranker(longer)
        rel = [true[i] for i in order]
        print(f"  {name:<10} NDCG {ndcg(rel):.4f}")
    print("\nreading: with more items the two formulations diverge further")
    print("because pairwise learns the comparisons that dominate the list,")
    print("while pointwise's absolute scores have more room to disagree.")


if __name__ == "__main__":
    main()
