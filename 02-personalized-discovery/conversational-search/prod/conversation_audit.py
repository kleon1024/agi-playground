"""Production resolution-stability audit over the emitted session log.

Stage 36 resolves follow-ups through session context. The failure mode
this path exists for is the aggregate resolution experiment: a
short-session-dominated log can report "conversational search resolves
well" while long sessions — where truncation drops the first-turn
grounding — lose most of their resolution.

This path reads the envelope the core script emits
(`core/session_context.py --emit-log /tmp/session-envelope.json`),
stratifies resolution by session length, and reports where the session
stops resolving — the case-finding for the conversational path.

Requires: pandas

Run:
    python conversation_audit.py /tmp/session-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, sessions in envelope["sessions"].items():  # type: ignore[assignment]
        for s in sessions:
            rows.append(
                {
                    "stratum": stratum,
                    "turns": s["turns"],
                    "followup": s["followup"],
                    "resolution": s["resolution"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("resolution-stability audit over the 10-session log:")
    print(f"  aggregate resolution: {frame['resolution'].mean():.3f}")
    print()
    print("  stratum  sessions  mean turns  resolution")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<9} {sub['turns'].mean():<11.1f} "
            f"{sub['resolution'].mean():.3f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    tail_res = tail["resolution"].mean()
    print()
    if tail_res < 0.5 and head["resolution"].mean() > 0.9:
        print("verdict: RESOLUTION LOST IN LONG SESSIONS -- the")
        print(f"aggregate resolution {frame['resolution'].mean():.3f} is a")
        print(f"short-session artifact: head resolves at "
              f"{head['resolution'].mean():.3f} while tail resolution is")
        print(f"{tail_res:.3f}. Truncation drops the oldest turns first, and")
        print("the first-turn topic is exactly the grounding the follow-up")
        print("needs. Pin the first-turn grounding (or compress the middle")
        print("turns) so the referent survives the window.")
    else:
        print("verdict: RESOLUTION SPREAD -- resolution holds across")
        print("session lengths or degrades uniformly; no concentration")
        print("to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: conversation_audit.py <session-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
