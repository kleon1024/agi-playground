"""Production cost-attribution audit over the emitted scale rows.

Stage 50's read prices the cascade at one catalogue size, where each
stage costs 1.0 unit by design. The failure mode this path exists for
is the budget that drifts as the catalogue grows: recall candidates
scale sublinearly with the catalogue while the later stages keep fixed
budgets, so the stage that owns the query cost changes with scale. This
path reads the envelope the core script emits (`core/cost.py
--emit-log /tmp/cost-envelope.json`) and attributes the query budget
per stage per scale, the way a cost team reads per-stage spend from
sampled traces.

The check answers the case-finding question of the stage: before you
optimize a stage, find out which stage owns the budget at your scale.

Requires: pandas

Run:
    python cost_audit.py /tmp/cost-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    stage_names: list[str] = envelope["stages"]  # type: ignore[assignment]
    rows = []
    for scale in envelope["scales"]:  # type: ignore[union-attr]
        row = {"catalogue": scale["catalogue"]}
        per_stage: dict[str, float] = scale["per_stage"]  # type: ignore[assignment]
        for name in stage_names:
            row[name] = per_stage[name]
        row["total"] = scale["total"]
        rows.append(row)
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame, envelope: dict[str, object]) -> None:
    stage_names: list[str] = envelope["stages"]  # type: ignore[assignment]
    print("cost-attribution audit (units per stage per catalogue):")
    header = "  " + f"{'catalogue':>10} " + " ".join(
        f"{name:>11}" for name in stage_names
    ) + f" {'total':>8}"
    print(header)
    for _, row in frame.iterrows():
        label = f"{int(row['catalogue'])/1_000_000:.0f}M" if int(row["catalogue"]) < 1_000_000_000 else "1B"
        cells = " ".join(f"{row[name]:>11.2f}" for name in stage_names)
        print(f"  {label:>10} {cells} {row['total']:>8.2f}")
    print("\nshare of the query budget by stage:")
    print("  " + f"{'catalogue':>10} " + " ".join(
        f"{name:>11}" for name in stage_names
    ))
    for _, row in frame.iterrows():
        label = f"{int(row['catalogue'])/1_000_000:.0f}M" if int(row["catalogue"]) < 1_000_000_000 else "1B"
        shares = " ".join(
            f"{row[name] / row['total']:>11.0%}" for name in stage_names
        )
        print(f"  {label:>10} {shares}")
    last = frame.iloc[-1]
    recall_share = last["recall (ann)"] / last["total"]
    print()
    if recall_share > 0.5:
        print(f"verdict: RECALL DOMINANT -- recall owns {recall_share:.0%} of the")
        print("query budget at the 1B catalogue, against 25% at 10M. The")
        print("flat 1.0-each design holds only at the declared size; as the")
        print("catalogue grows, the ANN index's candidate set is what the")
        print("budget follows. Optimize recall (index quality, candidate")
        print("budget, embedding size) before touching fine-rank.")
    else:
        print("verdict: LATER STAGES DOMINANT -- the fixed-budget stages own")
        print("the query cost at this scale; optimize fine-rank or mixing")
        print("before recall.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: cost_audit.py <cost-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame, envelope)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
