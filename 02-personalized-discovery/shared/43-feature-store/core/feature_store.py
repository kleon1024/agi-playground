"""Feature store, read: one computation, two identical reads.

Stage 43 introduces the feature store. A feature is computed once at
ingestion and served unchanged to training and serving, so the model
and the ranker see the same number. The naive alternative recomputes
on read, and the two sides drift apart as the world moves.

Run:
    uv run python core/feature_store.py
    uv run python core/feature_store.py --emit-log /tmp/store-reads.json

The `--emit-log` flag writes the same read as a JSON envelope so the
production path in `prod/store_consistency.py` can audit it the way an
online service would audit its own store reads.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CATALOGUE = [
    {"id": "P1001", "price": 49.0, "category": "audio", "added_hour": 0},
    {"id": "P1002", "price": 89.0, "category": "audio", "added_hour": 2},
    {"id": "P1003", "price": 19.0, "category": "cable", "added_hour": 1},
]

CATEGORY_CTR = {"audio": 0.032, "cable": 0.011}


def store_features() -> dict[str, dict[str, float]]:
    """The store: computed once at ingestion hour, immutable afterwards."""
    out: dict[str, dict[str, float]] = {}
    for item in CATALOGUE:
        out[item["id"]] = {
            "price": item["price"],
            "age_hours": 0.0,
            "category_ctr": CATEGORY_CTR[item["category"]],
        }
    return out


def naive_recompute(item: dict[str, object], now_hour: int) -> dict[str, float]:
    """The naive path: recompute the feature whenever it is read."""
    return {
        "price": float(item["price"]),
        "age_hours": float(now_hour - int(item["added_hour"])),
        "category_ctr": CATEGORY_CTR[str(item["category"])],
    }


def score(feats: dict[str, float]) -> float:
    return 1000.0 * feats["category_ctr"] - 0.5 * feats["price"] + (10.0 - feats["age_hours"])


def reads() -> list[dict[str, object]]:
    """The per-item reads this stage is about: store path vs naive path."""
    stored = store_features()
    out = []
    for item in CATALOGUE:
        store_feats = stored[item["id"]]
        naive_feats = naive_recompute(item, 5)
        out.append(
            {
                "id": item["id"],
                "store": store_feats,
                "naive": naive_feats,
                "store_score": score(store_feats),
                "naive_score": score(naive_feats),
            }
        )
    return out


def render(rows: list[dict[str, object]]) -> None:
    stored = store_features()
    print("feature store, read at serve time (hour 5):")
    for item in CATALOGUE:
        feats = stored[item["id"]]
        print(
            f"  {item['id']}: price ${feats['price']:.2f}, "
            f"age {feats['age_hours']:.0f}h, ctr {feats['category_ctr']:.3f}, "
            f"score {score(feats):.1f}"
        )
    print("\nnaive recompute at serve time (hour 5):")
    for item in CATALOGUE:
        feats = naive_recompute(item, 5)
        print(
            f"  {item['id']}: price ${feats['price']:.2f}, "
            f"age {feats['age_hours']:.0f}h, ctr {feats['category_ctr']:.3f}, "
            f"score {score(feats):.1f}"
        )
    print("\nreading: the store serves age 0.0 to training and serving")
    print("alike; the naive path serves age 3-5 at serve time. The ranker")
    print("reorders on a feature the model never saw - equality of the")
    print("two reads is the whole point of the store.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the store reads as JSON")
    args = parser.parse_args()
    rows = reads()
    render(rows)
    if args.emit_log:
        envelope = {"hour": 5, "items": rows}
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
