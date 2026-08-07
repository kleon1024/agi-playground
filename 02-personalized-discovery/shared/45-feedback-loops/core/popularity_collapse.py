"""Feedback loop, read: the ranker trains on what it showed, and what
it showed entrenches.

Stage 45 introduces the feedback loop. The recommender ranks items by
an estimated click rate, shows the top of the list, observes clicks on
those items, and updates the estimate. Items shown more collect more
evidence and rise; items never shown stay at the prior. Over rounds,
exposure concentrates even when the true rates differ only slightly.

Run:
    uv run python core/popularity_collapse.py
    uv run python core/popularity_collapse.py --emit-log /tmp/loop-envelope.json

The `--emit-log` flag writes the per-item exposure ledger after the last
round so the production path in `prod/exposure_audit.py` can run the
exposure-concentration check the way a team audits its own serving log.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


def simulate() -> tuple[list[dict[str, float | int]], float, float, int, int]:
    """Run the loop and return the per-item ledger plus headline stats."""
    rng = random.Random(7)
    n_items = 20
    true_ctr = [0.050 - 0.002 * i for i in range(n_items)]
    clicks = [0] * n_items
    shown = [0] * n_items
    prior = 0.025

    def rate(i: int) -> float:
        return clicks[i] / shown[i] if shown[i] else prior

    for _ in range(300):
        order = sorted(range(n_items), key=rate, reverse=True)
        for i in order[:5]:
            shown[i] += 1
            if rng.random() < true_ctr[i]:
                clicks[i] += 1

    head_share = sum(shown[:5]) / sum(shown)
    tail_share = sum(shown[-5:]) / sum(shown)
    coverage = sum(1 for s in shown if s > 0)
    sustained = sum(1 for s in shown if s >= 100)
    ledger = [
        {
            "id": f"P{i:02d}",
            "shown": shown[i],
            "clicks": clicks[i],
            "true_ctr": true_ctr[i],
            "estimate": clicks[i] / shown[i] if shown[i] else 0.025,
        }
        for i in range(n_items)
    ]
    return ledger, head_share, tail_share, coverage, sustained


def render(
    ledger: list[dict[str, float | int]],
    head_share: float,
    tail_share: float,
    coverage: int,
    sustained: int,
) -> None:
    n_items = 20
    print("feedback loop, read (300 rounds, show top 5, update on clicks):")
    print(f"  impressions head 5 (true ctr 0.042-0.050): {head_share:.0%}")
    print(f"  impressions tail 5 (true ctr 0.012-0.020): {tail_share:.0%}")
    print(f"  catalogue coverage: {coverage} of {n_items} items ever shown")
    print(f"  sustained exposure (>=100 impressions): {sustained} of {n_items}")
    print("\nreading: items 0-4 gather clicks and their estimates rise;")
    print("items 5-19 never gather enough to outrank the head, even")
    print("where their true rate beats the prior. Exposure entrenches")
    print("the first winners and starves the rest. The model's own")
    print("output became its training data, so 'more of what works'")
    print("works only until the world changes - and the starved tail")
    print("is where the change would first be visible.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the exposure ledger as JSON")
    args = parser.parse_args()
    ledger, head_share, tail_share, coverage, sustained = simulate()
    render(ledger, head_share, tail_share, coverage, sustained)
    if args.emit_log:
        envelope = {
            "rounds": 300,
            "head_share": head_share,
            "tail_share": tail_share,
            "items": ledger,
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
