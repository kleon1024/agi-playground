"""The cache that misses together, read: synchronized refresh blows the p95.

Stage 08's serving path keeps a p95 budget. This script compares two
cache-refresh policies: all shards refresh at once (stampede) versus a
staggered refresh, and reads the tail.

Run:
    uv run python core/cold_cache_read.py
"""

from __future__ import annotations


def p95(times: list[float]) -> float:
    ordered = sorted(times)
    return ordered[int(len(ordered) * 0.95)]


def main() -> None:
    n = 100
    hit = 2.0
    miss = 50.0
    # Synchronized: one refresh hour, every request in that window misses.
    sync = [miss if 40 <= i < 60 else hit for i in range(n)]
    # Staggered: refreshes spread, so at most 2% of requests miss.
    stagger = [miss if i in (40, 90) else hit for i in range(n)]
    print("cold cache, read (100 requests, p95):")
    print(f"  synchronized refresh: p95 {p95(sync):.0f} ms")
    print(f"  staggered refresh:    p95 {p95(stagger):.0f} ms")
    print("\nreading: cache misses are cheap alone and expensive together.")
    print("A synchronized refresh converts a cold window into a p95")
    print("breach; staggering the same refreshes keeps the tail flat.")
    print("Tail latency is a scheduling property as much as a compute one.")


if __name__ == "__main__":
    main()
