"""Production intent-mix audit over the emitted query log.

Stage 10's classifier assigns an intent per query, and the aggregate mix
looks healthy. The failure mode this path exists for is the intent that
the aggregate hides: a query whose keywords fire two intent classes is
assigned by rule order, and a tail query with no keyword at all falls
back to navigational by default. Both are silent decisions that decide
the retrieval path before retrieval runs.

This path reads the envelope the core script emits
(`core/query_understanding.py --emit-log /tmp/query-understanding-envelope.json`)
and stratifies the log by head and tail, the way a search team drills
into an aggregate intent mix: coverage per class, the collision rate, and
the default-fallback share.

Requires: pandas

Run:
    python intent_audit.py /tmp/query-understanding-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def aggregate(frame: pd.DataFrame) -> pd.DataFrame:
    """Intent mix over the whole log, with coverage and collision counts."""
    rows = []
    for intent in ("navigational", "transactional", "informational"):
        subset = frame[frame["intent"] == intent]
        rows.append(
            {
                "intent": intent,
                "queries": len(subset),
                "share": len(subset) / len(frame),
                "no_signal": int((subset["signals"].apply(len) == 0).sum()),
                "collision": int((subset["signals"].apply(len) > 1).sum()),
            }
        )
    return pd.DataFrame(rows)


def stratified(frame: pd.DataFrame) -> pd.DataFrame:
    """Coverage and collision per frequency class, head vs tail."""
    rows = []
    for freq in ("head", "tail"):
        subset = frame[frame["freq"] == freq]
        no_signal = subset[subset["signals"].apply(len) == 0]
        collision = subset[subset["signals"].apply(len) > 1]
        rows.append(
            {
                "freq": freq,
                "queries": len(subset),
                "share": len(subset) / len(frame),
                "no_signal": len(no_signal),
                "no_signal_share": len(no_signal) / len(subset),
                "collision": len(collision),
                "collision_share": len(collision) / len(subset),
            }
        )
    return pd.DataFrame(rows)


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    log = envelope["log"]  # type: ignore[assignment]
    rows = [
        {
            "query": r["query"],
            "freq": r["freq"],
            "intent": r["intent"],
            "signals": list(r["signals"]),
            "tokens": r["tokens"],
        }
        for r in log
    ]
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    agg = aggregate(frame)
    strata = stratified(frame)

    print("intent-mix audit over the query log:")
    print("  aggregate intent mix (32 queries):")
    for _, row in agg.iterrows():
        print(
            f"    {row['intent']:<14} {int(row['queries']):>2} "
            f"{row['share']:6.1%}  no-keyword {int(row['no_signal'])}  "
            f"collision {int(row['collision'])}"
        )

    collision = frame[frame["signals"].apply(len) > 1]
    print("\n  collisions (two intent classes fired, rule order decided):")
    if len(collision) == 0:
        print("    none")
    for _, row in collision.iterrows():
        print(
            f"    {row['freq']:<5} {row['query']!r:<42} "
            f"{'/'.join(row['signals'])} -> {row['intent']}"
        )

    print("\n  head vs tail stratification:")
    for _, row in strata.iterrows():
        print(
            f"    {row['freq']:<5} {int(row['queries']):>2} queries "
            f"({row['share']:6.1%})  no-keyword {int(row['no_signal'])} "
            f"({row['no_signal_share']:5.1%})  collision "
            f"{int(row['collision'])} ({row['collision_share']:5.1%})"
        )

    tail = strata[strata["freq"] == "tail"].iloc[0]
    head = strata[strata["freq"] == "head"].iloc[0]
    print()
    if int(tail["collision"]) > int(head["collision"]):
        print("verdict: INTENT COLLISION -- the aggregate mix says the rule")
        print("order is fine, but every collision query is in the tail:")
        print(f"tail carries all {int(tail['collision'])} collisions")
        print(f"({tail['collision_share']:.0%} of tail) against 0 of head.")
        print("Rule order (transactional before informational) silently")
        print("decides the retrieval path for these; the fix is a")
        print("confidence-aware intent model with an explicit ambiguous")
        print("bucket, or dual-path retrieval that does not force one intent.")
    elif int(tail["no_signal"]) > int(head["no_signal"]):
        print("verdict: INTENT TAIL -- the default fallback is doing the")
        print("routing. Most no-keyword queries are short, rare tail")
        print("queries whose intent the keyword list never learned; they")
        print("fall back to navigational and get entity pages instead of")
        print("the comparison or review content they asked for.")
    else:
        print("verdict: QUIET -- head and tail behave alike; the classifier")
        print("needs a different audit, not a tighter threshold.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: intent_audit.py <query-understanding-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
