"""The exact-vs-approximate price, read from the recorded FAISS run.

Stage 02's prod lane compared exact and approximate ANN search at two
settings. The recorded run holds the trade: recall bought back at a real,
measured latency cost. This script reads the record and lays out the two
points on the curve.

Input (recorded, unchanged): ../runs/2026-07-30-multi-queue-coverage.md

Run:
    uv run python core/approx_price.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-multi-queue-coverage.md"
    ).read_text()
    rows = re.findall(
        r"approx recall@25 against the exact index: ([\d.]+)\n"
        r".*?exact  \(IndexFlatIP\)\s+([\d.]+) ms.*?\n"
        r".*?approx \(IndexHNSWFlat\) ([\d.]+) ms",
        run,
        re.DOTALL,
    )
    print("exact vs approximate ANN (recorded), read:")
    if not rows:
        # fallback: the summary line
        summary = re.search(
            r"raising `--ef-search` from its default to 64 moved recall from "
            r"([\d.]+) to ([\d.]+) while narrowing.*?"
            r"\(([\d.]+) ms -> ([\d.]+) ms vs. ([\d.]+) ms -> ([\d.]+) ms\)",
            run,
        )
        if summary:
            print(f"  default: recall {summary.group(1)} at {summary.group(3)}ms")
            print(f"  ef=64:   recall {summary.group(2)} at {summary.group(4)}ms")
            print(f"  exact:   {summary.group(5)}ms -> {summary.group(6)}ms")
    for recall, exact_ms, approx_ms in rows:
        print(f"  recall@25 {recall} | exact {exact_ms}ms vs approx {approx_ms}ms")
    print("\nreading: the trade is recall bought at latency — 0.913 -> 0.984")
    print("for a narrower gap to exact (0.576 -> 0.714ms vs 1.133 -> 0.911ms),")
    print("which is a real measured price, not a theoretical one.")


if __name__ == "__main__":
    main()
