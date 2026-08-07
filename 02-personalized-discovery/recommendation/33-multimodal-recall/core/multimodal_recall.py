"""Multimodal recall, read: the cold item with a picture and no clicks.

Stage 33 is the frontier of cold-start: a VLM embeds image and text
into one space, so a brand-new item is retrievable from its content
before it has a single interaction. This script reads retrieval
coverage for cold items.

Run:
    uv run python core/multimodal_recall.py
    uv run python core/multimodal_recall.py --emit-log /tmp/modality-coverage-envelope.json

The `--emit-log` flag writes the audit cohort: 20 items — 10 head and
10 tail — with the modalities each item has vectors for. Head items
have both image and text vectors; tail items have exactly one, so they
are reachable through one surface only. The production path in
`prod/modality_coverage_audit.py` measures coverage per stratum, the
case-finding that shows which items a query of a given modality can
never see.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: items with the modality vectors they have. Head items
# carry both image and text vectors; tail items carry exactly one, so
# a query of the missing modality cannot reach them.
AUDIT_ITEMS = {
    "head": [
        {"name": "h1", "image": True, "text": True},
        {"name": "h2", "image": True, "text": True},
        {"name": "h3", "image": True, "text": True},
        {"name": "h4", "image": True, "text": True},
        {"name": "h5", "image": True, "text": True},
        {"name": "h6", "image": True, "text": True},
        {"name": "h7", "image": True, "text": True},
        {"name": "h8", "image": True, "text": True},
        {"name": "h9", "image": True, "text": True},
        {"name": "h10", "image": True, "text": True},
    ],
    "tail": [
        {"name": "t1", "image": True, "text": False},
        {"name": "t2", "image": True, "text": False},
        {"name": "t3", "image": True, "text": False},
        {"name": "t4", "image": True, "text": False},
        {"name": "t5", "image": True, "text": False},
        {"name": "t6", "image": False, "text": True},
        {"name": "t7", "image": False, "text": True},
        {"name": "t8", "image": False, "text": True},
        {"name": "t9", "image": False, "text": True},
        {"name": "t10", "image": False, "text": True},
    ],
}


def render() -> None:
    # (item, has image vector, has text vector, has interactions)
    items = [
        ("item_a", True, True, True),
        ("item_b", True, False, True),
        ("item_c", True, True, False),
        ("item_d", False, True, False),
        ("item_e", False, False, False),
    ]
    print("multimodal recall, read:")
    for name, image, text, interacted in items:
        vectors = []
        if image:
            vectors.append("image")
        if text:
            vectors.append("text")
        reachable = "yes" if vectors else "no"
        cold = "cold" if not interacted else "warm"
        print(f"  {name}: vectors {vectors or ['none']}, {cold}, reachable {reachable}")
    cold_with_vector = sum(
        1 for _, image, text, interacted in items if not interacted and (image or text)
    )
    cold_total = sum(1 for _, _, _, interacted in items if not interacted)
    print(f"  cold items retrievable: {cold_with_vector}/{cold_total}")
    print("\nreading: a cold item is only retrievable if its content")
    print("produces a vector. The VLM is the cold-start bridge: image and")
    print("text embeddings make the never-clicked item reachable, which")
    print("is the frontier version of stage 01's content understanding.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"items": AUDIT_ITEMS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
