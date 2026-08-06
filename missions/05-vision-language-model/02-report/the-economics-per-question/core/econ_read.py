"""The per-question economics, read from the recorded hosted-API run.

Stage 02's report compared three pathways, and the economics are part of
the build-vs-buy verdict: the hosted API cost $0.00128/question. This
script reads the recorded report and lays out the per-question cost and
the training cost it is measured against.

Input (recorded, unchanged): ../runs/2026-07-31-hosted-api-full.md

Run:
    uv run python core/econ_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-hosted-api-full.md"
    ).read_text()
    print("the hosted-API economics (recorded), read:")
    total = re.search(r"Real dollar cost \| .*?\\?\$([\d.]+) total, \\?\$([\d.]+)/question", run)
    if total:
        print(f"  hosted API: ${total.group(1)} total, "
              f"${total.group(2)}/question (from usage.cost)")
    vision = re.search(r"(overall exact-match[^\n]*)", run)
    if vision:
        print(f"  {vision.group(1)}")
    print("\nreading: the per-question price is the build-vs-buy floor — any")
    print("nonzero per-question cost already exceeds the $0 training cost,")
    print("so the entire tradeoff is on the accuracy axis.")


if __name__ == "__main__":
    main()
