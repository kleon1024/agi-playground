"""Label arrives late, read: a training cut taken now only sees the
labels that arrived early.

Stage 44 detour: conversions are logged with a delay. A training set
built from what is available now over-samples the labels that arrived
fast and under-counts the slow ones, biasing the model toward the
items whose conversions are quick to observe.

Run:
    uv run python core/label_late.py
"""

from __future__ import annotations

# (item, clicks, conversions, delay_hours)
ROWS = [
    ("P1001", 500, 20, 2),
    ("P1002", 400, 12, 8),
    ("P1003", 300, 9, 14),
]


def main() -> None:
    print("label arrives late, read (cut at hour 6, labels need delay):")
    print("  item   clicks  total conversions  visible at cut  estimate")
    for item_id, clicks, conversions, delay in ROWS:
        visible = conversions if delay <= 6 else 0
        rate = conversions / clicks
        visible_rate = visible / clicks
        print(f"  {item_id}   {clicks:>5}  {conversions:>14}  "
              f"{visible:>13}  {visible_rate:.4f} (true {rate:.4f})")
    print("\nreading: P1002 and P1003 converted slowly, so the cut at")
    print("hour 6 sees zero of their labels and estimates 0.0000.")
    print("The model trains on the fast-converting items only - the")
    print("label arrival delay is a sampling bias, and the fix is to")
    print("hold out the unconfirmed window, not to trust the cut.")


if __name__ == "__main__":
    main()
