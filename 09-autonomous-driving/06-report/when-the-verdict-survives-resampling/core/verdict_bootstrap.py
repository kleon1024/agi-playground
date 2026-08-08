"""Stage 06 detour -- verdict robustness under seed resampling.

Stage 06's verdicts are point estimates on one 50-scenario sample. The
NOT-MET headline (cloned 0.28 vs rule baseline 0.28) is two cells of a
table, and this detour asks what either cell is worth: how much would the
verdict move if a different 50 scenarios had been drawn, and are the two
0.28 cells the same scenarios or different ones?

The run re-simulates every cell per seed (clone, lane-only floor, and
expert on eval seeds 100-149; hard clone and hard expert on hard seeds
200-249), then pairs a bootstrap over the 50 seeds per cell. Pairing
matters: clone and floor are measured on the same scenarios, so a verdict
of "tie" means something different when the two policies solve the same
scenarios (no complementarity) than when they solve disjoint ones (a
blend would clear the bar). The bootstrap preserves that per-seed
correlation and turns the single verdict into a distribution.

Usage:
    python verdict_bootstrap.py
"""

from __future__ import annotations

import json
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
from expert import lane_only_policy, make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)
HARD_SEEDS = range(200, 250)
BOOTSTRAP_DRAWS = 2000
DRAW_SIZE = 50
RNG_SEED = 7


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def _outcome_code(out) -> str:
    if out.completed:
        return "completed"
    if out.collided:
        return "collided"
    if out.offroad:
        return "offroad"
    return "timeout"


def _per_seed(scenarios, policy_factory) -> list[dict]:
    rows = []
    for s in scenarios:
        out = simulate(s, policy_factory(s))
        rows.append(
            {
                "seed": s.seed,
                "outcome": _outcome_code(out),
                "completed": out.completed,
                "x": round(out.x_reached, 2),
            }
        )
    return rows


def _completion(rows: list[dict]) -> float:
    return round(sum(r["completed"] for r in rows) / len(rows), 3)


def _paired_bootstrap(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> dict:
    """Paired resampling of n=50 seeds, difference a_count - b_count per draw."""
    n = len(a)
    diffs = np.empty(BOOTSTRAP_DRAWS, dtype=np.int64)
    for i in range(BOOTSTRAP_DRAWS):
        idx = rng.integers(0, n, size=DRAW_SIZE)
        diffs[i] = a[idx].sum() - b[idx].sum()
    frac = diffs / DRAW_SIZE
    return {
        "mean": round(float(frac.mean()), 4),
        "ci95": [round(float(np.percentile(frac, 2.5)), 4),
                 round(float(np.percentile(frac, 97.5)), 4)],
        "p_gt": round(float((diffs > 0).mean()), 4),
        "p_lt": round(float((diffs < 0).mean()), 4),
        "p_tie": round(float((diffs == 0).mean()), 4),
    }


def _set_stats(clone: list[dict], floor: list[dict]) -> dict:
    c_winners = {r["seed"] for r in clone if r["completed"]}
    f_winners = {r["seed"] for r in floor if r["completed"]}
    c_fail = {r["seed"] for r in clone if not r["completed"]}
    f_fail = {r["seed"] for r in floor if not r["completed"]}
    shared_w = sorted(c_winners & f_winners)
    clone_only = sorted(c_winners - f_winners)
    floor_only = sorted(f_winners - c_winners)
    iou = round(len(shared_w) / max(1, len(c_winners | f_winners)), 4)
    return {
        "clone_winners": sorted(c_winners),
        "floor_winners": sorted(f_winners),
        "shared_winners": shared_w,
        "clone_only_winners": clone_only,
        "floor_only_winners": floor_only,
        "shared_failures": sorted(c_fail & f_fail),
        "winners_iou": iou,
        "clone_winners_subset_of_floor": c_winners <= f_winners,
        "clone_failures_subset_of_floor_failures": c_fail <= f_fail,
        "clone_solves_any_floor_failure": bool(c_winners & f_fail),
    }


def main() -> None:
    eval_scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]
    hard_scenarios = [sample_scenario(seed, hard=True) for seed in HARD_SEEDS]

    model = CloneNet()
    model.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    model.eval()

    t0 = time.time()
    clone = _per_seed(eval_scenarios, lambda s: cloned_policy(model))
    t_clone = time.time() - t0
    t0 = time.time()
    floor = _per_seed(eval_scenarios, lambda s: lambda obs, car: lane_only_policy(s, obs, car))
    t_floor = time.time() - t0
    t0 = time.time()
    expert = _per_seed(eval_scenarios, make_expert)
    t_expert = time.time() - t0
    t0 = time.time()
    hard_clone = _per_seed(hard_scenarios, lambda s: cloned_policy(model))
    t_hard_clone = time.time() - t0
    t0 = time.time()
    hard_expert = _per_seed(hard_scenarios, make_expert)
    t_hard_expert = time.time() - t0

    rng = np.random.default_rng(RNG_SEED)
    c = np.array([r["completed"] for r in clone], dtype=np.int64)
    f = np.array([r["completed"] for r in floor], dtype=np.int64)
    e = np.array([r["completed"] for r in expert], dtype=np.int64)
    hc = np.array([r["completed"] for r in hard_clone], dtype=np.int64)
    he = np.array([r["completed"] for r in hard_expert], dtype=np.int64)

    bootstrap = {
        "clone_minus_floor": _paired_bootstrap(c, f, rng),
        "expert_minus_clone": _paired_bootstrap(e, c, rng),
        "hard_expert_minus_hard_clone": _paired_bootstrap(he, hc, rng),
    }

    clone_wins = bootstrap["clone_minus_floor"]["p_gt"]
    summary = {
        "draws": BOOTSTRAP_DRAWS,
        "draw_size": DRAW_SIZE,
        "rng_seed": RNG_SEED,
        "hardware": {
            "machine": platform.machine(),
            "processor": platform.processor() or platform.system(),
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "wall_s": {
            "clone": round(t_clone, 2),
            "floor": round(t_floor, 2),
            "expert": round(t_expert, 2),
            "hard_clone": round(t_hard_clone, 2),
            "hard_expert": round(t_hard_expert, 2),
            "total": round(t_clone + t_floor + t_expert + t_hard_clone + t_hard_expert, 2),
        },
        "completion": {
            "clone": _completion(clone),
            "floor": _completion(floor),
            "expert": _completion(expert),
            "hard_clone": _completion(hard_clone),
            "hard_expert": _completion(hard_expert),
        },
        "per_seed": {
            "clone": clone,
            "floor": floor,
            "expert": expert,
            "hard_clone": hard_clone,
            "hard_expert": hard_expert,
        },
        "seed_sets": _set_stats(clone, floor),
        "bootstrap": bootstrap,
        "verdict": {
            "stage_06_row": "cloned beats rule baseline",
            "stage_06_point_verdict": "NOT MET (0.28 vs 0.28)",
            "p_fresh_draw_shows_clone_above_floor": clone_wins,
        },
    }

    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-verdict-bootstrap.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
