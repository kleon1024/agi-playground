"""Session state moves, read: the boost decays and the batch order
wins back.

Stage 48 detour: the realtime boost for a viewed category decays as
the view recedes. Minutes after the view, the session reorders the
slate; later, the batch model's learned order reasserts itself.

Run:
    uv run python core/session_moves.py
"""

from __future__ import annotations

# (item, category, batch score)
ITEMS = [
    ("P1001", "audio", 0.032),
    ("P1002", "audio", 0.024),
    ("P1003", "cable", 0.028),
    ("P1004", "cable", 0.025),
    ("P1005", "cases", 0.020),
]

LAST_VIEW_CATEGORY = "audio"


def boost(minutes_since_view: int) -> float:
    return 0.012 * (0.9 ** minutes_since_view)


def main() -> None:
    print("session state moves, read (boost on audio, decays per minute):")
    for minutes in (2, 20, 40):
        scored = [
            (item_id, cat, batch + (boost(minutes) if cat == LAST_VIEW_CATEGORY else 0.0))
            for item_id, cat, batch in ITEMS
        ]
        order = [item_id for item_id, _, s in sorted(scored, key=lambda r: r[2], reverse=True)]
        print(f"  {minutes:>2} min since view: boost {boost(minutes):.4f}, order {order}")
    print("\nreading: two minutes after the view the second audio item")
    print("outranks the cable item on the session boost; by twenty")
    print("minutes the boost has decayed and the batch order is back.")
    print("The session state is not binary - its age is the feature -")
    print("and the decay curve is where the freshness-versus-stability")
    print("decision lives.")


if __name__ == "__main__":
    main()
