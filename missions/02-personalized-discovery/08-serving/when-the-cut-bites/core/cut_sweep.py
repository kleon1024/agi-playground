"""What the pre-rank cut buys: p95 end-to-end latency vs the cut size.

Stage 08's two-stage design exists because fine_rank costs ~12x per
candidate what pre_rank does (14us vs 1.2us per the stage's own stage
specs). The pre-rank cut — how many candidates survive to the expensive
ranker — is therefore the dial that decides whether the funnel fits its
latency budget. This script sweeps it, reusing the stage's timing model
unmodified, and reads the p95 end-to-end latency per cut.

Run:
    uv run python core/cut_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from latency_pipeline import FunnelConfig, run_harness


def main() -> None:
    cuts = (50, 100, 200, 300, 500, 1000)
    print("pre-rank cut sweep (fine_rank 14us/candidate, recall 3000, trials 5000)")
    print(f"{'cut':>6} {'mean ms':>9} {'p95 ms':>9} {'fine-rank p95':>13}")
    for cut in cuts:
        cfg = FunnelConfig(prerank_candidates=cut)
        result = run_harness(cfg, 5000, seed=0)
        print(
            f"{cut:>6} {result['end_to_end_mean_ms']:>9.2f} {result['end_to_end_p95_ms']:>9.2f} "
            f"{result['stage_p95_ms'].get('fine_rank', 0.0):>13.2f}"
        )


if __name__ == "__main__":
    main()
