"""The merges that build the vocabulary, read from the recorded BPE run.

Stage 01's BPE training recorded the merge sequence: early merges are
high-frequency characters and bigrams, late merges are rare words. This
script reads the record and lays out the progression.

Input (recorded, unchanged): ../runs/2026-07-26-bpe-16k.md

Run:
    uv run python core/merge_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-26-bpe-16k.md"
    ).read_text()
    print("BPE merges (recorded), read:")
    for row in re.findall(
        r"merge\s+(\d+)\s+(\d+),\s+(\d+)\s+-> '?([^']*)'?\s+\(x([\d,]+)\)", run
    ):
        print(f"  merge {row[0]:>6}: {row[1]},{row[2]} -> '{row[3]}' "
              f"(x{row[4]})")
    print("\nreading: the merge order is the vocabulary's logic — early merges")
    print("collapse frequent characters and bigrams, late merges keep rare")
    print("whole words, and the sequence is what the 16,384-vocab tokenizer")
    print("is built from.")


if __name__ == "__main__":
    main()
