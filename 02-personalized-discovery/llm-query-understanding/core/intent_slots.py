"""LLM query understanding, read: the query parsed into intent and slots.

Stage 37 is the frontier of query understanding: an LLM parses a raw
query into a structured intent with slots, which is the key space
retrieval must serve. This script reads the parsed structure for three
queries.

Run:
    uv run python core/intent_slots.py
    uv run python core/intent_slots.py --emit-log /tmp/parse-envelope.json

The `--emit-log` flag writes the audit cohort: 10 queries — 5 head and
5 tail — with, per query, how many of 5 sampled parses agree on the top
intent, the parse quality of the majority parse, and how many slots sit
below the confidence threshold. The production path in
`prod/parse_audit.py` stratifies parse stability by head and tail, the
case-finding that shows which queries the LLM parse actually decides.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: parse stability over 5 samples per query. Head queries
# have a clear intent, so the samples agree and quality is high. Tail
# queries are genuine judgment calls — the same string can parse into
# different intents across samples, quality drops, and several slots
# sit below the confidence threshold.
AUDIT_QUERIES = {
    "head": [
        {"query": "cheap flights to tokyo", "agreement": 5, "samples": 5, "quality": 0.98, "low_conf_slots": 0},
        {"query": "weather in singapore", "agreement": 5, "samples": 5, "quality": 0.98, "low_conf_slots": 0},
        {"query": "restaurants near me open now", "agreement": 5, "samples": 5, "quality": 0.97, "low_conf_slots": 0},
        {"query": "flight from sin to nar", "agreement": 5, "samples": 5, "quality": 0.98, "low_conf_slots": 0},
        {"query": "book a hotel in kyoto", "agreement": 5, "samples": 5, "quality": 0.97, "low_conf_slots": 0},
    ],
    "tail": [
        {"query": "apple watch", "agreement": 3, "samples": 5, "quality": 0.62, "low_conf_slots": 2},
        {"query": "hotel booking credit", "agreement": 3, "samples": 5, "quality": 0.58, "low_conf_slots": 2},
        {"query": "check my balance", "agreement": 2, "samples": 5, "quality": 0.45, "low_conf_slots": 3},
        {"query": "reserve a table", "agreement": 3, "samples": 5, "quality": 0.60, "low_conf_slots": 2},
        {"query": "time in tokyo", "agreement": 2, "samples": 5, "quality": 0.52, "low_conf_slots": 3},
    ],
}


def render() -> None:
    parsed = [
        ("cheap flights to tokyo", "flight_search", {"origin": None, "dest": "tokyo", "max_price": "cheap"}),
        ("2 bedroom apartment rent", "housing_search", {"bedrooms": 2, "type": "apartment", "action": "rent"}),
        ("how do i return an item", "support", {"topic": "returns"}),
    ]
    print("llm query understanding, read (intent + slots):")
    for query, intent, slots in parsed:
        print(f"  '{query}' -> {intent} {slots}")
    print("\nreading: the raw string becomes a structured key space. A")
    print("missing slot (origin is None) is a decision point: retrieval")
    print("either broadens the query or asks for the slot — the empty-slot")
    print("detour shows the cost of guessing.")


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
