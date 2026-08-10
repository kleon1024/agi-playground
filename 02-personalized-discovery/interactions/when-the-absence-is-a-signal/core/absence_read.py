"""Absence as a signal, read: exposure decides what no-click means.

Stage 00 models interactions. This script separates two very different
zeros in a log: an item that was shown and not clicked (implicit
negative) and an item that was never shown (no information at all).

Run:
    uv run python core/absence_read.py
"""

from __future__ import annotations


def main() -> None:
    # (item, exposures, clicks)
    log = [
        ("A", 1000, 120),
        ("B", 1000, 4),
        ("C", 1000, 0),
        ("D", 0, 0),
    ]
    print("absence as a signal, read:")
    for name, exposures, clicks in log:
        if exposures == 0:
            print(f"  {name}: never shown -> no signal")
        elif clicks == 0:
            print(f"  {name}: shown {exposures}x, 0 clicks -> implicit negative")
        else:
            ctr = clicks / exposures
            print(f"  {name}: shown {exposures}x, {clicks} clicks -> ctr {ctr:.3f}")
    print("\nreading: a zero click after 1000 exposures is a real negative,")
    print("a zero with zero exposure is silence. Treating them alike")
    print("rewards never-shown items and punishes honest failures.")


if __name__ == "__main__":
    main()
