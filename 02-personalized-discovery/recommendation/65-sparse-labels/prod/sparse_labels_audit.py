"""Production sparse-label audit over the emitted cohort envelope.

Stage 65 trains a buy head over slices with very different label
densities: a dense head slice, a cold-user slice, and a cold-item slice
that carries almost no purchase labels. The failure mode this path
exists for is the aggregate number: a single AUC over all rows is a
dense-slice number, and the slices where the labels barely exist are
unmeasurable, not bad.

This path reads the envelope `core/sparse_labels.py --emit-log` writes,
then reports the label-density report by slice, the delay distribution
of the purchase labels, and the per-slice AUC with a bootstrap
confidence interval for the shared model -- the case-finding that shows
which slice the aggregate number hides.

Requires: pandas, numpy

Run:
    python sparse_labels_audit.py /tmp/sparse-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def auc_ci(ps: list[float], ys: list[int], draws: int = 300) -> tuple[float, float]:
    """Bootstrap 5-95% interval of the AUC for the given slice."""
    ps_a = np.asarray(ps, dtype=float)
    ys_a = np.asarray(ys, dtype=int)
    rng = np.random.default_rng(0)
    values = []
    for _ in range(draws):
        idx = rng.integers(0, len(ps_a), len(ps_a))
        values.append(auc(ps_a[idx].tolist(), ys_a[idx].tolist()))
    return float(np.percentile(values, 5)), float(np.percentile(values, 95))


def render(frame: pd.DataFrame, snapshot: float) -> None:
    print("sparse-label audit over the 1,600-row test cohort:")
    print("\nlabel-density report by slice:")
    print("  slice       rows  positives  positive rate")
    for slice_name in ("head", "cold-user", "cold-item"):
        sub = frame[frame["slice"] == slice_name]
        pos = int(sub["buy"].sum())
        print(
            f"  {slice_name:<11} {len(sub):<5} {pos:<10} "
            f"{pos / len(sub):.4f}"
        )

    delays = frame[frame["buy"] == 1]["delay"]
    if len(delays):
        print("\ndelay distribution of purchase labels:")
        print(f"  median {delays.median():.2f}d, p75 {delays.quantile(0.75):.2f}d, "
              f"p95 {delays.quantile(0.95):.2f}d")
        print(f"  in-flight at snapshot {snapshot}d: "
              f"{(delays > snapshot).mean():.0%} of purchases")

    print("\nshared model, per-slice buy AUC (bootstrap 5-95%):")
    print("  slice       rows  positives     auc    ci low   ci high")
    rows = []
    for slice_name in ("head", "cold-user", "cold-item"):
        sub = frame[frame["slice"] == slice_name]
        pos = int(sub["buy"].sum())
        a = auc(sub["shared_buy"].tolist(), sub["buy"].tolist())
        lo, hi = auc_ci(sub["shared_buy"].tolist(), sub["buy"].tolist())
        rows.append((slice_name, len(sub), pos, a, lo, hi))
        print(
            f"  {slice_name:<11} {len(sub):<5} {pos:<10} {a:>7.3f} "
            f"{lo:>8.3f} {hi:>8.3f}"
        )
    agg = auc(frame["shared_buy"].tolist(), frame["buy"].tolist())
    print(f"  aggregate                                          {agg:>7.3f}")

    cold_item = frame[frame["slice"] == "cold-item"]
    print()
    if int(cold_item["buy"].sum()) <= 5:
        print("verdict: THE AGGREGATE AUC IS A DENSE-SLICE NUMBER --")
        print(f"the aggregate buy AUC is {agg:.3f}, but the cold-item slice")
        print("carries a handful of positives and its 5-95% interval spans")
        print("chance; the number that ships is a head-and-cold-user number.")
        print("report per slice with its interval, and gate the cold-item")
        print("slice on a different signal (surrogate, exposure, content)")
        print("because its own labels cannot decide anything yet.")
    else:
        print("verdict: COLD-ITEM SLICE MEASURABLE -- no sparse-slice defect")
        print("detected on this cohort.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: sparse_labels_audit.py <sparse-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = pd.DataFrame(envelope["rows"])
    render(frame, float(envelope["snapshot"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
