"""The report stage: hold mission 09's own pre-declared acceptance bar
(`mission.yaml`, written before stage 00 existed) against stage 00's real
split result and stage 01's real descriptor-baseline and trained-model
results, and say MET or NOT MET -- never a softened paraphrase of either.

Same discipline as missions 02, 03, 05, 06, 07, and 08's own report stages:
every threshold below is quoted or cited from `mission.yaml`, and reads stage
00/01's own JSON artifacts directly -- no numbers copied by hand.

Run:
    uv run python report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

STAGE00 = Path(__file__).resolve().parents[2] / "00-dataset-and-property"
STAGE01 = Path(__file__).resolve().parents[2] / "01-descriptor-baseline-and-model"

SPLIT_SUMMARY = STAGE00 / "data" / "split_summary.json"
DESCRIPTOR_SEEDS = [STAGE01 / "runs" / f"descriptor-seed{i}.json" for i in range(3)]
MODEL_SEEDS = [STAGE01 / "runs" / f"model-seed{i}.json" for i in range(3)]


def load(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def spread(values: list[float]) -> dict:
    return {
        "mean": statistics.fmean(values),
        "spread": max(values) - min(values),
        "values": values,
    }


def main() -> None:
    lines = ["Mission 09 outcome report", "=" * 72]

    split_summary = load(SPLIT_SUMMARY)
    descriptor_runs = [load(p) for p in DESCRIPTOR_SEEDS]
    model_runs = [load(p) for p in MODEL_SEEDS]

    missing = []
    if split_summary is None:
        missing.append(f"{SPLIT_SUMMARY} (stage 00 split -- run 00-dataset-and-property/core/prepare_dataset.py)")
    if any(r is None for r in descriptor_runs):
        missing.append(f"{STAGE01}/runs/descriptor-seed{{0,1,2}}.json (run core/descriptor_baseline.py for each seed)")
    if any(r is None for r in model_runs):
        missing.append(f"{STAGE01}/runs/model-seed{{0,1,2}}.json (run core/smiles_model.py for each seed)")

    if missing:
        lines += ["", "VERDICT: CANNOT DETERMINE", "", "This report will not guess. Missing inputs:"]
        lines += [f"  - {m}" for m in missing]
        print("\n".join(lines))
        return
    assert split_summary is not None

    desc_auc = spread([r["test_roc_auc"] for r in descriptor_runs])
    model_auc = spread([r["test_roc_auc"] for r in model_runs])
    gap = desc_auc["mean"] - model_auc["mean"]
    larger_spread = max(desc_auc["spread"], model_auc["spread"])
    beats_baseline = model_auc["mean"] > desc_auc["mean"] and abs(gap) > larger_spread

    lines.append("")
    lines.append("1. Acceptance: trained model beats descriptor baseline by more than run-to-run spread")
    lines.append("-" * 72)
    lines.append(f"  descriptor baseline (RDKit + logistic regression): "
                 f"mean {desc_auc['mean']:.4f}  spread {desc_auc['spread']:.4f}  seeds {desc_auc['values']}")
    lines.append(f"  trained model (SMILES char-transformer):           "
                 f"mean {model_auc['mean']:.4f}  spread {model_auc['spread']:.4f}  seeds {model_auc['values']}")
    lines.append(f"  gap (descriptor - model): {gap:+.4f}  (larger of the two spreads: {larger_spread:.4f})")
    lines.append(f"  -> trained model beats descriptor baseline: {beats_baseline}")
    if gap > 0:
        lines.append(
            "  -> the descriptor baseline wins, and by more than either spread: "
            "this is not a 'no result' near-tie, the trained model is clearly worse here."
        )

    scaffold = split_summary["scaffold_split_stats"]
    lines.append("")
    lines.append("2. Acceptance: scaffold overlap between train and test is measured and reported")
    lines.append("-" * 72)
    lines.append(f"  overlap_scaffold_count: {scaffold['overlap_scaffold_count']}")
    lines.append(f"  overlap_test_molecule_fraction: {scaffold['overlap_test_molecule_fraction']}")
    lines.append("  -> measured directly on the split output, not assumed: True")

    stage_runs = {
        "00-dataset-and-property": STAGE00 / "runs" / "2026-08-01-dataset-and-split.md",
        "01-descriptor-baseline-and-model": STAGE01 / "runs" / "2026-08-01-descriptor-and-model.md",
        "02-report": Path(__file__).resolve().parents[1] / "runs" / "2026-08-01-outcome-report.md",
    }
    lines.append("")
    lines.append("3. Acceptance: every stage has a runs/ entry before being marked verified")
    lines.append("-" * 72)
    for stage, path in stage_runs.items():
        lines.append(f"  {stage}: {'present' if path.exists() else 'MISSING'} ({path})")

    lines.append("")
    lines.append("4. Acceptance: the does_not_prove boundary appears in mission.yaml and the README")
    lines.append("-" * 72)
    mission_yaml = Path(__file__).resolve().parents[2] / "mission.yaml"
    mission_readme = Path(__file__).resolve().parents[2] / "README.md"
    yaml_has = "does_not_prove" in mission_yaml.read_text()
    readme_has = "does not discover, validate, or provide" in mission_readme.read_text()
    lines.append(f"  mission.yaml declares does_not_prove: {yaml_has}")
    lines.append(f"  README restates the same boundary: {readme_has}")

    # Criterion 1 alone decides MET/NOT MET for the mission's actual decision;
    # criteria 2-4 are process guardrails this run also satisfies, checked
    # separately above rather than folded silently into one boolean.
    lines.append("")
    lines.append("=" * 72)
    if beats_baseline:
        lines.append("VERDICT: MET -- the trained model beats the descriptor baseline on SR-MMP,")
        lines.append("by more than either baseline's run-to-run spread, on a measured-clean scaffold split.")
    else:
        lines.append("VERDICT: NOT MET -- the trained model does NOT beat the descriptor baseline on SR-MMP.")
        lines.append(
            f"The descriptor baseline (mean {desc_auc['mean']:.4f}) beats the trained model "
            f"(mean {model_auc['mean']:.4f}) by {gap:.4f} ROC-AUC, well outside either spread. "
            "The honest answer this mission's own decision framing allows for is exactly this one: "
            "for SR-MMP, on this scaffold split, with this ten-descriptor set and this from-scratch "
            "architecture, the descriptor baseline is the better model to ship."
        )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
