"""Join looks ahead, read: the joiner snaps features at label time, so
the snapshot contains the outcome's own window.

Stage 44 detour: the skew is usually told as features changing between
logging and serving. The leakier variant is the training join itself.
When the joiner pairs each label with the feature snapshot taken at
label arrival instead of at decision time, the feature includes clicks
that happened after the decision - including the very conversions the
label counts. Offline the leaked feature separates the training rows
beautifully; live it ranks on luck.

Run:
    uv run python core/join_lookahead.py
"""

from __future__ import annotations

# 500 clicks per item at hour 2; labels arrive at hour 5.
# item_ctr is the item's own click rate as of the snapshot hour.
ROWS = [
    {"id": "P1001", "clicks": 500, "label_ctr": 0.020,
     "asof_feature": 0.020, "labeltime_feature": 0.024},
    {"id": "P1002", "clicks": 400, "label_ctr": 0.020,
     "asof_feature": 0.020, "labeltime_feature": 0.020},
]


def separation(feature: str) -> float:
    """Share of row pairs the feature separates, given equal labels."""
    values = [row[feature] for row in ROWS]
    distinct = len({v for v in values if v is not None})
    return 1.0 if distinct > 1 else 0.0


def main() -> None:
    print("join looks ahead, read (clicks at hour 2, labels arrive hour 5):")
    print("  training rows as joined by each strategy:")
    print("  as-of join (snapshot at decision hour 2):")
    for row in ROWS:
        print(f"    {row['id']}: item_ctr {row['asof_feature']:.3f}, "
              f"label ctr {row['label_ctr']:.3f}")
    print("  label-time join (snapshot at hour 5):")
    for row in ROWS:
        print(f"    {row['id']}: item_ctr {row['labeltime_feature']:.3f}, "
              f"label ctr {row['label_ctr']:.3f}")
    print()
    print(f"  offline separation, leaked join: "
          f"{separation('labeltime_feature'):.2f}")
    print(f"  offline separation, as-of join:   "
          f"{separation('asof_feature'):.2f}")
    print("\nreading: the label-time snapshot contains the outcome's own")
    print("window: P1001's early conversions raised its feature from")
    print("0.020 to 0.024, so the leaked join 'predicts' the label from")
    print("the label. The as-of join returns the honest answer - both")
    print("items were identical at decision time, so there is nothing")
    print("to rank on. A leak that looks like signal offline is how a")
    print("model learns to promote its own luck.")


if __name__ == "__main__":
    main()
