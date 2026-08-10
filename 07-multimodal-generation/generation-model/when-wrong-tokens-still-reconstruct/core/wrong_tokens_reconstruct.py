"""The exact-match metric versus what the frames actually look like.

Stage 02's recorded runs report a token-sequence exact-match rate of 7-22%
across seeds — the LM rarely predicts the oracle's exact token sequence —
yet all three seeds beat the frame-repeat baseline. This script reads the
recorded per-seed numbers and lays out the reconciliation: how far the LM's
wrong tokens are from the oracle's, measured by reconstruction MSE, and how
that gap compares to the frame-repeat baseline's.

Inputs (recorded, unchanged): ../runs/generation-seed{0,1,2}.json

Run:
    uv run python core/wrong_tokens_reconstruct.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    rows = []
    for seed in (0, 1, 2):
        with open(root / f"generation-seed{seed}.json") as fh:
            d = json.load(fh)
        mse = d["reconstruction_mse"]
        rows.append(
            (
                seed,
                d["predicted_token_sequence_exact_match_rate"],
                mse["lm_completion"],
                mse["oracle_tokens"],
                mse["frame_repeat_baseline"],
            )
        )

    print(f"{'seed':>4} {'exact-match':>12} {'lm MSE':>8} {'oracle MSE':>11} {'gap':>7} {'framerepeat':>11}")
    for seed, em, lm, oracle, fr in rows:
        print(f"{seed:>4} {em:>12.3f} {lm:>8.4f} {oracle:>11.4f} {lm - oracle:>+7.4f} {fr:>11.4f}")

    ems = [r[1] for r in rows]
    gaps = [r[2] - r[3] for r in rows]
    print(f"\nexact-match: mean {statistics.mean(ems):.3f}, half-range {(max(ems)-min(ems))/2:.3f}")
    print(f"reconstruction gap (lm - oracle): mean {statistics.mean(gaps):+.4f}")


if __name__ == "__main__":
    main()
