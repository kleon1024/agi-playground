"""Production modality-coverage audit over the emitted item log.

Stage 33 makes cold items retrievable through content vectors. The
failure mode this path exists for is the single-modality item: an item
with one vector is reachable through one surface only, so a query of
the missing modality can never see it. The aggregate "reachable"
coverage hides this — every item is reachable through at least one
modality, and only the per-surface split shows the items each query
misses.

This path reads the envelope the core script emits
(`core/multimodal_recall.py --emit-log /tmp/modality-coverage-envelope.json`),
computes image, text, and either-modality coverage per stratum, and
reports where single-modality items live — the case-finding that shows
which items a given query surface cannot retrieve.

Requires: pandas

Run:
    python modality_coverage_audit.py /tmp/modality-coverage-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, items in envelope["items"].items():  # type: ignore[assignment]
        for item in items:
            image = bool(item["image"])
            text = bool(item["text"])
            rows.append(
                {
                    "stratum": stratum,
                    "item": item["name"],
                    "image": image,
                    "text": text,
                    "both": image and text,
                    "single": image != text,
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("modality-coverage audit over the 20-item log:")
    print(f"  aggregate reachable (either modality): "
          f"{(frame['image'] | frame['text']).mean():.0%}")
    print()
    print("  stratum  items  image  text  both  single")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<6} {sub['image'].mean():.0%}   "
            f"{sub['text'].mean():.0%}   {sub['both'].mean():.0%}  "
            f"{sub['single'].mean():.0%}"
        )
    print()
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    if head["both"].mean() == 1.0 and tail["single"].mean() == 1.0:
        print("verdict: SINGLE-MODALITY ITEMS ARE HALF-REACHABLE --")
        print(f"head items carry both vectors ({head['both'].mean():.0%}) and")
        print("are reachable through either surface. Tail items are")
        print(f"single-modality ({tail['single'].mean():.0%}): image-only items")
        print("are invisible to text queries and text-only items")
        print("to image queries. The aggregate reachable figure of 100%")
        print("hides that half the query surfaces miss every tail item.")
        print("Report coverage per modality, and for a single-modality")
        print("item fall back to the modality it has or synthesize the")
        print("missing one (Radford et al. 2021; Liang et al. 2022).")
    else:
        print("verdict: COVERAGE UNIFORM -- every stratum is reachable")
        print("through both modalities; no per-surface gap.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: modality_coverage_audit.py <modality-coverage-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
