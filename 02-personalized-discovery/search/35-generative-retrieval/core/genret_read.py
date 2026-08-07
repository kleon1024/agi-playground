"""Generative retrieval, read: the model emits document IDs directly.

Stage 35 is the frontier of retrieval: instead of scoring a candidate
set, a sequence model generates the document IDs most likely to answer
the query — retrieval without an index scan. This script reads a beam
search over a small ID space.

Run:
    uv run python core/genret_read.py
    uv run python core/genret_read.py --emit-log /tmp/genret-envelope.json

The `--emit-log` flag writes the audit cohort: a 20-query log — 10 head
and 10 tail — with the decode recall@5 and the emitted-ID precision per
query. The production path in `prod/genret_audit.py` stratifies decode
quality by head and tail, the case-finding that shows which queries the
generative path can actually decode.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: decode recall@5 (does the beam contain the relevant
# doc) and emitted-ID precision (do the emitted IDs exist) per query.
# Head queries decode perfectly; tail queries lose recall and emit
# nonexistent IDs — the decode is a trained behavior, and the tail is
# where training has the least evidence.
AUDIT_QUERIES = {
    "head": [
        {"query": "running shoes", "recall": 1.0, "precision": 1.0},
        {"query": "headphones", "recall": 1.0, "precision": 1.0},
        {"query": "wireless mouse", "recall": 1.0, "precision": 1.0},
        {"query": "usb cable", "recall": 1.0, "precision": 1.0},
        {"query": "phone case", "recall": 1.0, "precision": 1.0},
        {"query": "laptop stand", "recall": 1.0, "precision": 1.0},
        {"query": "coffee maker", "recall": 1.0, "precision": 1.0},
        {"query": "bluetooth speaker", "recall": 1.0, "precision": 1.0},
        {"query": "desk chair", "recall": 1.0, "precision": 1.0},
        {"query": "yoga mat", "recall": 1.0, "precision": 1.0},
    ],
    "tail": [
        {"query": "trail gaiters", "recall": 0.6, "precision": 0.8},
        {"query": "copper water bottle", "recall": 0.4, "precision": 0.6},
        {"query": "chalk bag", "recall": 0.8, "precision": 1.0},
        {"query": "shimano cleats", "recall": 0.4, "precision": 0.6},
        {"query": "raw denim", "recall": 0.6, "precision": 0.8},
        {"query": "dash cam", "recall": 0.2, "precision": 0.4},
        {"query": "espresso tamper", "recall": 0.6, "precision": 0.8},
        {"query": "spinning rod", "recall": 0.4, "precision": 0.6},
        {"query": "passport holder", "recall": 0.8, "precision": 1.0},
        {"query": "beard trimmer", "recall": 0.6, "precision": 0.8},
    ],
}


def render() -> None:
    # (doc id, generative score)
    ids = [("doc_17", 0.9), ("doc_03", 0.7), ("doc_42", 0.4), ("doc_09", 0.2)]
    print("generative retrieval, read (beam over doc IDs):")
    for doc_id, score in sorted(ids, key=lambda x: -x[1]):
        print(f"  {doc_id}: {score:.1f}")
    top2 = [d for d, _ in sorted(ids, key=lambda x: -x[1])[:2]]
    print(f"  beam top-2: {top2}")
    print("\nreading: the model emits the doc IDs directly, so there is no")
    print("index scan and no candidate generation step. The frontier cost")
    print("is decode latency and the risk of emitting IDs that do not")
    print("exist — the hallucination detour prices that.")


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
