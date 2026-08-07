"""The slow bidder, read: the exchange decides in the meantime.

Stage 29's exchange waits for bids. This script reads what happens when a
bidder misses the deadline.

Run:
    uv run python core/slow_bidder.py
"""

from __future__ import annotations


def main() -> None:
    deadline_ms = 100.0
    bidders = {"a": 40.0, "b": 95.0, "c": 130.0}
    print("slow bidder, read (deadline 100 ms):")
    for name, ms in bidders.items():
        status = "bid in time" if ms <= deadline_ms else "TIMED OUT"
        print(f"  bidder {name}: {ms:.0f} ms -> {status}")
    print("\nreading: bidder c loses the auction not on price but on speed.")
    print("The timeout is a selection mechanism: bids that arrive late")
    print("cannot win, and a slow bidder is invisible to the exchange no")
    print("matter how good its price is. Latency is a bidder's cost of entry.")


if __name__ == "__main__":
    main()
