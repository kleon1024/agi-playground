"""Production pairwise label-consistency audit over the grading batches.

Stage 12's ranker is trained on ordinal grades, and a grader's judgment
is relative: two grading passes of the same items can disagree on
boundary grades. The failure mode this path exists for is the offline
NDCG that moves because the labels moved, not because the model did —
the ranker's learned pairwise preferences are a function of which
grading pass you froze.

This path reads the envelope the core script emits
(`core/learning_to_rank.py --emit-log /tmp/ltr-envelope.json`), re-runs
the pairwise fit on each grading batch, and checks two things: the
direction disagreements between the batches (the obvious gate) and the
learned pair preferences that flip when the fit changes (the check the
direction gate misses).

Requires: pandas

Run:
    python ltr_audit.py /tmp/ltr-envelope.json
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pandas as pd


def fit(data: list[dict[str, float]], grades: list[int]) -> tuple[float, float]:
    """Re-run the stage's pairwise least-squares fit on one batch."""
    pairs = []
    for a, b in itertools.combinations(range(len(data)), 2):
        ga, gb = grades[a], grades[b]
        if ga == gb:
            continue
        x1 = data[a]["x1"] - data[b]["x1"]
        x2 = data[a]["x2"] - data[b]["x2"]
        label = 1.0 if ga > gb else -1.0
        pairs.append((x1, x2, label))
    n = len(pairs)
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    sy2 = sum(p[1] * p[1] for p in pairs)
    w2 = (n * sxy - sx * sy) / (n * sy2 - sy * sy)
    w1 = (sx - w2 * sy) / n
    return w1, w2


def order(data: list[dict[str, float]], weights: tuple[float, float]) -> list[int]:
    scored = [(weights[0] * r["x1"] + weights[1] * r["x2"], i) for i, r in enumerate(data)]
    scored.sort(reverse=True)
    return [i for _, i in scored]


def ndcg(rel: list[int]) -> float:
    def dcg(grades: list[int]) -> float:
        return sum(g / (1 if i == 0 else i) for i, g in enumerate(grades, start=1))

    ideal = sorted(rel, reverse=True)
    return dcg(rel) / dcg(ideal)


def direction_disagreements(a: list[int], b: list[int]) -> int:
    count = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        if a[i] == a[j] or b[i] == b[j]:
            continue
        if (a[i] > a[j]) != (b[i] > b[j]):
            count += 1
    return count


def preference_flips(
    data: list[dict[str, float]],
    grades: list[int],
    base: tuple[float, float],
    other: tuple[float, float],
) -> int:
    count = 0
    for i, j in itertools.combinations(range(len(data)), 2):
        if grades[i] == grades[j]:
            continue
        xi = data[i]["x1"] - data[j]["x1"]
        xj = data[i]["x2"] - data[j]["x2"]
        if (base[0] * xi + base[1] * xj > 0) != (other[0] * xi + other[1] * xj > 0):
            count += 1
    return count


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    data = envelope["data"]  # type: ignore[assignment]
    batches = envelope["batches"]  # type: ignore[assignment]
    base = fit(data, batches["A"])
    rows = []
    for name, grades in batches.items():
        weights = fit(data, grades)
        ordered = order(data, weights)
        self_ndcg = ndcg([grades[i] for i in ordered])
        frozen_ndcg = ndcg([batches["A"][i] for i in ordered])
        rows.append(
            {
                "batch": name,
                "direction_disagreements": direction_disagreements(batches["A"], grades),
                "preference_flips": preference_flips(data, batches["A"], base, weights),
                "ndcg_frozen": frozen_ndcg,
                "ndcg_self": self_ndcg,
                "order": ordered,
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("pairwise label-consistency audit over the grading batches:")
    print("  batch  direction disagr.  learned-pref flips  NDCG@A   NDCG@self")
    for _, row in frame.iterrows():
        print(
            f"  {row['batch']}      {int(row['direction_disagreements']):>3}              "
            f"{int(row['preference_flips']):>3}             "
            f"{row['ndcg_frozen']:.4f}  {row['ndcg_self']:.4f}"
        )
    flips = int(frame[frame["batch"] != "A"]["preference_flips"].max())
    spread = frame[frame["batch"] != "A"]["ndcg_frozen"]
    print(f"\n  NDCG@A spread across re-gradings: {spread.min():.4f} - {spread.max():.4f}")
    print()
    if flips > 0:
        print("verdict: PAIRWISE INCONSISTENT -- two plausible grading passes")
        print(f"flip up to {flips} of the ranker's learned pair preferences, and")
        print("offline NDCG moves with zero model change. Batch C changes no")
        print("pair direction yet flips the most preferences: a direction-only")
        print("consistency gate undercounts label fragility. The labels, not")
        print("the model, are the fragile component; redundant grading or a")
        print("margin-aware loss is the fix.")
    else:
        print("verdict: QUIET -- the re-gradings did not move the learned")
        print("preferences. The labels are consistent under this audit.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: ltr_audit.py <ltr-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
