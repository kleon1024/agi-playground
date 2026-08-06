"""The calibration that decides, read from the recorded fine-rank run.

Stage 04's run measured negative transfer and calibration on the click
head. The recorded ECE numbers — before and after Platt scaling, at two
trunk sizes — show what calibration actually buys and where it does not
reach. This script reads the record and lays out the two panels.

Input (recorded, unchanged): ../runs/2026-07-30-negative-transfer-and-calibration.md

Run:
    uv run python core/calibration_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-negative-transfer-and-calibration.md"
    ).read_text()
    print("fine-rank calibration and negative transfer (recorded), read:")
    for panel in re.finditer(
        r"trunk hidden=(\d+), epochs=(\d+), lr=[\d.]+\n\n"
        r"negative transfer:.*?\n"
        r"task\s+naive\s+balanced\n"
        r"(.*?)\n"
        r"calibration \(click head, 400 held-out examples\):\n"
        r"\s+ECE before Platt scaling\s+([\d.]+)\n"
        r"\s+ECE after  Platt scaling\s+([\d.]+)",
        run,
        re.DOTALL,
    ):
        hidden, epochs, tasks, ece_before, ece_after = panel.groups()
        print(f"  trunk hidden={hidden} epochs={epochs}:")
        print(f"    {tasks.replace(chr(10), chr(10)+'    ')}")
        print(f"    ECE {ece_before} -> {ece_after} (Platt)")
    print("\nreading: calibration is not a metric-improvement pass — the value")
    print("tree downstream does arithmetic on these probabilities, and ECE is")
    print("what keeps the arithmetic honest. The dwell row's recovery (naive")
    print("0.658/-0.080 -> balanced 0.803/0.809) is the negative-transfer half.")


if __name__ == "__main__":
    main()
