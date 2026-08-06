"""The PARTIAL verdict, read bullet by bullet.

Stage 05's outcome report returns PARTIAL on exactly one of seven bullets.
This script reads the recorded report text and prints the bullet-1
structure — the decisive/no-result/cannot-determine split that makes the
verdict PARTIAL rather than MET or NOT MET.

Input (recorded, unchanged): ../runs/2026-08-01-outcome-report.txt

Run:
    uv run python core/partial_read.py
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    txt = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-outcome-report.txt"
    ).read_text()
    bullet1 = txt.split("1. Beats the no-harness baseline", 1)[1].split(
        "2. Beats always-frontier", 1
    )[0]
    print("bullet 1 of the outcome report, read:")
    print(bullet1.strip())
    print("reading: PARTIAL is narrower than NOT MET — 6 of 7 bullets are")
    print("MET, and the one that is not names exactly which comparison is")
    print("missing, not a blanket failure.")


if __name__ == "__main__":
    main()
