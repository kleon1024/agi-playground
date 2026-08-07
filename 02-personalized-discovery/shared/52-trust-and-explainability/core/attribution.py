"""Trust and explainability, read: an explanation is only as good as
the claim the user can check.

Stage 52 introduces explanation quality. For one shown item, a linear
scorer attributes the decision to its features. The user can verify
some of those claims and not others. The attribution that builds trust
is the one whose largest term the user can actually check.

Run:
    uv run python core/attribution.py
    uv run python core/attribution.py --emit-log /tmp/attribution-envelope.json

The `--emit-log` flag writes the per-surface explanation rows so the
production path in `prod/attribution_audit.py` can answer the
case-finding question of the stage: explanation coverage is healthy in
the aggregate, and the surface that leads with an uncheckable headline
is invisible until you stratify by surface.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The shown item and its feature values, with model weights.
FEATURES = [
    ("price", 3.0, -0.008, "verifiable"),
    ("category affinity", 0.2, 0.040, "verifiable"),
    ("similar users bought", 0.9, 0.022, "unverifiable"),
    ("you viewed this category", 0.4, 0.035, "verifiable"),
]

# Production-log surface rows: where explanations are shown, what share
# of items carry one, and how often the largest contribution is a claim
# the user can check. The similar-users recs surface leans on the
# unverifiable feature, and its headline-verifiable share is the tell.
SURFACES = [
    {"surface": "home feed", "traffic": 0.45, "explained": 0.85, "headline_verifiable": 0.72},
    {"surface": "search results", "traffic": 0.20, "explained": 0.90, "headline_verifiable": 0.85},
    {"surface": "similar-users recs", "traffic": 0.25, "explained": 0.80, "headline_verifiable": 0.30},
    {"surface": "email digest", "traffic": 0.10, "explained": 0.95, "headline_verifiable": 0.55},
]


def render_surfaces() -> None:
    print("\nsurface view (explanation coverage by surface):")
    print(f"  {'surface':<18} {'traffic':>8} {'explained':>9} "
          f"{'headline verifiable':>18}")
    for row in SURFACES:
        print(
            f"  {row['surface']:<18} {row['traffic']:>8.0%} "
            f"{row['explained']:>9.0%} {row['headline_verifiable']:>18.0%}"
        )
    explained_agg = sum(r["traffic"] * r["explained"] for r in SURFACES)
    verifiable_agg = sum(r["traffic"] * r["headline_verifiable"] for r in SURFACES)
    print(f"  {'aggregate':<18} {1.0:>8.0%} {explained_agg:>9.0%} "
          f"{verifiable_agg:>18.0%}")
    print("\n  reading: 86% of shown items carry an explanation and the")
    print("  aggregate headline is 62% verifiable, but the similar-users")
    print("  recs surface leads with an uncheckable claim on 70% of its")
    print("  items. Stratify by surface before declaring the explanation")
    print("  policy healthy.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the surface rows as JSON")
    args = parser.parse_args()
    print("trust and explainability, read (contributions to the score):")
    contributions = [
        (name, value, weight, value * weight, checkable)
        for name, value, weight, checkable in FEATURES
    ]
    total = sum(max(0.0, c[3]) for c in contributions)
    for name, value, weight, contrib, checkable in contributions:
        if contrib >= 0:
            share = contrib / total if total else 0.0
            print(f"  {name:<24} value {value:<4.1f} x weight {weight:+.3f} "
                  f"= {contrib:+.4f} ({share:.0%} of score, {checkable})")
        else:
            print(f"  {name:<24} value {value:<4.1f} x weight {weight:+.3f} "
                  f"= {contrib:+.4f} (penalty, {checkable})")
    top = max(contributions, key=lambda c: c[3])
    print(f"\nreading: the largest contribution is '{top[0]}', which the")
    print("user cannot check - no record of similar users exists on")
    print("their side. The verifiable claims ('you viewed this")
    print("category', 'category affinity') are smaller. Trust is built")
    print("on explanations the user can falsify, not on the term with")
    print("the largest coefficient.")
    render_surfaces()
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({"surfaces": SURFACES, "score_features": FEATURES})
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
