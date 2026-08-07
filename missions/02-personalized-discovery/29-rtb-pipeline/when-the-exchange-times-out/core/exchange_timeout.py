"""The exchange times out, read: no bid, no fill, no revenue.

Stage 29's exchange must respond before the publisher's deadline. This
script reads the fill loss from exchange-side timeouts.

Run:
    uv run python core/exchange_timeout.py
"""

from __future__ import annotations


def main() -> None:
    requests = 1_000_000
    print("exchange timeout, read (1,000,000 requests):")
    for timeout_rate in (0.01, 0.05, 0.10):
        lost = int(requests * timeout_rate)
        print(f"  {timeout_rate:.0%} timeout: {lost:,} requests unfilled")
    print("\nreading: every timed-out request is a slot that runs without a")
    print("bid — the publisher's inventory, the exchange's revenue, and the")
    print("advertiser's reach all miss together. Timeout rate is a revenue")
    print("metric, not an availability footnote.")


if __name__ == "__main__":
    main()
