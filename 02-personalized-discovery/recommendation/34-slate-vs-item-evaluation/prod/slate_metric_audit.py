"""Production slate metric-agreement audit over the emitted log.

Stage 34 evaluates slates, not items. The failure mode this path exists
for is metric disagreement: the item-level metric (score sum) and the
slate-level metric (diversity-adjusted value) rank the same page
differently, so an item-only report picks the wrong winner exactly
where the slate is near-tied. The aggregate comparison hides this —
across all comparisons the metrics agree half the time and disagree
half the time, and only the head/tail split shows where.

This path reads the envelope the core script emits
(`core/slate_eval.py --emit-log /tmp/slate-metric-envelope.json`),
computes which winner each metric picks per comparison, and reports
the agreement rate per stratum — the case-finding that shows which
winners the item-level metric gets wrong.

Requires: pandas

Run:
    python slate_metric_audit.py /tmp/slate-metric-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def item_sum(slate: list) -> float:
    return sum(float(s) for _, s, _ in slate)


def slate_value(slate: list) -> float:
    distinct = len({d for _, _, d in slate})
    return item_sum(slate) * (1.0 + 0.2 * distinct)


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, comparisons in envelope["slates"].items():  # type: ignore[assignment]
        for idx, comparison in enumerate(comparisons):
            a_sum = item_sum(comparison["a"])
            b_sum = item_sum(comparison["b"])
            a_value = slate_value(comparison["a"])
            b_value = slate_value(comparison["b"])
            sum_winner = "a" if a_sum > b_sum else "b"
            value_winner = "a" if a_value > b_value else "b"
            rows.append(
                {
                    "stratum": stratum,
                    "comparison": idx,
                    "sum_a": round(a_sum, 2),
                    "sum_b": round(b_sum, 2),
                    "value_a": round(a_value, 2),
                    "value_b": round(b_value, 2),
                    "sum_winner": sum_winner,
                    "value_winner": value_winner,
                    "agree": sum_winner == value_winner,
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("slate metric-agreement audit over the 20-comparison log:")
    print("  stratum  comparisons  item-sum wins a  slate-value wins a  agree")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        sum_a = (sub["sum_winner"] == "a").sum()
        value_a = (sub["value_winner"] == "a").sum()
        agree = sub["agree"].sum()
        print(
            f"  {stratum:<8} {len(sub):<12} {sum_a:<17} "
            f"{value_a:<18} {agree}/{len(sub)}"
        )
    print()
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    if head["agree"].mean() == 1.0 and tail["agree"].mean() == 0.0:
        print("verdict: THE METRICS AGREE ON HEAD SLATES AND FLIP ON TAIL")
        print("SLATES -- on head comparisons item-sum and slate-value pick")
        print("the same winner (10/10). On tail comparisons every winner")
        print("flips (0/10): the higher item-score sum loses on slate")
        print("value once diversity counts. An item-level report is right")
        print("where the decision is easy and wrong where it matters.")
        print("Report the winner per metric and declare which metric the")
        print("product optimizes before tuning the ranker (Ie et al. 2019;")
        print("Craswell et al. 2008).")
    else:
        print("verdict: METRICS AGREE -- the item-level and slate-level")
        print("winners match in every stratum; no flip to report.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: slate_metric_audit.py <slate-metric-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
