"""The interval that decides, read from the recorded bootstrap run.

The significance chapter's run compared two item-set sizes with the same
true effect (+0.06). The recorded JSON holds both confidence intervals:
n=300 excludes zero, n=25 includes it — and the small-N condition shows the
larger observed gap. This script reads the JSON and lays out the two rows.

Input (recorded, unchanged): ../runs/bootstrap-run.json

Run:
    uv run python core/interval_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "bootstrap-run.json"
    ) as fh:
        d = json.load(fh)
    print(f"true effect: {d['true_effect']} (per-item pass probability)")
    print("  condition  n   score A  score B  gap     95% CI        excludes 0")
    for key, label in (("large_n", "n=300"), ("small_n", "n=25")):
        c = d[key]
        print(
            f"  {label:<9} {c['n_items']:<4} {c['score_a']:.3f}    "
            f"{c['score_b']:.3f}   {c['observed_gap']:.3f}  "
            f"({c['ci_95_low']:.3f}, {c['ci_95_high']:.3f})  "
            f"{'YES' if c['ci_excludes_zero'] else 'NO'}"
        )
    print("\nreading: the n=25 gap is larger (0.200 vs 0.133) and the n=300")
    print("interval decides — point-estimate size and statistical confidence")
    print("are different axes, and the interval is the one that ships.")


if __name__ == "__main__":
    main()
