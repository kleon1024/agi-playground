"""The real-photo margin, read: narrow, real, and noisy on the text side.

Stage 04's recorded run compared vision vs text-only on real photographs.
This script reads the recorded per-seed results and lays out the three
numbers the verdict depends on: the margin (vision minus text-only), vision's
own spread, and text-only's spread — because a narrow margin can still be
real (beyond vision's spread) while the other arm drowns in noise.

Input (recorded, unchanged): ../runs/real-photo-results.json

Run:
    uv run python core/real_photo_margin.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "real-photo-results.json") as fh:
        d = json.load(fh)
    v = d["vision_per_seed"]
    t = d["text_only_per_seed"]
    v_mean, t_mean = statistics.fmean(v), statistics.fmean(t)
    v_spread = (max(v) - min(v)) / 2
    t_spread = (max(t) - min(t)) / 2
    margin = v_mean - t_mean
    print(f"vision:    mean {v_mean:.4f} spread {v_spread:.4f} per-seed {[round(x,4) for x in v]}")
    print(f"text-only: mean {t_mean:.4f} spread {t_spread:.4f} per-seed {[round(x,4) for x in t]}")
    print(f"margin: {margin:+.4f} — beyond vision's spread ({v_spread:.4f})? {margin > v_spread}")
    print(f"text-only spread is {t_spread / v_spread:.1f}x vision's")


if __name__ == "__main__":
    main()
