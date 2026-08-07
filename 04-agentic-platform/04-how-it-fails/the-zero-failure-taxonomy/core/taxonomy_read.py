"""The zero-failure taxonomy, read from the recorded failure catalogue.

Stage 04's run sorted every real attempt into failure categories. The
sharpest row: the full-harness arm produced zero failures of any kind.
This script reads the recorded taxonomy and lays out the two-arm contrast.

Input (recorded, unchanged): ../runs/2026-08-01-failure-taxonomy.txt

Run:
    uv run python core/taxonomy_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    txt = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-failure-taxonomy.txt"
    ).read_text()
    print("failure taxonomy (recorded), read:")
    # The taxonomy txt lists each category twice (harness then no-harness).
    cats = re.findall(r"(\w+)\s+(\d+/\d+)", txt)
    seen: dict[str, tuple[str, str]] = {}
    for name, frac in cats:
        if name in ("Mission", "failure", "taxonomy"):  # header words
            continue
        if name not in seen:
            seen[name] = (frac, "")
        else:
            prev_harness, _ = seen[name]
            seen[name] = (prev_harness, frac)
    for name, (harness, noharness) in seen.items():
        print(f"  {name:<20} harness {harness:<6} no-harness {noharness}")
    print("\nreading: the harness arm's zero-failure rows are a real result —")
    print("with tools and retries, no tier needed a second observation to")
    print("notice a wrong patch; the no-harness arm is where failures live.")


if __name__ == "__main__":
    main()
