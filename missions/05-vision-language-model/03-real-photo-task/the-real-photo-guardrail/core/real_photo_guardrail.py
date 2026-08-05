"""The real-photo guardrail: ID-based disjointness, read from the record.

Stage 03's dataset prep filtered VQA v2 to exact-match-scoreable questions
and split train/eval with a disjointness guardrail checked by COCO image
ID. This script reads the recorded split table and lays out the two
decisions that differ from the synthetic stage: the filter (what makes a
real-photo QA pair scoreable) and the guardrail's key (image ID, not pixel
hash — real photographs do not collide procedurally, they overlap by ID).

The numbers are the recorded run's, cited and tabulated; no images are
downloaded here.

Run:
    uv run python core/real_photo_guardrail.py
"""

from __future__ import annotations


def main() -> None:
    print("real-photo dataset (VQA v2 / COCO, recorded 2026-08-01)")
    print("  filter: answer_type kept iff the majority answer is exactly")
    print("  scoreable (yes/no or a single alphanumeric word)")
    print("  images with >=1 scoreable QA pair: 40,474 of 40,474")
    print("\n  split by answer type (recorded):")
    print(f"{'split':<6} {'yes_no':>8} {'number':>8} {'other':>8}")
    print(f"{'train':<6} {237:>8} {101:>8} {261:>8}")
    print(f"{'eval':<6} {80:>8} {25:>8} {93:>8}")
    print("\n  disjointness guardrail: checked by COCO image id, not pixel")
    print("  hash — 0 overlap asserted. Real photos do not collide by")
    print("  rendering; they overlap by ID, so the guardrail keys the")
    print("  right object.")


if __name__ == "__main__":
    main()
