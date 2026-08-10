"""Production parse-stability audit over the emitted query log.

Stage 37 parses a raw query into an intent and slots with an LLM. The
failure mode this path exists for is the aggregate parse-quality
experiment: a head-dominated log can report "the LLM parse is good"
while tail queries — genuine judgment calls — swing between intents
across samples, and the same string can flip the retrieval path.

This path reads the envelope the core script emits
(`core/intent_slots.py --emit-log /tmp/parse-envelope.json`),
stratifies parse agreement and quality by head and tail, and reports
where the parse actually decides — the case-finding for the LLM path.

Requires: pandas

Run:
    python parse_audit.py /tmp/parse-envelope.json
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
                    "agreement": q["agreement"],
                    "samples": q["samples"],
                    "quality": q["quality"],
                    "low_conf_slots": q["low_conf_slots"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    frame["agree_rate"] = frame["agreement"] / frame["samples"]
    print("parse-stability audit over the 10-query log:")
    print(f"  aggregate parse quality: {frame['quality'].mean():.3f}  "
          f"mean agreement: {frame['agree_rate'].mean():.3f}")
    print()
    print("  stratum  queries  agreement  quality  low-conf slots")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<8} "
            f"{sub['agree_rate'].mean():.3f}    "
            f"{sub['quality'].mean():.3f}  "
            f"{sub['low_conf_slots'].mean():.1f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    tail_agree = tail["agree_rate"].mean()
    print()
    if tail_agree < 0.7 and head["agree_rate"].mean() > 0.95:
        print("verdict: PARSE QUALITY HIDES SWINGING JUDGMENT CALLS -- the")
        print(f"aggregate quality {frame['quality'].mean():.3f} is a head")
        print(f"artifact: head parses agree at {head['agree_rate'].mean():.3f}")
        print(f"and score {head['quality'].mean():.3f}, while tail parses agree")
        print(f"at only {tail_agree:.3f} — the same query parses into")
        print("different intents across samples, so a low-confidence call")
        print("flips the retrieval path. Sample the parse and take the")
        print("majority (self-consistency), and treat a low-confidence slot")
        print("as a clarification or a broadening, never a silent guess.")
    else:
        print("verdict: PARSE SPREAD -- parse stability holds across")
        print("strata or degrades uniformly; no concentration to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: parse_audit.py <parse-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
