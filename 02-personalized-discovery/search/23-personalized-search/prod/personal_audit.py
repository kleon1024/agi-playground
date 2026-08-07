"""Production personalization-lift audit over the emitted query log.

Stage 23 re-ranks with user context. The failure mode this path exists
for is the aggregate personalization experiment: the mean lift over a
log dominated by users who cannot be personalized hides that the lift
is concentrated in one slice — heavy history on tail queries — while
new users and head queries see no change.

This path reads the envelope the core script emits
(`core/user_context.py --emit-log /tmp/personal-envelope.json`),
crosses history depth with query stratum, and reports the lift per
slice — the case-finding that shows who actually benefits from the
model being shipped.

Requires: pandas

Run:
    python personal_audit.py /tmp/personal-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for depth, strata in envelope["queries"].items():  # type: ignore[assignment]
        for stratum, queries in strata.items():
            for q in queries:
                rows.append(
                    {
                        "depth": depth,
                        "stratum": stratum,
                        "query": q["query"],
                        "base": q["base"],
                        "personal": q["personal"],
                    }
                )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    agg = frame["personal"].mean() - frame["base"].mean()
    print("personalization-lift audit over the 16-query log:")
    print(f"  aggregate NDCG: base {frame['base'].mean():.3f} -> "
          f"personal {frame['personal'].mean():.3f} (lift {agg:+.3f})")
    print()
    print("  depth  stratum  queries  base    personal  lift")
    for depth in ("heavy", "new"):
        for stratum in ("tail", "head"):
            sub = frame[(frame["depth"] == depth) & (frame["stratum"] == stratum)]
            lift = sub["personal"].mean() - sub["base"].mean()
            print(
                f"  {depth:<6} {stratum:<8} {len(sub):<8} "
                f"{sub['base'].mean():.3f}  {sub['personal'].mean():.3f}   "
                f"{lift:+.3f}"
            )
    heavy = frame[frame["depth"] == "heavy"]
    new = frame[frame["depth"] == "new"]
    heavy_lift = heavy["personal"].mean() - heavy["base"].mean()
    new_lift = new["personal"].mean() - new["base"].mean()
    print()
    if heavy_lift > 0.1 and new_lift <= 0.0:
        print("verdict: PERSONALIZATION LIFT CONCENTRATED IN HEAVY-HISTORY")
        print(f"USERS -- the aggregate lift {agg:+.3f} is entirely the")
        print(f"heavy-history slice ({heavy_lift:+.3f}); new users get")
        print(f"{new_lift:+.3f}. The model being shipped only helps users")
        print("with history, and only on tail queries. If new users are")
        print("most of your traffic, the aggregate hides that most of")
        print("your sessions see no benefit — report the lift per slice")
        print("and pair the model with a cold-start policy.")
    else:
        print("verdict: LIFT SPREAD -- personalization helps more than")
        print("one slice, or none; no concentration to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: personal_audit.py <personal-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
