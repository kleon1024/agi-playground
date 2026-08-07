"""Training-serving skew, read: the price the server sees is not the
price the model trained on.

Stage 44 introduces training-serving consistency. The training set is
built from logged features - what the world looked like when the
decision was made. Serving reads live features. When a logged feature
stops matching the live one, the offline ranking is honest for a world
that no longer exists.

Run:
    uv run python core/skew.py
    uv run python core/skew.py --emit-log /tmp/skew-envelope.json

The `--emit-log` flag writes the logged and live feature vectors as a
JSON envelope so the production path in `prod/skew_audit.py` can run
the distribution check the way a platform runs TFDV against training
and serving environments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Logged at decision time: what the model trained on.
LOGGED = [
    {"id": "P1001", "price": 49.0, "ctr": 0.042},
    {"id": "P1002", "price": 89.0, "ctr": 0.023},
    {"id": "P1003", "price": 19.0, "ctr": 0.018},
]

# Live at serve time, after a promo ends and prices rise.
LIVE_PRICE = {"P1001": 56.0, "P1002": 89.0, "P1003": 24.0}


def true_ctr(price: float) -> float:
    """The real click rate as a function of the price actually shown."""
    if price <= 20.0:
        return 0.018
    if price <= 30.0:
        return 0.030
    if price <= 55.0:
        return 0.042
    return 0.026


def live_rows() -> list[dict[str, float | str]]:
    """The live feature vectors: the world at serve time."""
    return [
        {
            "id": row["id"],
            "price": LIVE_PRICE[row["id"]],
            "ctr": true_ctr(LIVE_PRICE[row["id"]]),
        }
        for row in LOGGED
    ]


def render() -> None:
    print("training-serving skew, read:")
    print("  offline order (logged CTR):")
    offline = sorted(LOGGED, key=lambda row: row["ctr"], reverse=True)
    for row in offline:
        print(f"    {row['id']}: logged ctr {row['ctr']:.3f}")
    print("  live truth (CTR at the price actually served):")
    live = live_rows()
    for row in sorted(live, key=lambda r: r["ctr"], reverse=True):
        print(f"    {row['id']}: live ctr {row['ctr']:.3f}")
    offline_winner = offline[0]["id"]
    live_winner = max(live, key=lambda r: r["ctr"])["id"]
    print(f"\nreading: offline says {offline_winner} wins; live reality")
    print(f"says {live_winner} wins. The logged price is the model's")
    print("world, and that world ended. Serving-time feature logging and")
    print("re-validation on live features are the fix, not a better model.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write logged and live vectors as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        envelope = {"logged": LOGGED, "live": live_rows()}
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
