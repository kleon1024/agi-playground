"""Zero-result rate, read: the query the index cannot answer.

Stage 24 measures the search funnel from logs. This script reads the
zero-result rate and what it says about coverage.

Run:
    uv run python core/zero_results.py
    uv run python core/zero_results.py --emit-log /tmp/measure-envelope.json

The `--emit-log` flag writes the audit cohort: the search funnel over
four slices — device crossed with query stratum — with queries,
zero-result, click, and conversion counts per slice. The production
path in `prod/measure_audit.py` compares each slice with the aggregate,
the case-finding that catches the funnel metric hiding a collapsed
slice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: per-slice funnel counts. The mobile-tail slice carries
# the failure — a 25% zero-result rate and 0.2% conversion — while the
# aggregate over all slices looks normal.
AUDIT_SLICES = [
    {"slice": "desktop-head", "queries": 10_000, "zero": 200, "click": 4_500, "conv": 200},
    {"slice": "desktop-tail", "queries": 2_000, "zero": 160, "click": 760, "conv": 30},
    {"slice": "mobile-head", "queries": 12_000, "zero": 480, "click": 4_800, "conv": 216},
    {"slice": "mobile-tail", "queries": 3_000, "zero": 750, "click": 660, "conv": 6},
]


def render() -> None:
    queries = {
        "headphones": 0,
        "wireless earbuds": 0,
        "heaphones": 0,
        "bluetooth speaker": 3,
    }
    total = len(queries)
    zero = sum(1 for v in queries.values() if v == 0)
    print("zero-result rate, read:")
    print(f"  {zero}/{total} queries return nothing")
    print(f"  zero-result rate: {zero / total:.1%}")
    print("\nreading: two of the four zeros are catalog gaps (no earbuds,")
    print("no misspelled-word correction), one is a vocabulary miss. The")
    print("rate is a coverage signal: every zero is a query the index")
    print("cannot answer, and the breakdown says which fix each needs.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"slices": AUDIT_SLICES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
