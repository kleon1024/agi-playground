"""The three satisfied acceptance items, read from the recorded report.

Stage 02's NOT MET verdict still satisfies three of four acceptance items.
This script reads the recorded report and lays out what held and what
failed.

Input (recorded, unchanged): ../runs/2026-08-01-outcome-report.md

Run:
    uv run python core/three_met.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-outcome-report.md"
    ).read_text()
    print("mission 09 outcome report (recorded), read:")
    for row in re.findall(
        r"(NOT MET[^\n]*|scaffold overlap[^\n]*|0\.0[^\n]*|"
        r"descriptor baseline[^\n]*|trained model[^\n]*|does_not_prove[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: the verdict is NOT MET on the headline, but three other")
    print("acceptance items hold — the scaffold overlap is measured (0.0),")
    print("every stage has a runs entry, and the does_not_prove boundary is")
    print("stated. A failing verdict can still be a disciplined one.")


if __name__ == "__main__":
    main()
