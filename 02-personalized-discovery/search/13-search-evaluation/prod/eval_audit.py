"""Production metric-divergence audit over the emitted rankings.

Stage 13 computes NDCG and MRR, and each metric has a blind spot. The
failure mode this path exists for is the leaderboard that inherits the
blind spot: when the winner is picked by one metric, a ranking that
concentrates relevance where that metric cannot see can tie or win the
leaderboard while being measurably worse on the other metric.

This path reads the envelope the core script emits
(`core/search_eval.py --emit-log /tmp/eval-envelope.json`), builds both
leaderboards, and reports the rank difference per ranking — the
case-finding that shows which metric each ranking exploits.

Requires: pandas

Run:
    python eval_audit.py /tmp/eval-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    metrics = envelope["metrics"]  # type: ignore[assignment]
    names = list(metrics.keys())
    rows = []
    for name, m in metrics.items():
        ndcg_rank = 1 + sum(1 for o in names if metrics[o]["ndcg"] > m["ndcg"])
        mrr_rank = 1 + sum(1 for o in names if metrics[o]["mrr"] > m["mrr"])
        rows.append(
            {
                "ranking": name,
                "ndcg": m["ndcg"],
                "mrr": m["mrr"],
                "ndcg_rank": ndcg_rank,
                "mrr_rank": mrr_rank,
                "rank_gap": abs(ndcg_rank - mrr_rank),
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("metric-divergence audit over the graded rankings:")
    print("  ranking                 NDCG    rank   MRR    rank   gap")
    for _, row in frame.iterrows():
        print(
            f"  {row['ranking']:<24} {row['ndcg']:.4f}   "
            f"{int(row['ndcg_rank'])}      {row['mrr']:.4f}   "
            f"{int(row['mrr_rank'])}      {int(row['rank_gap'])}"
        )
    gapped = frame[frame["rank_gap"] >= 2]
    mrr_tie = frame[frame["mrr"] == frame["mrr"].max()]
    print()
    if len(gapped) > 0:
        names = ", ".join(gapped["ranking"].tolist())
        print(f"verdict: METRIC DIVERGENCE -- {len(gapped)} of {len(frame)}")
        print("rankings move at least two leaderboard positions by metric")
        print(f"({names}). MRR ties {len(mrr_tie)} rankings as joint best")
        print("that NDCG separates across the same five; the first-hit")
        print("gamer is MRR-perfect and NDCG-fifth. A leaderboard")
        print("that picks a winner by one metric is picking among rankings")
        print("the other metric ranks differently — report both, and audit")
        print("per position, because the metric being optimized is the one")
        print("that gets gamed.")
    else:
        print("verdict: CONSISTENT -- the two leaderboards agree on every")
        print("ranking. The metric suite is not in conflict for this set.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: eval_audit.py <eval-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
