"""The beam that found the optimum, read from the recorded slate run.

Stage 06's run compared greedy, capped, and beam-searched slates against
the exhaustive optimum. The recorded numbers: greedy produced 3 sports
items, the cap enforced 2, and beam widths 1/2/3/9 all found the 2.2624
optimum. This script reads the record and lays out what the beam result
does and does not prove.

Input (recorded, unchanged): ../runs/2026-07-27-core.md

Run:
    uv run python core/beam_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-core.md"
    ).read_text()
    print("slate search (recorded), read:")
    greedy = re.search(r"greedy top-5 had (\d+) sports items", run)
    cap = re.search(r"category cap 2 returned ([\d.]+) utility", run)
    beam = re.search(r"matching the exhaustive optimum at beam widths ([\d, ]+)", run)
    ads = re.search(r"At ad loads 0/1/2: revenue was ([\d./]+) and displaced value was ([\d./]+)", run)
    if greedy:
        print(f"  greedy top-5: {greedy.group(1)} sports items (cap violated)")
    if cap:
        print(f"  category cap 2: utility {cap.group(1)}")
    if beam:
        print(f"  beam widths {beam.group(1)} all match the exhaustive optimum")
    if ads:
        print(f"  ad loads: revenue {ads.group(1)} vs displaced value {ads.group(2)}")
    print("\nreading: a narrow beam finding the optimum is not proof a beam is")
    print("enough — this constructed catalogue did not expose an approximation")
    print("loss. The displacement column is the price of the ad revenue, and")
    print("both are part of the same slate decision.")


if __name__ == "__main__":
    main()
