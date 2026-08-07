"""Search evaluation: NDCG, MRR, and the metrics' blind spots.

Search evaluation answers "did the ranking work" with a metric, and the
metric choice changes what gets optimized. This stage computes NDCG@k and
MRR on a small result set and shows the classic blind spot: MRR only cares
about the first relevant hit, NDCG weights the top of the list heavily, so
a system can game either by placing one good hit early.

Run:
    uv run python core/search_eval.py
    uv run python core/search_eval.py --emit-log /tmp/eval-envelope.json

The `--emit-log` flag writes the graded rankings plus the computed
metrics so the production path in `prod/eval_audit.py` can build both
leaderboards — the way a search team checks that the metric that picks
the winner is not the metric being gamed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def ndcg(rel: list[int], k: int | None = None) -> float:
    k = k or len(rel)
    gain = [r / (1 if i == 0 else i) for i, r in enumerate(rel[:k], start=1)]
    ideal = sorted(rel, reverse=True)
    igain = [r / (1 if i == 0 else i) for i, r in enumerate(ideal[:k], start=1)]
    return sum(gain) / sum(igain) if sum(igain) else 0.0


def mrr(rel: list[int]) -> float:
    for i, r in enumerate(rel, start=1):
        if r > 0:
            return 1.0 / i
    return 0.0


RANKINGS = {
    "A: one good hit early": [3, 0, 0, 0, 0],
    "B: good spread": [1, 2, 2, 1, 0],
    "C: good at top": [3, 2, 0, 0, 0],
    "D: reversed": [0, 0, 0, 2, 3],
}

# Audit cohort: rankings where the two leaderboards diverge — F wins MRR
# by placing a mediocre hit first (NDCG ranks it fifth); G concentrates
# high grades at the top where NDCG looks and MRR punishes the weak first
# slot; H is a spread ranking MRR and NDCG both demote.
AUDIT_RANKINGS = {
    "F: first-hit gamer": [1, 3, 3, 3, 3],
    "G: ndcg gamer": [2, 3, 3, 3, 0],
    "H: spread, early miss": [0, 3, 2, 2, 1],
}


def render() -> None:
    print("search evaluation metrics, read:")
    for name, rel in RANKINGS.items():
        print(f"  {name:<22} NDCG@5 {ndcg(rel):.4f}  MRR {mrr(rel):.4f}  rel {rel}")
    print("\nreading: MRR rewards 'first hit early' and ignores the rest;")
    print("NDCG rewards graded relevance weighted to the top. A system can")
    print("inflate MRR by placing one mediocre hit first — the metric's")
    print("blind spot, and why evaluation reports several metrics together.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write rankings and metrics as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        all_rankings = {**RANKINGS, **AUDIT_RANKINGS}
        envelope = {
            "rankings": all_rankings,
            "metrics": {
                name: {
                    "ndcg": ndcg(rel),
                    "mrr": mrr(rel),
                }
                for name, rel in all_rankings.items()
            },
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
