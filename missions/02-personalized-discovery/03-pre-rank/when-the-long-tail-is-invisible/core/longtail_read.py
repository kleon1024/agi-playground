"""The long tail a proxy never surfaces, read from the recorded runs.

Stage 03's run compared cheap-proxy and popularity-only surface rates at
four seeds and a funnel-realistic scale. The sharpest row: popularity-only's
long-tail surface rate is 0.000 in every run. This script reads the record
and lays out why that zero is structural, not tuning.

Input (recorded, unchanged): ../runs/2026-07-30-longtail-surface-rate.md

Run:
    uv run python core/longtail_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-longtail-surface-rate.md"
    ).read_text()
    print("long-tail surface rate (recorded), read:")
    for row in re.findall(
        r"seed\s+(\d+)\s+([\d.]+)\s+([\d.]+) / ([\d.]+)\s+([\d.]+) / ([\d.]+)",
        run,
    ):
        seed, lt, proxy_ov, proxy_lt, pop_ov, pop_lt = row
        print(f"  seed {seed}: long-tail {lt} | proxy {proxy_ov}/{proxy_lt} "
              f"| popularity {pop_ov}/{pop_lt}")
    funnel = re.search(
        r"cheap proxy \(content \+ popularity\):.*?([\d.]+), long-tail ([\d.]+)",
        run,
    )
    if funnel:
        print(f"  funnel scale: cheap proxy overall {funnel.group(1)}, "
              f"long-tail {funnel.group(2)}")
    print("\nreading: popularity-only long-tail is 0.000 on every seed — a cold")
    print("item's popularity is noise, so it can never rank above a head item")
    print("on that signal alone. The zero is structural, not a tuning miss.")


if __name__ == "__main__":
    main()
