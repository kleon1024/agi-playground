"""The image-ID guardrail, read from the recorded real-photo dataset run.

Stage 03 rebuilt the task on real photographs, where the leakage guardrail
changes from pixel-hash disjointness to COCO image-id disjointness. This
script reads the recorded run and lays out the split and the guardrail.

Input (recorded, unchanged): ../runs/2026-08-01-real-photo-dataset.md

Run:
    uv run python core/id_guardrail_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-real-photo-dataset.md"
    ).read_text()
    print("the real-photo dataset build (recorded), read:")
    for row in re.findall(
        r"(train images\s+: [\d]+ \([\d]+ QA pairs\)|"
        r"eval images\s+: [\d]+ \([\d]+ QA pairs\)|"
        r"image-id overlap between train and eval[^\n]*|"
        r"images with >=1 scoreable QA pair[^\n]*)",
        run,
    ):
        print(f"  {row}")
    print("\nreading: real photographs essentially never collide by pixel hash,")
    print("so the guardrail moves to image-id disjointness — the same real image")
    print("must not appear in both splits, checked by COCO id, not by rendering.")


if __name__ == "__main__":
    main()
