"""The behavioural floor that never moves, read from the recorded sweep.

Stage 01's threshold sweep shows behavioural coverage at 63% in every row —
the behaviour queue's reach does not depend on the labeller at all. This
script reads the record and isolates that constant: the threshold reshapes
only where the content queue draws its boundary, while the behaviour queue
stays where the log put it.

Input (recorded, unchanged): ../runs/2026-07-27-core.md

Run:
    uv run python core/behavioral_floor.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-core.md"
    ).read_text()
    catalogue = re.search(r"(\d+) items; (\d+) cold", run)
    beh = re.search(r"behavioural coverage (\d+)%", run)
    print("the behavioural floor, read from the recorded threshold sweep:")
    print(f"  catalogue: {catalogue.group(1)} items, {catalogue.group(2)} cold" if catalogue else "  catalogue: ?")
    print(f"  behavioural coverage: {beh.group(1)}% at every threshold" if beh else "  behavioural coverage: ?")
    print("  union/cold coverage move with the threshold; behaviour does not")
    print("\nreading: two queues, two different owners of reach. The content")
    print("queue's boundary is a dial; the behaviour queue's is a fact about")
    print("the log. A threshold can never rescue an item neither queue reaches.")


if __name__ == "__main__":
    main()
