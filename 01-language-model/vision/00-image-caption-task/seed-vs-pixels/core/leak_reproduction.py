"""Why a leakage guardrail checks pixels, not seeds — reproduced.

Stage 00's recorded run found 116 pixel-identical train/eval collisions
with disjoint seed ranges, then fixed them with rejection sampling — and the
rejection sampler silently emptied eval's single-shape bucket. This script
reproduces both defects on the stage's own generator: the naive adjacent-seed
split's collision count, and the fixed split's rejection count plus the
distortion it introduces.

Everything is imported from the stage's core; only the two splits are new.

Run:
    uv run python core/leak_reproduction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from generate_dataset import (
    check_disjoint,
    make_eval_set_disjoint_from,
    make_example,
)


def single_shape_count(examples: list[dict]) -> int:
    return sum(1 for ex in examples if len(ex["shapes"]) == 1)


def main() -> None:
    n_train, n_eval = 2000, 400
    train = [make_example(s) for s in range(n_train)]
    train_dupes = len(train) - len({ex["pixel_hash"] for ex in train})

    # naive: eval drawn from the next seeds, no rejection — the original leak
    naive_eval = [make_example(s) for s in range(n_train, n_train + n_eval)]
    naive_collisions = check_disjoint(train, naive_eval)

    # fixed: rejection sampling past seed 100000 — the stage's final pipeline
    fixed_eval, rejected = make_eval_set_disjoint_from(train, n_eval, 100_000)
    fixed_collisions = check_disjoint(train, fixed_eval)

    print(f"train={n_train} eval={n_eval}")
    print(f"train-internal pixel-hash duplicates: {train_dupes}")
    print(f"naive (adjacent seeds, no rejection): collisions={naive_collisions}")
    print(f"fixed (rejection past 100000): collisions={fixed_collisions}, rejected={rejected}")
    print(f"single-shape images: train={single_shape_count(train)}, "
          f"naive-eval={single_shape_count(naive_eval)}, fixed-eval={single_shape_count(fixed_eval)}")


if __name__ == "__main__":
    main()
