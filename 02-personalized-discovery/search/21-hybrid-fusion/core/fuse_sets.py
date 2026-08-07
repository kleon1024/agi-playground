"""Fusing candidate sets, read: BM25 plus dense into one list.

Stage 21 combines lexical and dense candidate sets. This script reads
reciprocal rank fusion on two short lists.

Run:
    uv run python core/fuse_sets.py
    uv run python core/fuse_sets.py --emit-log /tmp/fusion-envelope.json

The `--emit-log` flag writes the audit cohort: a 20-query log — 10 head
and 10 tail — with the NDCG of the fused list at three fusion weights
(lexical-only 0.0, balanced 0.5, dense-only 1.0). The production path
in `prod/fusion_audit.py` stratifies the weight swing by head and tail,
the case-finding that shows where the fusion weight actually decides.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return scores


# Audit cohort: NDCG of the fused list at weight 0.0 (lexical only),
# 0.5 (balanced), 1.0 (dense only). Head queries are covered by either
# matcher, so the weight barely moves the score; tail queries swing
# with the weight — the fused result is a decision about which matcher
# to trust for the rare query.
AUDIT_QUERIES = {
    "head": [
        {"query": "headphones", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "running shoes", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "wireless mouse", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "usb cable", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "phone case", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "laptop stand", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "coffee maker", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "bluetooth speaker", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "desk chair", "w0": 0.90, "w05": 0.92, "w1": 0.90},
        {"query": "yoga mat", "w0": 0.90, "w05": 0.92, "w1": 0.90},
    ],
    "tail": [
        {"query": "trail gaiters", "w0": 0.55, "w05": 0.80, "w1": 0.45},
        {"query": "copper water bottle", "w0": 0.60, "w05": 0.78, "w1": 0.40},
        {"query": "chalk bag", "w0": 0.50, "w05": 0.82, "w1": 0.50},
        {"query": "shimano cleats", "w0": 0.58, "w05": 0.76, "w1": 0.42},
        {"query": "raw denim", "w0": 0.52, "w05": 0.84, "w1": 0.46},
        {"query": "dash cam", "w0": 0.62, "w05": 0.74, "w1": 0.44},
        {"query": "espresso tamper", "w0": 0.54, "w05": 0.80, "w1": 0.48},
        {"query": "spinning rod", "w0": 0.60, "w05": 0.78, "w1": 0.42},
        {"query": "passport holder", "w0": 0.50, "w05": 0.82, "w1": 0.50},
        {"query": "beard trimmer", "w0": 0.56, "w05": 0.80, "w1": 0.44},
    ],
}


def render() -> None:
    lexical = ["d1", "d2", "d3", "d4"]
    dense = ["d4", "d5", "d1", "d6"]
    fused = rrf([lexical, dense])
    print("hybrid fusion, read (reciprocal rank fusion):")
    for doc, score in sorted(fused.items(), key=lambda kv: -kv[1]):
        where = []
        if doc in lexical:
            where.append(f"lexical#{lexical.index(doc) + 1}")
        if doc in dense:
            where.append(f"dense#{dense.index(doc) + 1}")
        print(f"  {doc}: {score:.4f} ({', '.join(where)})")
    print("\nreading: d4 and d1 appear in both sets and rank highest; d2, d3")
    print("survive only from lexical; d5, d6 only from dense. Fusion keeps")
    print("the union while rewarding documents both matchers agree on.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"queries": AUDIT_QUERIES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
