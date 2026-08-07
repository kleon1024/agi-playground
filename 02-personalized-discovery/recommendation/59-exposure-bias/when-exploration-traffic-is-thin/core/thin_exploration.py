"""When exploration traffic is thin: random buckets fix the bias but
cover few items, so the corrected model still knows nothing about the
items the old model never showed.

Run:
    uv run python core/thin_exploration.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(47)
    m = 2000
    exposed = 120  # old policy shows a popular subset
    rows = 20000
    rnd_share = 0.02  # 2% of traffic explores
    seen = set()
    for _ in range(rows):
        if rng.random() < rnd_share:
            seen.add(rng.randrange(m))
        else:
            seen.add(rng.randrange(exposed))
    uncovered = m - len(seen)
    print("when exploration traffic is thin, read (coverage):")
    print(f"  catalogue size          {m}")
    print(f"  items ever seen in log  {len(seen)}")
    print(f"  items never exposed     {uncovered}  ({uncovered / m:.1%})")
    print()
    print("reading: 2% exploration across 20k rows reaches under 200 distinct")
    print("items in a 2,000-item catalogue, so the long tail stays invisible")
    print("to every correction. exploration fixes bias where it reaches; the")
    print("rest of the tail is what content-based recall (stage 01) exists for.")


if __name__ == "__main__":
    main()
