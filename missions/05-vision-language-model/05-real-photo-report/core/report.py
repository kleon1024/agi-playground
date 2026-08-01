"""The real-photo report: hold mission 05's own pre-declared acceptance bar
against the three real, measured pathways on stage 03's real-photo eval set
-- vision (stage 04), text-only (stage 04), hosted API (this stage) -- and
say MET or NOT MET, never a softened paraphrase of either. Same discipline
as stage 02's synthetic-shapes report: every threshold is quoted from
mission.yaml, and this script does not get to pick a more flattering
comparison after seeing the numbers.

The vision/text-only per-seed numbers are read from stage 04's own
`runs/real-photo-results.json` (not re-derived here). The hosted-API numbers
come from this stage's own `runs/hosted-api-raw.jsonl`.

Run:
    uv run python report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

STAGE04_RESULTS = (
    Path(__file__).resolve().parents[2] / "04-real-photo-vision-fusion" / "runs" / "real-photo-results.json"
)
RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"
HOSTED_RAW = RUNS_DIR / "hosted-api-raw.jsonl"


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
        lines.append(f"    {cat:<10} {c:>3}/{t:<3} ({pct:5.1f}%)")
    return lines


def main() -> None:
    lines = ["Mission 05 real-photo outcome report", "=" * 72]

    if not STAGE04_RESULTS.exists():
        print(f"VERDICT: CANNOT DETERMINE\n\nMissing {STAGE04_RESULTS} -- run stage 04's train.py first.")
        return
    stage04 = json.loads(STAGE04_RESULTS.read_text())
    vision_per_seed = stage04["vision_per_seed"]
    text_only_per_seed = stage04["text_only_per_seed"]

    hosted_records = load_hosted_results()
    if not hosted_records:
        print(f"VERDICT: CANNOT DETERMINE\n\nMissing {HOSTED_RAW} -- run core/call_hosted_api.py first.")
        return

    vision_mean = statistics.mean(vision_per_seed)
    vision_spread = max(vision_per_seed) - min(vision_per_seed) if len(vision_per_seed) > 1 else 0.0
    text_only_mean = statistics.mean(text_only_per_seed)

    hosted_acc, hosted_by_cat, hosted_cost = hosted_accuracy(hosted_records)

    margin_vs_text_only = vision_mean - text_only_mean
    margin_vs_hosted = vision_mean - hosted_acc
    beats_text_only = margin_vs_text_only > vision_spread
    beats_hosted = margin_vs_hosted > vision_spread

    lines.append("")
    lines.append("1. Primary metric: vision pathway vs each baseline (exact-match accuracy)")
    lines.append("-" * 72)
    lines.append(f"  vision:      mean={vision_mean:.4f}  spread={vision_spread:.4f}  per_seed={vision_per_seed}")
    lines.append(f"  text-only:   mean={text_only_mean:.4f}  per_seed={text_only_per_seed}")
    lines.append(
        f"  hosted API:  {hosted_acc:.4f}  ({len(hosted_records)} questions, single run -- no seeds, a fixed API)"
    )
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
    lines += render_category_table("2. Hosted API accuracy by answer type", hosted_by_cat)

    lines.append("")
    lines.append("3. Cost")
    lines.append("-" * 72)
    lines.append(
        f"  hosted API: ${hosted_cost:.4f} total over {len(hosted_records)} questions "
        f"(${hosted_cost / len(hosted_records):.5f}/question)"
    )
    lines.append(f"  vision/text-only training: $0 (local CPU), {stage04['wall_clock_s']:.1f}s wall-clock")

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
