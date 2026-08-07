"""The cost-quality pairing, read from the recorded outcome report.

Stage 03's verdict pairs quality with cost — the generation must beat
frame-repeat AND fit the declared ceiling. This script reads the recorded
report and lays out the two halves of the verdict.

Input (recorded, unchanged): ../runs/2026-07-31-outcome-report.txt

Run:
    uv run python core/cost_quality.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    txt = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-outcome-report.txt"
    ).read_text()
    print("mission 08 outcome report (recorded), read:")
    for row in re.findall(
        r"(margin[^\n]*|ceiling[^\n]*|VERDICT[^\n]*|MET[^\n]*|"
        r"beats frame-repeat[^\n]*|8\.5%[^\n]*)", txt
    ):
        print(f"  {row.strip()}")
    print("\nreading: the verdict pairs cost with quality rather than")
    print("reporting either alone — mission.yaml's cost/quality-together")
    print("rule, which is the discipline the cost-first mission exists to")
    print("enforce.")


if __name__ == "__main__":
    main()
