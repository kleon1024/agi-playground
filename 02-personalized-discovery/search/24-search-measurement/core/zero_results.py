"""Zero-result rate, read: the query the index cannot answer.

Stage 24 measures the search funnel from logs. This script reads the
zero-result rate and what it says about coverage.

Run:
    uv run python core/zero_results.py
"""

from __future__ import annotations


def main() -> None:
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


if __name__ == "__main__":
    main()
