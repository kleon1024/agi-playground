"""The empty set that was two rules' fault, read from the recorded run.

Stage 07's run holds the sharpest interaction in the rule engine: the EU
regional rule and the safety rule each remove part of the set, and applied
together they empty it. This script reads the record and lays out the
per-rule counts and the joint failure.

Input (recorded, unchanged): ../runs/2026-07-27-core.md

Run:
    uv run python core/empty_set_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-core.md"
    ).read_text()
    print("rule-engine interactions (recorded), read:")
    for row in re.findall(
        r"(US request|EU regional|safety|Tightening the cap)[^.;\n]*",
        run,
    ):
        print(f"  {row.strip()}")
    print("\nreading: each rule alone leaves survivors; the joint application")
    print("empties the set. A rule engine's failure mode is interaction, not")
    print("any single rule — which is why precedence and the empty-set")
    print("check are part of the engine, not post-processing.")


if __name__ == "__main__":
    main()
