"""The guardrail that vetoes a headline.

Stage 09's breached fixture is the sharpest lesson in the report stage: the
candidate beats both baselines on nDCG@10 by more than seed variance (0.4102
vs 0.3012 popularity and 0.3552 item-item CF), yet the verdict is NOT MET
because one guardrail — cold-start coverage — falls below its baseline (0.271
vs 0.298). This script reads the fixture and prints the headline beside the
veto, so the report's rule ("a guardrail breach is a veto, not an extra
point") is one table.

Input (recorded, unchanged): ../core/fixtures/breached.json

Run:
    uv run python core/guardrail_veto.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "core" / "fixtures" / "breached.json"
    ) as fh:
        d = json.load(fh)
    cand = statistics.fmean(d["primary_metric"]["candidate"])
    pop = statistics.fmean(d["primary_metric"]["baselines"]["popularity"])
    cf = statistics.fmean(d["primary_metric"]["baselines"]["item_item_cf"])
    cold = d["guardrails"]["cold_start"]

    print("the breached fixture, read:")
    print(f"  candidate nDCG@10: {cand:.4f}  vs popularity {pop:.4f} / CF {cf:.4f}")
    print("  -> beats both baselines by more than seed variance")
    print(f"  cold-start guardrail: candidate {cold['candidate']:.3f} "
          f"< baseline {cold['baseline']:.3f}  -> BREACH")
    print("\nreading: a guardrail is a veto, not an extra point — a headline")
    print("win with one breached guardrail still renders NOT MET.")


if __name__ == "__main__":
    main()
