"""The user's no, read: rejection flips a value-tree decision.

Stage 05's value tree trades user value against revenue. This script
shows what an explicit dislike signal does to one item's score and the
slate it was in.

Run:
    uv run python core/reject_read.py
"""

from __future__ import annotations


def main() -> None:
    # (item, user_value, revenue, weight_on_revenue)
    slate = [
        ("x", 0.8, 0.3, 0.5),
        ("y", 0.6, 0.9, 0.5),
        ("z", 0.5, 0.2, 0.5),
    ]
    print("rejection, read (value = value - weight * revenue):")
    for name, value, revenue, w in slate:
        score = value - w * revenue
        print(f"  {name}: value {value} revenue {revenue} -> score {score:.2f}")
    # The user rejects x: its user value drops to zero.
    print("  after user rejects x:")
    for name, value, revenue, w in slate:
        v = 0.0 if name == "x" else value
        score = v - w * revenue
        print(f"  {name}: value {v} revenue {revenue} -> score {score:.2f}")
    print("\nreading: one explicit negative rewrites the trade — the item")
    print("with the highest combined score can fall below the fold. The")
    print("value tree is only as current as the signals feeding it.")


if __name__ == "__main__":
    main()
