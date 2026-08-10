"""The split that leaks: what the 99.1% leak actually buys.

Stage 00's recorded MovieLens run showed the leak as two numbers: a time
split that leaks 0 of 1,223 test rows, and a random split that leaks
17,885 of 18,055 (99.1%). This script reads the recorded run's numbers and
lays out what the leak actually does to the popularity floor — the baseline
every later stage must beat — which moves between the two splits (0.0389 vs
0.0496 hit-rate@20).

Input (recorded, unchanged): ../runs/2026-07-30-movielens-split.md

Run:
    uv run python core/split_leak.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-movielens-split.md"
    ).read_text()

    def grab(pattern: str) -> str:
        m = re.search(pattern, run)
        assert m, f"pattern not found in recorded run: {pattern}"
        return m.group(1)

    leaks = re.findall(
        r"future leakage: (\d+/\d+) test rows precede a same-user train row", run
    )
    assert len(leaks) == 2, f"expected 2 leak counts, found {leaks}"
    time_leak, rand_leak = leaks
    pop_time = grab(r"time split:\s+([\d.]+)")
    pop_rand = grab(r"random split:\s+([\d.]+)")
    example = grab(r"(user 75[^\n]+)")

    print("the recorded MovieLens split, read:")
    print(f"  time split:   {time_leak} test rows leak the future")
    print(f"  random split: {rand_leak} test rows leak the future (99.1%)")
    print(f"  popularity hit-rate@20: time {pop_time}  random {pop_rand}")
    print(f"  concrete leak: {example}")
    print("\nreading: the leak is not a small corruption — it moves the")
    print("baseline itself, so comparing scores across splits compares")
    print("different experiments.")


if __name__ == "__main__":
    main()
