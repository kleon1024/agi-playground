"""Detour 05-b -- the aggregate boundary hides a cliff across ODD cells.

Stage 05 reports one row for the cloned policy on hard scenarios: 0.04
completion, 0.24 collision, 0.72 timeout. This script splits the same 50
scenarios by the declared curvature range of the hard ODD (amplitude
[0.9, 1.4] split into thirds) and asks two questions.

Question 1 (structure): is the boundary uniform across the ODD, or does
it live in a cell? The clone's aggregate 0.04 completion is two episodes;
where did they come from, and does the failure mode shift by cell?

Question 2 (coverage): a uniform draw of 50 scenarios samples the extreme
third thinly, so the corner verdict rests on a handful of scenarios. How
many scenarios does each cell actually carry, how wide is the verdict on
that n, and what does stratified sampling cost in this simulator?

The expert is run on the same tracks so the cell structure is comparative,
not scenario-specific.

Usage:
    python odd_coverage.py
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch

SIM_DIR = Path(__file__).resolve().parents[3] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[3] / "02-expert-policy" / "core"
CLONE_DIR = Path(__file__).resolve().parents[3] / "03-behavior-cloning" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
sys.path.insert(0, str(CLONE_DIR))
from clone import CloneNet
from driving_sim import sample_scenario, simulate
from expert import make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
HARD_SEEDS = range(200, 250)
AMP_LO, AMP_HI = 0.9, 1.4  # declared hard curvature range (stage 05)
N_CELLS = 3


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def cell_of(amplitude: float) -> int:
    """Cell index 0..2 by thirds of the declared hard amplitude range."""
    width = (AMP_HI - AMP_LO) / N_CELLS
    return min(int((amplitude - AMP_LO) / width), N_CELLS - 1)


def wilson_95(p: float, n: int) -> tuple[float, float]:
    """Wilson score interval, stdlib-only; labeled approximate in the chapter."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.959964
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (centre - spread) / denom), min(1.0, (centre + spread) / denom))


def clopper_pearson_upper_zero_successes(n: int) -> float:
    """Exact 95% upper bound for a rate observed as 0/n."""
    return 1.0 - 0.025 ** (1.0 / n)


def main() -> None:
    t0 = time.time()
    scenarios = [sample_scenario(seed, hard=True) for seed in HARD_SEEDS]
    model = CloneNet()
    model.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    model.eval()

    cells = {}  # cell index -> per-policy outcome tallies
    for s in scenarios:
        idx = cell_of(s.amplitude)
        c = cells.setdefault(
            idx,
            {
                "n": 0,
                "amp_min": float("inf"),
                "amp_max": float("-inf"),
                "clone": {"completed": 0, "collision": 0, "offroad": 0, "timeout": 0},
                "expert": {"completed": 0, "collision": 0, "offroad": 0, "timeout": 0},
            },
        )
        c["n"] += 1
        c["amp_min"] = min(c["amp_min"], s.amplitude)
        c["amp_max"] = max(c["amp_max"], s.amplitude)
        for name, factory in (
            ("expert", make_expert),
            ("clone", lambda ss: cloned_policy(model)),
        ):
            out = simulate(s, factory(s))
            if out.completed:
                key = "completed"
            elif out.collided:
                key = "collision"
            elif out.offroad:
                key = "offroad"
            else:
                key = "timeout"
            c[name][key] += 1
    t1 = time.time()

    width = (AMP_HI - AMP_LO) / N_CELLS
    cell_rows = []
    for idx in sorted(cells):
        c = cells[idx]
        lo = AMP_LO + idx * width
        hi = AMP_LO + (idx + 1) * width
        n = c["n"]
        row = {
            "cell": f"[{lo:.2f}, {hi:.2f})",
            "n": n,
            "amp_range_seen": [round(c["amp_min"], 3), round(c["amp_max"], 3)],
        }
        for name in ("clone", "expert"):
            tallies = c[name]
            rates = {}
            for key in ("completed", "collision", "offroad", "timeout"):
                rates[key] = round(tallies[key] / n, 3)
            lo_ci, hi_ci = wilson_95(rates["completed"], n)
            row[name] = {
                **rates,
                "completion_ci95": [round(lo_ci, 3), round(hi_ci, 3)],
            }
        cell_rows.append(row)

    # Per-cell confidence: how many scenarios does the extreme cell's 0.0
    # completion rate rest on, and what n bounds its upper error at 0.05?
    zero_cells = [
        {
            "cell": row["cell"],
            "n": row["n"],
            "clopper_pearson_upper_95": round(
                clopper_pearson_upper_zero_successes(row["n"]), 3
            ),
        }
        for row in cell_rows
        if row["clone"]["completed"] == 0.0
    ]
    n_upper_05 = math.ceil(math.log(0.025) / math.log(0.95))
    # Cost to hit that target per cell, measured clone-eval wall-clock per
    # hard scenario from the stage 05 run (5.63s for 50 scenarios).
    clone_wall = 5.63 / 50.0  # stage 05 run, cloned eval
    summary = {
        "command": "python odd_coverage.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "declared_hard_amplitude_range": [AMP_LO, AMP_HI],
        "n_cells": N_CELLS,
        "scenarios": len(scenarios),
        "cells": cell_rows,
        "zero_success_cells": zero_cells,
        "confidence_target": {
            "upper_bound_target": 0.05,
            "n_per_cell_needed": n_upper_05,
            "total_scenarios_for_all_cells": n_upper_05 * N_CELLS,
            "estimated_wall_clock_s": round(
                n_upper_05 * N_CELLS * clone_wall, 1
            ),
        },
        "wall_clock_s": round(t1 - t0, 2),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-odd-coverage.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
