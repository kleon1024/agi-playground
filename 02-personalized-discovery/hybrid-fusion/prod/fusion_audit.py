"""Production fusion-weight audit over the emitted query log.

Stage 21 fuses lexical and dense candidate sets. The failure mode this
path exists for is the fusion weight tuned on the wrong queries: a
head-dominated sweep looks flat, so the team concludes the weight does
not matter, while the tail swings with the weight — the fused result
is a decision about which matcher to trust, made for the rare query.

This path reads the envelope the core script emits
(`core/fuse_sets.py --emit-log /tmp/fusion-envelope.json`), stratifies
the NDCG at each weight and the per-query swing by head and tail, and
reports where the weight actually decides — the case-finding for the
fusion weight decision.

Requires: pandas

Run:
    python fusion_audit.py /tmp/fusion-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, queries in envelope["queries"].items():  # type: ignore[assignment]
        for q in queries:
            rows.append(
                {
                    "stratum": stratum,
                    "query": q["query"],
                    "w0": q["w0"],
                    "w05": q["w05"],
                    "w1": q["w1"],
                    "swing": max(q["w0"], q["w05"], q["w1"])
                    - min(q["w0"], q["w05"], q["w1"]),
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("fusion-weight audit over the 20-query log:")
    print("  stratum  queries  NDCG@w0  NDCG@w0.5  NDCG@w1   mean swing")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<8} {sub['w0'].mean():.3f}   "
            f"{sub['w05'].mean():.3f}     {sub['w1'].mean():.3f}   "
            f"{sub['swing'].mean():.3f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    head_swing = head["swing"].mean()
    tail_swing = tail["swing"].mean()
    print()
    if tail_swing > 0.2 and head_swing < 0.05:
        print("verdict: WEIGHT SWING CONCENTRATED IN THE TAIL -- the")
        print(f"weight moves tail NDCG by {tail_swing:.2f} on average")
        print(f"(0.45-0.80 range) against {head_swing:.2f} on head.")
        print("A head-dominated sweep looks flat, so the team concludes")
        print("the weight does not matter — but for the tail it decides")
        print("which matcher wins. Tune the weight on the tail, not the")
        print("aggregate, and report the swing per stratum.")
    else:
        print("verdict: WEIGHT STABLE -- the swing is small in both")
        print("strata or spread across them; the weight is not the")
        print("decision for this set.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: fusion_audit.py <fusion-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
