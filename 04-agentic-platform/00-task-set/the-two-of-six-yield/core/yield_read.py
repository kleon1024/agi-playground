"""The two-of-six yield, read from the recorded task-mining runs.

Stage 00 mined task sets from two histories: this repository's (private)
and more-itertools' (public). The recorded runs share one finding: how few
candidates survive fail-at-base/pass-at-gold. This script reads both
records and lays out the yields side by side.

Inputs (recorded, unchanged): ../runs/2026-07-29-private-task-set.md and
../runs/2026-08-01-public-task-set.md

Run:
    uv run python core/yield_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    private = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-29-private-task-set.md"
    ).read_text()
    public = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-public-task-set.md"
    ).read_text()

    priv_cand = re.search(r"(\d+) of (\d+) candidates", private)
    pub_cand = re.search(r"(\d+) of (\d+),", public)
    priv_commits = re.search(r"from (\d+) commits", private)
    pub_commits = re.search(r"runs to (\d+) commits", public)
    print("task-mining yield (recorded), read:")
    print(f"  private ({priv_commits.group(1)} commits): "
          f"{priv_cand.group(1)} of {priv_cand.group(2)} candidates survived" if priv_cand else "  private: ?")
    print(f"  public ({pub_commits.group(1)} commits): "
          f"{pub_cand.group(1)} of {pub_cand.group(2)} candidates survived" if pub_cand else "  public: ?")
    print("\nreading: the yield is the finding — most commits that look like")
    print("fixes do not survive fail-at-base/pass-at-gold, which is why the")
    print("verification step, not the mining, is what makes a task real.")


if __name__ == "__main__":
    main()
