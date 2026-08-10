"""Production explanation-surface audit over the emitted surface rows.

Stage 52's read shows the attribution that builds trust is the one
whose largest term the user can check. The failure mode this path
exists for is explanation coverage that is healthy in the aggregate and
unverifiable underneath: surfaces differ in how often the largest
contribution is a claim the user can actually check, and the aggregate
hides the surface where trust is spent on black-box headlines. This
path reads the envelope the core script emits
(`core/attribution.py --emit-log /tmp/attribution-envelope.json`) and
compares each surface's headline-verifiable share against the
aggregate, the way a trust or UX team reads explanation telemetry.

The check answers the case-finding question of the stage: before you
declare the explanation policy healthy, find the surface that leads
with claims the user cannot check.

Requires: pandas

Run:
    python attribution_audit.py /tmp/attribution-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    frame = pd.DataFrame(envelope["surfaces"])  # type: ignore[arg-type]
    verifiable_agg = (frame["traffic"] * frame["headline_verifiable"]).sum()
    frame["vs_aggregate"] = frame["headline_verifiable"] - verifiable_agg
    return frame


def render(frame: pd.DataFrame) -> None:
    verifiable_agg = (frame["traffic"] * frame["headline_verifiable"]).sum()
    explained_agg = (frame["traffic"] * frame["explained"]).sum()
    print("explanation-surface audit (headline verifiability by surface):")
    print(f"  {'surface':<18} {'traffic':>8} {'explained':>9} "
          f"{'headline verifiable':>18} {'vs aggregate':>13}")
    for _, row in frame.iterrows():
        print(
            f"  {row['surface']:<18} {row['traffic']:>8.0%} "
            f"{row['explained']:>9.0%} {row['headline_verifiable']:>18.0%} "
            f"{row['vs_aggregate']:>+13.0%}"
        )
    print(f"  {'aggregate':<18} {1.0:>8.0%} {explained_agg:>9.0%} "
          f"{verifiable_agg:>18.0%}")
    below = frame[frame["vs_aggregate"] < 0]
    print()
    if len(below) == 0:
        print("verdict: VERIFIABLE -- every surface's headline is at least as")
        print("checkable as the aggregate; the explanation policy is holding.")
        return
    worst = below.sort_values("vs_aggregate").iloc[0]
    print(f"verdict: UNVERIFIABLE HEADLINE -- the {worst['surface']} surface")
    print(f"leads with a claim the user cannot check on "
          f"{1 - float(worst['headline_verifiable']):.0%} of its items,")
    print(f"against a {verifiable_agg:.0%} aggregate headline-verifiable share.")
    print("The aggregate hides it because home feed and search are")
    print("verifiable-heavy; on the surface that leans on 'similar users")
    print("bought', the largest term is a black box the user has no record")
    print("to check. Surface the verifiable terms first on that surface or")
    print("drop the black-box headline before the trust is spent.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: attribution_audit.py <attribution-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
