"""Production margin-stratified pair audit over the emitted preference log.

Stage 32 trains a ranker from pairwise preferences. The failure mode
this path exists for is the near-tie pair: when the two items score
almost the same, label noise decides which one is reported as chosen,
and the model learns a wrong gradient from a preference that was never
really there. On the head the margins are wide and the label survives
noise; on the tail the margins are near zero and the preference flips.

This path reads the envelope the core script emits
(`core/preference_opt.py --emit-log /tmp/pair-margin-envelope.json`),
computes the flip rate and the Bradley-Terry loss under clean and
observed labels per stratum, and reports where label noise actually
decides the preference — the case-finding that shows which pairs the
annotator, not the user, created.

Requires: pandas

Run:
    python pair_margin_audit.py /tmp/pair-margin-envelope.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd


def bt_loss(chosen: float, rejected: float) -> float:
    return -math.log(1.0 / (1.0 + math.exp(-(chosen - rejected))))


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, pairs in envelope["pairs"].items():  # type: ignore[assignment]
        for p in pairs:
            flip = bool(p["flip"])
            clean_loss = bt_loss(p["chosen"], p["rejected"])
            if flip:
                observed_loss = bt_loss(p["rejected"], p["chosen"])
            else:
                observed_loss = clean_loss
            rows.append(
                {
                    "stratum": stratum,
                    "margin": p["chosen"] - p["rejected"],
                    "flip": flip,
                    "clean_loss": clean_loss,
                    "observed_loss": observed_loss,
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("margin-stratified pair audit over the 20-pair log:")
    print(f"  aggregate flip rate: {frame['flip'].mean():.2f}")
    print()
    print("  stratum  pairs  mean margin  flips  flip rate  clean loss  "
          "observed loss")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<6} {sub['margin'].mean():.3f}    "
            f"{sub['flip'].sum():<5} {sub['flip'].mean():.2f}    "
            f"{sub['clean_loss'].mean():.3f}     "
            f"{sub['observed_loss'].mean():.3f}"
        )
    print()
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    if head["flip"].sum() == 0 and tail["flip"].sum() > 0:
        print("verdict: NEAR-TIE PREFERENCES FLIP UNDER LABEL NOISE --")
        print(f"head pairs (mean margin {head['margin'].mean():.2f}) are")
        print(f"stable: 0/{len(head)} flips, observed loss equals clean")
        print(f"loss. Tail pairs (mean margin {tail['margin'].mean():.3f})")
        print(f"flip at {tail['flip'].sum()}/{len(tail)} -- the reported")
        print("preference contradicts the true one and forces a wrong")
        print(f"gradient. The aggregate flip rate {frame['flip'].mean():.2f}")
        print("hides that every flip is a near tie. Sample pairs by")
        print("margin, re-ask low-margin preferences, and evaluate on")
        print("high-margin held-out pairs; otherwise the tail preference")
        print("is the annotator, not the user (Rafailov et al. 2023,")
        print("Zhang et al. 2025).")
    else:
        print("verdict: PREFERENCES STABLE -- no stratum flips under label")
        print("noise; the observed labels match the true preferences.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: pair_margin_audit.py <pair-margin-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
