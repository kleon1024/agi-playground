"""The shuffle that did not move the score, read from the recorded run.

Stage 03's run compared shuffled, chronological-unpurged, and purged
walk-forward evaluation. The recorded numbers show a rule whose score is
the same with and without purge — a negative result that is itself the
lesson. This script reads the record and lays out the three paths.

Input (recorded, unchanged): ../runs/2026-07-27-walk-forward.md

Run:
    uv run python core/shuffle_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-walk-forward.md"
    ).read_text()
    print("walk-forward evaluation paths (recorded), read:")
    for row in re.findall(
        r"(shuffled-invalid out-of-fold Sharpe [\d.]+|"
        r"chronological-unpurged [\d.]+|purged-five-day/gapped-five-day [\d.]+|"
        r"14-trial teaching deflation was [\d.]+)",
        run,
    ):
        print(f"  {row}")
    note = re.search(r"(the recovered implementation never used its training indices[^.]*)", run)
    if note:
        print(f"\n  note: {note.group(1)}.")
    print("\nreading: this rule's score is the same with and without purge — not")
    print("proof leakage is harmless, but evidence the rule did not use the")
    print("training indices. A different rule could leak; the comparison is")
    print("the point, not the number.")


if __name__ == "__main__":
    main()
