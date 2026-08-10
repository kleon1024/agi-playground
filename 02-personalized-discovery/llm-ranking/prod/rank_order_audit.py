"""Production prompt-order audit over the emitted query log.

Stage 31 ranks with an LLM that sees the whole list as context. The
failure mode this path exists for is prompt-order sensitivity: the
same candidate set can rank differently just because the prompt wrote
the candidates in a different order. On the head the preference is
clear enough that the reorder is stable; on the tail the judgment
calls are marginal, and the written order becomes part of the
decision.

This path reads the envelope the core script emits
(`core/llm_rank.py --emit-log /tmp/rank-order-envelope.json`), ranks
each query's forward and reverse prompt answers, and reports the mean
absolute position displacement per stratum -- the case-finding that
shows which queries the prompt writing actually decides.

Requires: pandas

Run:
    python rank_order_audit.py /tmp/rank-order-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def displacement(forward: list[str], reverse: list[str]) -> float:
    """Mean absolute position shift between two rankings of the same docs."""
    rev_pos = {doc: i for i, doc in enumerate(reverse)}
    shifts = [abs(i - rev_pos[doc]) for i, doc in enumerate(forward)]
    return sum(shifts) / len(shifts)


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, queries in envelope["queries"].items():  # type: ignore[assignment]
        for q in queries:
            rows.append(
                {
                    "stratum": stratum,
                    "query": q["query"],
                    "swing": q["forward"] != q["reverse"],
                    "displacement": displacement(q["forward"], q["reverse"]),
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("prompt-order audit over the 20-query log:")
    print(f"  aggregate mean displacement: "
          f"{frame['displacement'].mean():.3f}")
    print()
    print("  stratum  queries  swing  mean displacement")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<8} "
            f"{sub['swing'].sum():<6} {sub['displacement'].mean():.3f}"
        )
    print()
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    if head["swing"].sum() == 0 and tail["swing"].sum() > 0:
        print("verdict: PROMPT ORDER SWINGS THE REORDER IN THE TAIL --")
        print(f"head rankings are stable (0/{len(head)} queries swing, mean")
        print(f"displacement {head['displacement'].mean():.2f}) while tail")
        print("rankings change with the written order "
              f"({tail['swing'].sum()}"
              f"/{len(tail)} queries swing, mean displacement "
              f"{tail['displacement'].mean():.2f}). The tail judgment")
        print("calls are not a stable ranking -- they are a function of how")
        print("the candidates were written into the prompt. The check is")
        print("forward-versus-reverse agreement on the tail before the LLM")
        print("reorder ships; where it swings, keep the pointwise order")
        print("(Qin et al. 2023) or sample the LLM more than once and")
        print("aggregate.")
    else:
        print("verdict: PROMPT ORDER AGREES -- forward and reverse rankings")
        print("match in every stratum; no prompt-order sensitivity.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: rank_order_audit.py <rank-order-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
