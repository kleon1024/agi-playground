"""The report stage: hold mission 05's own pre-declared acceptance bar
against the three real, measured pathways -- vision, text-only, hosted API
-- and say MET or NOT MET, never a softened paraphrase of either.

Same discipline as missions 02's `09-report` and 03's `05-report`: every
threshold below is quoted or cited from `mission.yaml`, written before any of
stages 00-01 existed, and this script does not get to pick a more flattering
comparison after seeing the numbers.

The vision/text-only per-seed numbers are copied verbatim from
`01-vision-fusion/runs/2026-07-31-vision-vs-text-only.md` (not re-derived
here) since that run already exists and re-running it would not change
already-recorded numbers, only cost CPU time for no new information. The
hosted-API numbers come from `runs/hosted-api-raw.jsonl` (this stage's own
real run, see `runs/2026-07-31-hosted-api-full.md`). The per-category
breakdown comes from `runs/category-breakdown.json` (this stage's own
re-run of stage 01's exact 3-seed comparison, kept per-category).

Run:
    uv run python report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"
HOSTED_RAW = RUNS_DIR / "hosted-api-raw.jsonl"
CATEGORY_JSON = RUNS_DIR / "category-breakdown.json"

# Copied verbatim from 01-vision-fusion/runs/2026-07-31-vision-vs-text-only.md
VISION_PER_SEED = [0.5128, 0.5153, 0.2844]
TEXT_ONLY_PER_SEED = [0.3304, 0.3482, 0.3023]


def load_hosted_results() -> list[dict]:
    if not HOSTED_RAW.exists():
        return []
    return [json.loads(line) for line in HOSTED_RAW.read_text().splitlines() if line]


def hosted_accuracy(records: list[dict]) -> tuple[float, dict[str, tuple[int, int]], float]:
    correct = 0
    total_cost = 0.0
    by_cat: dict[str, list[int]] = {}
    for r in records:
        pred = r["pred_raw"].strip().lower().rstrip(".")
        gt = r["answer"].strip().lower()
        is_correct = pred == gt
        correct += int(is_correct)
        total_cost += r["cost_usd"]
        bucket = by_cat.setdefault(r["type"], [0, 0])
        bucket[1] += 1
        bucket[0] += int(is_correct)
    acc = correct / len(records) if records else 0.0
    by_cat_t = {k: (v[0], v[1]) for k, v in by_cat.items()}
    return acc, by_cat_t, total_cost


def render_category_table(title: str, by_cat: dict[str, tuple[int, int]]) -> list[str]:
    lines = [title]
    for cat in sorted(by_cat):
        c, t = by_cat[cat]
        pct = 100 * c / t if t else 0.0
        lines.append(f"    {cat:<14} {c:>3}/{t:<3} ({pct:5.1f}%)")
    return lines


def main() -> None:
    lines = ["Mission 05 outcome report", "=" * 72]

    hosted_records = load_hosted_results()
    category_data = json.loads(CATEGORY_JSON.read_text()) if CATEGORY_JSON.exists() else None

    missing = []
    if not hosted_records:
        missing.append(f"{HOSTED_RAW} (hosted VLM API results — run core/call_hosted_api.py)")
    if category_data is None:
        missing.append(f"{CATEGORY_JSON} (per-category vision/text-only breakdown — run core/eval_by_category.py)")

    if missing:
        lines += ["", "VERDICT: CANNOT DETERMINE", "", "This report will not guess. Missing inputs:"]
        lines += [f"  - {m}" for m in missing]
        print("\n".join(lines))
        return

    vision_mean = statistics.mean(VISION_PER_SEED)
    vision_spread = max(VISION_PER_SEED) - min(VISION_PER_SEED)
    text_only_mean = statistics.mean(TEXT_ONLY_PER_SEED)

    hosted_acc, hosted_by_cat, hosted_cost = hosted_accuracy(hosted_records)

    margin_vs_text_only = vision_mean - text_only_mean
    margin_vs_hosted = vision_mean - hosted_acc
    beats_text_only = margin_vs_text_only > vision_spread
    beats_hosted = margin_vs_hosted > vision_spread

    lines.append("")
    lines.append("1. Primary metric: vision pathway vs each baseline (exact-match accuracy)")
    lines.append("-" * 72)
    lines.append(
        f"  vision:      mean={vision_mean:.4f}  spread={vision_spread:.4f}  per_seed={VISION_PER_SEED}"
    )
    lines.append(f"  text-only:   mean={text_only_mean:.4f}  per_seed={TEXT_ONLY_PER_SEED}")
    lines.append(f"  hosted API:  {hosted_acc:.4f}  ({len(hosted_records)} questions, single run — no seeds, it is a fixed API)")
    lines.append("")
    lines.append(
        f"  vs text-only: margin {margin_vs_text_only:+.4f} vs vision's own spread {vision_spread:.4f} "
        f"-> {'beats' if beats_text_only else 'does NOT beat'} the noise band"
    )
    lines.append(
        f"  vs hosted API: margin {margin_vs_hosted:+.4f} vs vision's own spread {vision_spread:.4f} "
        f"-> {'beats' if beats_hosted else 'does NOT beat'} the noise band"
    )

    lines.append("")
    lines += render_category_table("2. Hosted API accuracy by question category", hosted_by_cat)

    if category_data:
        lines.append("")
        lines.append("3. Vision and text-only accuracy by category (3 seeds combined, correct/total pooled)")
        lines.append("-" * 72)
        for key in ("vision", "text_only"):
            lines.append(f"  {key}:")
            by_cat = {c: (v["correct"], v["total"]) for c, v in category_data["by_category"][key].items()}
            lines += ["    " + line.strip() for line in render_category_table("", by_cat)[1:]]

    lines.append("")
    lines.append("4. Cost")
    lines.append("-" * 72)
    lines.append(f"  hosted API: ${hosted_cost:.4f} total over {len(hosted_records)} questions "
                  f"(${hosted_cost / len(hosted_records):.5f}/question)")

    verdict = "MET" if (beats_text_only and beats_hosted) else "NOT MET"
    lines.append("")
    lines.append(f"VERDICT: {verdict}")
    if verdict == "NOT MET":
        reasons = []
        if not beats_text_only:
            reasons.append(
                f"margin over text-only ({margin_vs_text_only:+.4f}) does not exceed vision's own "
                f"seed-to-seed spread ({vision_spread:.4f})"
            )
        if not beats_hosted:
            reasons.append(
                f"margin over the hosted API ({margin_vs_hosted:+.4f}) does not exceed vision's own "
                f"seed-to-seed spread ({vision_spread:.4f})"
            )
        lines.append("  " + "; ".join(reasons) + ".")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
