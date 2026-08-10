"""When the zero matters, read: the empty page is the expensive failure.

Stage 24 measures search coverage. This script prices a zero-result
query: no click, no conversion, and a user who may leave.

Run:
    uv run python core/zero_matters.py
"""

from __future__ import annotations


def main() -> None:
    traffic = 100_000
    zero_rate = 0.08
    zero = int(traffic * zero_rate)
    abandonment = 0.6
    lost = int(zero * abandonment)
    print("zero-result cost, read:")
    print(f"  daily queries: {traffic:,}")
    print(f"  zero-result:   {zero:,} ({zero_rate:.0%})")
    print(f"  likely lost:   {lost:,} users (abandonment {abandonment:.0%})")
    print("\nreading: 8% of queries return nothing and 60% of those users")
    print("leave. The zero-result rate is not a log curiosity — it is a")
    print("coverage metric with a revenue shape, which is why it belongs")
    print("in the search report next to NDCG and MRR.")


if __name__ == "__main__":
    main()
