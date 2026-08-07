"""Feature diverges, read: the training snapshot and the serve-time
read disagree, and the ranker reorders on a feature the model never
saw.

Stage 43 detour: the store exists because the naive path diverges.
This script reads the divergence directly - the same items, scored
with the training-time feature and the serve-time feature.

Run:
    uv run python core/feature_diverges.py
"""

from __future__ import annotations

ITEMS = [
    {"id": "P1001", "price": 49.0, "ctr": 0.032, "added_hour": 0},
    {"id": "P1002", "price": 49.0, "ctr": 0.032, "added_hour": 5},
    {"id": "P1003", "price": 19.0, "ctr": 0.011, "added_hour": 1},
]


def score(age_hours: float, ctr: float, price: float) -> float:
    return 1000.0 * ctr - 0.5 * price + (10.0 - age_hours)


def main() -> None:
    print("feature diverges, read (score at train hour 0 vs serve hour 5):")
    rows = []
    for item in ITEMS:
        train = score(0.0, item["ctr"], item["price"])
        serve = score(float(5 - item["added_hour"]), item["ctr"], item["price"])
        rows.append((item["id"], train, serve))
    for item_id, train, serve in rows:
        print(f"  {item_id}: train score {train:.1f}, serve score {serve:.1f}")
    train_order = [r[0] for r in sorted(rows, key=lambda r: r[1], reverse=True)]
    serve_order = [r[0] for r in sorted(rows, key=lambda r: r[2], reverse=True)]
    print(f"  train order: {train_order}")
    print(f"  serve order: {serve_order}")
    print("\nreading: the items are the same; only the feature differs.")
    print("The training-time ranker sees every item as new and puts")
    print("P1001 first; at serve time P1002 is the fresh one and wins")
    print("on an age feature the model never trained on. The divergence")
    print("is not a model bug - it is the two reads disagreeing about")
    print("the world, which is what the store prevents.")


if __name__ == "__main__":
    main()
