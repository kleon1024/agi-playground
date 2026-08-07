"""The dead-code reset's trajectory: a one-time fix or a maintenance loop?

Stage 05's recorded runs reset dead codes whenever usage drops, and the
`reset_log` records every reset event. This script reads the three recorded
seeds and lays out the trajectory: how many codes get reset per event, how
the reset rate decays across training, and what final codebook health the
reset maintains. The question the chapter answers is whether the reset is a
cure (a one-time intervention) or a steady-state maintenance (something the
training loop has to keep doing).

Inputs (recorded, unchanged): ../runs/reset-codec-seed{0,1,2}.json

Run:
    uv run python core/reset_trajectory.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    print(f"{'seed':>4} {'total resets':>13} {'first event':>12} {'last event':>11} "
          f"{'final usage':>11} {'eval MSE':>9}")
    all_trajectories = []
    for seed in (0, 1, 2):
        with open(root / f"reset-codec-seed{seed}.json") as fh:
            d = json.load(fh)
        log = d["reset_log"]
        first = log[0] if log else {}
        last = log[-1] if log else {}
        usage = d["codebook_usage"]
        print(
            f"{seed:>4} {d['resets_performed']:>13} "
            f"{first.get('step', 0):>8}@{first.get('n_reset', 0):>4} "
            f"{last.get('step', 0):>8}@{last.get('n_reset', 0):>4} "
            f"{usage['unique_codes_used']:>7}/{usage['codebook_size']:<3} "
            f"{d['codec_eval_mse']:>9.4f}"
        )
        # bucket the reset events into 200-step windows
        buckets: dict[int, int] = {}
        for event in log:
            b = event["step"] // 200
            buckets[b] = buckets.get(b, 0) + event["n_reset"]
        all_trajectories.append(buckets)

    print("\nreset events per 200-step window (seed 0):")
    for b in sorted(all_trajectories[0]):
        print(f"  step {b*200:>4}-{b*200+200:>4}: {all_trajectories[0][b]:>4} codes reset")


if __name__ == "__main__":
    main()
