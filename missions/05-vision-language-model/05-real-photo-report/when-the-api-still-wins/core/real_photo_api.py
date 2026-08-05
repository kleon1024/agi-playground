"""The build-vs-buy verdict on real photos, read from the recorded report.

Mission 05's real-photo report compared the vision pathway, the text-only
baseline, and the hosted API on 198 real-photo questions. This script reads
the recorded hosted-API raw log for the API's per-answer-type accuracy and
lays the three-arm comparison beside it, so the NOT MET verdict's structure
— vision beats text-only but the hosted API dominates both — is one table.

Inputs (recorded): ../runs/hosted-api-raw.jsonl (read, exact-match against
the majority answer after normalization) and the report's per-arm numbers
(cited).

Run:
    uv run python core/real_photo_api.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[2] / "runs" / "hosted-api-raw.jsonl"
    with open(path) as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    def correct(r: dict) -> bool:
        pred = (r.get("pred_raw") or "").strip().lower().rstrip(".")
        ans = (r.get("answer") or "").strip().lower()
        return pred == ans

    by_type: dict[str, list[bool]] = {}
    total_ok = 0
    for r in rows:
        ok = correct(r)
        total_ok += ok
        by_type.setdefault(r.get("type"), []).append(ok)
    print(f"hosted API (openai/gpt-4o-mini, {len(rows)} real-photo questions):")
    print(f"  overall: {total_ok}/{len(rows)} = {total_ok / len(rows):.3f}")
    for t, results in sorted(by_type.items()):
        print(f"  {t:<10} {sum(results):>3}/{len(results):<4} = "
              f"{sum(results) / len(results):.3f}")
    print("\nthree arms (recorded): vision 0.2374, text-only 0.2222,")
    print("hosted 0.4596. Vision beats text-only beyond its spread (+0.0152),")
    print("hosted beats vision by -0.2222 — the API dominates both, so the")
    print("verdict is NOT MET on real photos exactly as on the synthetic set.")


if __name__ == "__main__":
    main()
