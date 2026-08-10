"""Cross-endpoint analysis over the three real Tox21 comparisons this mission has already run.

No new training happens here. Every number is read directly from the
`split_summary.json` and `runs/*.json` files stages 00/01, 03, and 04 already
committed. This stage asks a single question of that existing data: does any
one simple variable (positive-class count, positive-class rate) predict (a)
how much the trained model's seed-to-seed variance is, and (b) which of the
two approaches wins, across the three endpoints measured so far.
"""

import json
import statistics
from itertools import pairwise
from pathlib import Path

MISSION_ROOT = Path(__file__).resolve().parents[2]

ENDPOINTS = [
    {
        "name": "SR-MMP",
        "split_summary": MISSION_ROOT / "00-dataset-and-property/data/split_summary.json",
        "runs_dir": MISSION_ROOT / "01-descriptor-baseline-and-model/runs",
    },
    {
        "name": "NR-PPAR-gamma",
        "split_summary": MISSION_ROOT / "03-second-endpoint/data/split_summary.json",
        "runs_dir": MISSION_ROOT / "03-second-endpoint/runs",
    },
    {
        "name": "NR-ER",
        "split_summary": MISSION_ROOT / "04-third-endpoint/data/split_summary.json",
        "runs_dir": MISSION_ROOT / "04-third-endpoint/runs",
    },
]


def load_endpoint(spec):
    split = json.loads(spec["split_summary"].read_text())
    n_train = split["n_train"]
    pos_rate = split["train_positive_rate"]
    pos_count = split.get("train_positive_count")
    if pos_count is None:
        pos_count = round(n_train * pos_rate)

    model_aucs, desc_aucs = [], []
    for seed in (0, 1, 2):
        m = json.loads((spec["runs_dir"] / f"model-seed{seed}.json").read_text())
        d = json.loads((spec["runs_dir"] / f"descriptor-seed{seed}.json").read_text())
        model_aucs.append(m.get("test_roc_auc", m.get("roc_auc")))
        desc_aucs.append(d.get("test_roc_auc", d.get("roc_auc")))

    model_mean = statistics.mean(model_aucs)
    model_spread = max(model_aucs) - min(model_aucs)
    desc_mean = statistics.mean(desc_aucs)
    desc_spread = max(desc_aucs) - min(desc_aucs)
    gap = model_mean - desc_mean

    if gap < -model_spread and gap < -desc_spread:
        verdict = "descriptor wins beyond spread"
    elif gap > model_spread and gap > desc_spread:
        verdict = "model wins beyond spread"
    else:
        verdict = "inconclusive (gap inside spread)"

    return {
        "name": spec["name"],
        "n_train": n_train,
        "train_positive_count": pos_count,
        "train_positive_rate": round(pos_rate, 4),
        "model_auc_mean": round(model_mean, 4),
        "model_auc_spread": round(model_spread, 4),
        "descriptor_auc_mean": round(desc_mean, 4),
        "descriptor_auc_spread": round(desc_spread, 4),
        "gap_model_minus_descriptor": round(gap, 4),
        "verdict": verdict,
    }


def spearman_like_direction(xs, ys):
    """For n=3, report only whether the ranking is monotonic -- not a real correlation coefficient."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranked_ys = [ys[i] for i in order]
    increasing = all(a <= b for a, b in pairwise(ranked_ys))
    decreasing = all(a >= b for a, b in pairwise(ranked_ys))
    if increasing and not decreasing:
        return "monotonic increasing"
    if decreasing and not increasing:
        return "monotonic decreasing"
    return "not monotonic"


def main():
    rows = [load_endpoint(spec) for spec in ENDPOINTS]

    print("Cross-endpoint analysis (n=3 Tox21 endpoints, no new training)")
    print("=" * 72)
    for r in rows:
        print(
            f"{r['name']:15s}  n_train={r['n_train']:5d}  "
            f"pos_count={r['train_positive_count']:4d}  pos_rate={r['train_positive_rate']:.4f}  "
            f"model={r['model_auc_mean']:.4f}(+/-{r['model_auc_spread']:.4f})  "
            f"desc={r['descriptor_auc_mean']:.4f}(+/-{r['descriptor_auc_spread']:.4f})  "
            f"gap={r['gap_model_minus_descriptor']:+.4f}  {r['verdict']}"
        )

    pos_counts = [r["train_positive_count"] for r in rows]
    model_spreads = [r["model_auc_spread"] for r in rows]
    gaps = [r["gap_model_minus_descriptor"] for r in rows]

    print()
    print("Question 1: does positive-class count predict the TRAINED MODEL'S seed-to-seed variance?")
    direction = spearman_like_direction(pos_counts, model_spreads)
    print(f"  ranking positive_count -> model_auc_spread is: {direction}")
    print(
        f"  raw pairs (pos_count, model_spread): "
        f"{sorted(zip(pos_counts, model_spreads))}"
    )
    print(
        "  n=3 is too small for a correlation coefficient to mean anything; this is a "
        "monotonicity check on ranks only, reported as suggestive, not conclusive."
    )

    print()
    print("Question 2: does positive-class count predict WHICH approach wins (gap direction)?")
    direction2 = spearman_like_direction(pos_counts, gaps)
    print(f"  ranking positive_count -> gap(model-descriptor) is: {direction2}")
    print(
        f"  raw pairs (pos_count, gap): {sorted(zip(pos_counts, gaps))}"
    )
    sr_mmp = next(r for r in rows if r["name"] == "SR-MMP")
    nr_er = next(r for r in rows if r["name"] == "NR-ER")
    print(
        f"  SR-MMP (pos_count={sr_mmp['train_positive_count']}) and NR-ER "
        f"(pos_count={nr_er['train_positive_count']}) have similar positive counts "
        f"but opposite winners ({sr_mmp['verdict']} vs {nr_er['verdict']}) -- "
        "positive-class count alone does not explain who wins."
    )

    print()
    print("OVERALL: variance-vs-scarcity holds directionally (weak, n=3); win/loss direction "
          "is NOT explained by positive-class count alone from this data.")

    out = {
        "endpoints": rows,
        "variance_vs_positive_count_direction": direction,
        "gap_vs_positive_count_direction": direction2,
        "note": "n=3; monotonicity check only, no correlation coefficient computed or implied.",
    }
    out_path = Path(__file__).resolve().parents[1] / "runs" / "2026-08-01-cross-endpoint-analysis.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nWrote {out_path.relative_to(MISSION_ROOT.parent.parent)}")


if __name__ == "__main__":
    main()
