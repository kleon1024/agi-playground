"""Query correction by edit distance, read: the typo that breaks BM25.

Stage 19 expands the query before retrieval. This script corrects a
misspelled query against a small dictionary and shows the retrieval
consequence of correcting or not.

Run:
    uv run python core/edit_distance.py
    uv run python core/edit_distance.py --emit-log /tmp/expansion-envelope.json

The `--emit-log` flag writes the audit cohort: a 24-query log — 12 head
queries the catalog already covers and 12 tail queries with vocabulary
mismatches — with the recall each query gets before and after expansion
and the irrelevant hits expansion adds. The production path in
`prod/expansion_audit.py` stratifies that log by head and tail, the
case-finding that shows where the expansion lift actually lives.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            ))
        prev = cur
    return prev[-1]


# Audit cohort: per-query recall@5 before and after expansion, and the
# irrelevant hits expansion adds. Head queries are already covered —
# expansion has nothing to recover and only adds noise. Tail queries
# carry the vocabulary mismatch that expansion repairs.
AUDIT_QUERIES = {
    "head": [
        {"query": "headphones", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "running shoes", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "wireless mouse", "base": 1.0, "expanded": 1.0, "noise": 2},
        {"query": "usb cable", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "phone case", "base": 1.0, "expanded": 1.0, "noise": 0},
        {"query": "laptop stand", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "coffee maker", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "bluetooth speaker", "base": 1.0, "expanded": 1.0, "noise": 2},
        {"query": "desk chair", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "yoga mat", "base": 1.0, "expanded": 1.0, "noise": 1},
        {"query": "backpack", "base": 1.0, "expanded": 1.0, "noise": 0},
        {"query": "keyboard", "base": 1.0, "expanded": 1.0, "noise": 1},
    ],
    "tail": [
        {"query": "heaphones", "base": 0.2, "expanded": 0.8, "noise": 0},
        {"query": "espreso machine", "base": 0.4, "expanded": 1.0, "noise": 1},
        {"query": "mech keyboard", "base": 0.2, "expanded": 0.6, "noise": 0},
        {"query": "standing desk pad", "base": 0.6, "expanded": 1.0, "noise": 0},
        {"query": "noise cancel headset", "base": 0.4, "expanded": 1.0, "noise": 1},
        {"query": "gaming chair", "base": 0.2, "expanded": 0.8, "noise": 0},
        {"query": "laptop sleeve 13", "base": 0.4, "expanded": 0.8, "noise": 1},
        {"query": "usb hub type c", "base": 0.2, "expanded": 0.6, "noise": 0},
        {"query": "phone tripod", "base": 0.6, "expanded": 1.0, "noise": 0},
        {"query": "bike phone mount", "base": 0.4, "expanded": 0.8, "noise": 1},
        {"query": "cable organizer", "base": 0.2, "expanded": 0.6, "noise": 0},
        {"query": "webcam cover", "base": 0.4, "expanded": 0.8, "noise": 0},
    ],
}


def render() -> None:
    vocab = ["headphones", "headsets", "shoes", "shorts", "flights"]
    query = "heaphones"
    matches = sorted(vocab, key=lambda w: edit_distance(query, w))
    print("query correction, read:")
    for word in matches:
        print(f"  {query} -> {word}: distance {edit_distance(query, word)}")
    corrected = matches[0]
    print(f"\n  corrected query: {corrected}")
    print("\nreading: BM25 on the raw query matches nothing in the index;")
    print("the corrected query matches the catalog. Correction is retrieval")
    print("pre-processing — its value is measured by the recall it recovers.")


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
