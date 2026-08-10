"""Production AUC-label seesaw audit over the emitted cohort envelope.

Stage 64 trains a shared trunk on a head slice and a tail slice with two
conflicting tasks (click and buy). The failure mode this path exists for
is the seesaw: the aggregate AUC can stay fine while one slice's or one
task's AUC silently pays for the objective the model is visibly
optimizing. The naive model's gradient is a head gradient, so the tail
slice and the buy task lose signal inside the shared trunk.

This path reads the envelope `core/seesaw.py --emit-log` writes, then
reports the stratified AUC matrix by slice and task for the naive and
the slice-weighted model, the per-task aggregate AUCs, and the
per-decile calibration of the click head -- the case-finding that shows
which slice and which task the aggregate number hides.

Requires: pandas

Run:
    python seesaw_audit.py /tmp/seesaw-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def stratified_auc(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    rows = []
    for slice_name in ("head", "tail"):
        sub = frame[frame["slice"] == slice_name]
        for task in ("click", "buy"):
            rows.append(
                {
                    "slice": slice_name,
                    "task": task,
                    "rows": len(sub),
                    "positives": int(sub[task].sum()),
                    "auc": auc(
                        sub[f"{prefix}_{task}"].tolist(), sub[task].tolist()
                    ),
                }
            )
    return pd.DataFrame(rows)


def calibration(frame: pd.DataFrame, prefix: str, task: str) -> pd.DataFrame:
    """Decile table: mean predicted probability versus actual rate, with
    the slope and intercept of the actual-on-predicted regression."""
    sub = frame[[f"{prefix}_{task}", task]].copy()
    sub["decile"] = pd.qcut(sub[f"{prefix}_{task}"], 10, labels=False)
    dec = (
        sub.groupby("decile", observed=True)
        .agg(pred=pd.NamedAgg(column=f"{prefix}_{task}", aggfunc="mean"),
             rate=pd.NamedAgg(column=task, aggfunc="mean"))
        .reset_index()
    )
    slope = (
        (dec["pred"] - dec["pred"].mean()) * (dec["rate"] - dec["rate"].mean())
    ).sum() / ((dec["pred"] - dec["pred"].mean()) ** 2).sum()
    intercept = dec["rate"].mean() - slope * dec["pred"].mean()
    return dec, slope, intercept


def render(frame: pd.DataFrame) -> None:
    print("auc-label seesaw audit over the 640-row test cohort:")
    for model, prefix in (("naive", "naive"), ("slice-weighted", "weighted")):
        print(f"\n{model} model, stratified AUC matrix:")
        m = stratified_auc(frame, prefix)
        print("  slice  task    rows  positives    auc")
        for _, row in m.iterrows():
            print(
                f"  {row['slice']:<6} {row['task']:<7} "
                f"{int(row['rows']):<5} {int(row['positives']):<10} "
                f"{row['auc']:.3f}"
            )
        agg_click = auc(
            frame[f"{prefix}_click"].tolist(), frame["click"].tolist()
        )
        agg_buy = auc(frame[f"{prefix}_buy"].tolist(), frame["buy"].tolist())
        print(f"  aggregate: click {agg_click:.3f}, buy {agg_buy:.3f}")

    dec, slope, intercept = calibration(frame, "naive", "click")
    print("\nnaive click head, per-decile calibration:")
    print("  decile   mean p  actual rate")
    for _, row in dec.iterrows():
        print(f"  {int(row['decile']):<7} {row['pred']:.3f}   {row['rate']:.3f}")
    print(f"  slope {slope:.3f}, intercept {intercept:.3f} "
          f"(a slope of 1.0 is a calibrated probability)")

    naive_tail = stratified_auc(frame, "naive")
    w_tail = stratified_auc(frame, "weighted")
    n_head_click = naive_tail[
        (naive_tail["slice"] == "head") & (naive_tail["task"] == "click")
    ]["auc"].iloc[0]
    w_head_click = w_tail[
        (w_tail["slice"] == "head") & (w_tail["task"] == "click")
    ]["auc"].iloc[0]
    n_tail_click = naive_tail[
        (naive_tail["slice"] == "tail") & (naive_tail["task"] == "click")
    ]["auc"].iloc[0]
    w_tail_click = w_tail[
        (w_tail["slice"] == "tail") & (w_tail["task"] == "click")
    ]["auc"].iloc[0]
    n_agg_click = auc(frame["naive_click"].tolist(), frame["click"].tolist())
    w_agg_click = auc(frame["weighted_click"].tolist(), frame["click"].tolist())
    print()
    if w_tail_click > n_tail_click + 0.01:
        print("verdict: AGGREGATE AUC HIDES THE TAIL SLICE TRADE --")
        print(f"slice weighting moves tail click AUC {n_tail_click:.3f} to "
              f"{w_tail_click:.3f} while head click AUC falls "
              f"{n_head_click:.3f} to {w_head_click:.3f}, and the")
        print(f"aggregate click AUC only moves {n_agg_click:.3f} to "
              f"{w_agg_click:.3f}. the aggregate number hides the")
        print("reallocation; ranking on it alone ships a head model and")
        print("calls the tail loss noise.")
    else:
        print("verdict: NO SLICE TRADE DETECTED -- tail AUC does not move")
        print("with slice weighting on this cohort.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: seesaw_audit.py <seesaw-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = pd.DataFrame(envelope["rows"])
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
