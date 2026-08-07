"""The two-environment null, read from the recorded full-chain report.

Stage 05's report elevated the null across two environments: the grid-world
and MiniGrid both collapsed at cold start. This script reads the recorded
report and lays out the two-environment shape of the verdict.

Input (recorded, unchanged): ../runs/2026-08-01-full-chain-report.md

Run:
    uv run python core/two_env_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-full-chain-report.md"
    ).read_text()
    print("mission 06 full-chain report (recorded), read:")
    for row in re.findall(
        r"(MET[^\n]*|NOT MET[^\n]*|null[^\n]*|two environments[^\n]*|"
        r"VERDICT[^\n]*|acceptance bar[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: the null repeated across two environments is a stronger")
    print("claim than one failure — the verdict is the pattern, not either")
    print("environment's number.")


if __name__ == "__main__":
    main()
