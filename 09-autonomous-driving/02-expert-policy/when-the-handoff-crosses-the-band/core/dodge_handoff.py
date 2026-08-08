"""Detour 02-a -- case-mining the expert's four failures.

Stage 02 reports that the rule-based expert loses four of 50 scenarios and
attributes them to "obstacle sandwiches" -- obstacles at both lane edges near
an in-lane obstacle. This script tests that attribution the way an incident
post-mortem would: it replays each failing scenario step by step and reads
the actual decision trace.

The attribution fails. None of the four scenarios is a sandwich by the
stage-02 definition (an in-lane obstacle with lane-edge obstacles within 3m).
What the traces show instead is one shared mechanism, the dodge-handoff
transition: the expert re-plans a lateral target from the kinematic safe set
but never checks that the path from the current offset to the new one is
dynamically feasible, so a lane change that "clears" the obstacle at the
target offset still clips it while crossing the band between offsets.

The script then repairs the controller two ways and measures each alone and
combined: a precise rear window (an obstacle at or behind the car blocks a
lane only when its exact centre distance is inside the collision radius) and
a transition-feasibility check (obstacles swept by the band between the
current and target offset veto or pace the crossing). The combined repair
still loses seed 133, so the script records three follow-up variants of the
transition guard (hold-when-safe, hold-when-close, cross-slower) to show
the fix-fix loop: each variant moves the residual failure to a different
seed instead of removing it.

Usage:
    python dodge_handoff.py
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from itertools import pairwise
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[3] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[3] / "02-expert-policy" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
from driving_sim import (
    ROAD_HALF_WIDTH,
    sample_scenario,
    simulate,
)
from expert import (
    CANDIDATE_OFFSETS,
    CLEARANCE_MARGIN,
    DODGE_RELEASE,
    _obs_offset,
    _safe_offsets,
    _steer_to,
    _threats,
)

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)
FAIL_SEEDS = [107, 108, 127, 142]


def _safe_offsets_precise(scenario, car, threats) -> list[float]:
    """_safe_offsets with a precise rear window.

    An obstacle at or behind the car (dx <= 0) blocks a candidate lane only
    when the exact centre distance hypot(dx, lateral difference) is inside
    the collision radius. The forward check keeps the clearance margin.
    """
    safe = []
    for off in CANDIDATE_OFFSETS:
        if abs(off) > ROAD_HALF_WIDTH - 0.35:
            continue
        ok = True
        for dx, ox, oy, r, _vx in threats:
            off_o = _obs_offset(scenario, ox, oy)
            if dx <= 0:
                if math.hypot(dx, off - off_o) < r + 0.35:
                    ok = False
                    break
            elif abs(off - off_o) < r + CLEARANCE_MARGIN:
                ok = False
                break
        if ok:
            safe.append(off)
    return safe


def make_expert_v7(scenario, precise: bool = True, transition: bool = True,
                   variant: str = "v7", trace: list | None = None):
    """The stage-02 expert with the two detour repairs.

    `precise` turns on the precise rear window in the safe-set computation;
    `transition` turns on the transition-feasibility check in the dodge
    branch. With both off this is byte-for-byte the stage-02 controller
    (verified against the recorded 0.92/0.08 run). With `trace` set, every
    step appends its decision record to the list.

    `variant` selects the transition guard's hold rule for the fix-fix
    exploration: `v7` holds only when a close swept obstacle exists, the
    current offset is safe, and the conflict is beyond 8m; `hold_safe`
    drops the 8m gate; `hold_close` drops the current-offset check too;
    `cruise4` keeps the v7 rule but crosses at 4.0 instead of 6.0.
    """
    dodge = {"off": 0.0}

    def policy(obs, car):
        window = max(10.0, car.v * 2.5)
        threats = _threats(scenario, car, window)
        cur_off = car.y - scenario.lane_center(car.x)

        if not threats:
            dodge["off"] = 0.0
            return _steer_to(scenario, car, 0.0, 3.0), 1

        nearest = min(threats, key=lambda t: t[0])
        conflict = None
        for dx, ox, oy, r, _vx in threats:
            if (
                abs(cur_off - _obs_offset(scenario, ox, oy)) < r + CLEARANCE_MARGIN
                and (conflict is None or dx < conflict[0])
            ):
                conflict = (dx, ox, oy, r)
        n_dx, n_ox, n_oy, n_r = (
            conflict
            if conflict is not None
            else (nearest[0], nearest[1], nearest[2], nearest[3])
        )
        n_gap = abs(cur_off - _obs_offset(scenario, n_ox, n_oy))

        target_speed = 4.0
        swept: list = []
        if n_dx < 8.0:
            target_speed = 2.5

        if conflict is not None:
            horizon = n_dx + 2.0
            near = [t for t in threats if t[0] < horizon]
            safe = (
                _safe_offsets_precise(scenario, car, near)
                if precise
                else _safe_offsets(scenario, car, near)
            )
            if dodge["off"] in safe:
                target_off = dodge["off"]
            elif safe:
                target_off = min(safe, key=lambda o: abs(o - cur_off))
            else:
                target_off = cur_off

            if transition and target_off != cur_off:
                lo, hi = min(cur_off, target_off), max(cur_off, target_off)
                mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0
                swept = [
                    t
                    for t in threats
                    if 0 < t[0] < max(8.0, car.v * 3.0)
                    and abs(_obs_offset(scenario, t[1], t[2]) - mid)
                    < half + t[3] + 0.25
                ]
                if swept:
                    close = [t for t in swept if t[0] < max(5.0, car.v * 1.8)]
                    cur_safe = all(
                        abs(cur_off - _obs_offset(scenario, ox, oy))
                        >= r + CLEARANCE_MARGIN
                        for _dx, ox, oy, r, _vx in close
                    )
                    if variant == "hold_safe":
                        hold = bool(close and cur_safe)
                    elif variant == "hold_close":
                        hold = bool(close)
                    else:
                        hold = bool(close and cur_safe and n_dx > 8.0)
                    if hold:
                        target_off = cur_off
                        target_speed = 1.2
                    else:
                        target_speed = 4.0 if variant == "cruise4" else 6.0

            if n_dx < 3.0 and n_gap < n_r + 0.55:
                target_speed = 1.2
        elif dodge["off"] != 0.0 and nearest[0] > -DODGE_RELEASE:
            target_off = dodge["off"]
            throttle = 1
        else:
            target_off = 0.0
            target_speed = 6.0

        dodge["off"] = target_off
        throttle = 0 if car.v > target_speed + 0.15 else 1
        if trace is not None:
            trace.append(
                {
                    "x": round(car.x, 2),
                    "v": round(car.v, 2),
                    "cur_off": round(cur_off, 2),
                    "target_off": round(target_off, 2),
                    "conflict_dx": round(n_dx, 2),
                    "conflict_off": round(
                        _obs_offset(scenario, n_ox, n_oy), 2
                    ),
                    "swept": len(swept),
                    "dodge_off": round(dodge["off"], 2),
                }
            )
        lookahead = 2.0 if abs(target_off) > 0.05 else 3.0
        return _steer_to(scenario, car, target_off, lookahead), throttle

    return policy


def is_sandwich(scenario, tol_m: float) -> bool:
    """The stage-02 attribution: an in-lane obstacle (offset 0) with
    lane-edge obstacles at both +-1.2 within `tol_m` longitudinally."""
    obs = [
        (ox, oy - scenario.lane_center(ox))
        for ox, oy, _r, _vx in scenario.obstacles
    ]
    for ox, off in obs:
        if abs(off) > 0.05:
            continue
        left = any(
            abs(ox2 - ox) <= tol_m and abs(off2 + 1.2) < 0.05
            for ox2, off2 in obs
        )
        right = any(
            abs(ox2 - ox) <= tol_m and abs(off2 - 1.2) < 0.05
            for ox2, off2 in obs
        )
        if left and right:
            return True
    return False


def is_cluster(scenario, gap_m: float = 6.0) -> bool:
    """Two or more obstacles with longitudinal positions within `gap_m`."""
    xs = sorted(ox for ox, _oy, _r, _vx in scenario.obstacles)
    return any(b - a <= gap_m for a, b in pairwise(xs))


def _eval(policy_factory, scenarios) -> dict:
    results = {"completed": 0, "collided": 0, "offroad": 0, "timeout": 0,
               "steps": [], "fail_seeds": []}
    for s in scenarios:
        out = simulate(s, policy_factory(s))
        if out.completed:
            results["completed"] += 1
        elif out.collided:
            results["collided"] += 1
        elif out.offroad:
            results["offroad"] += 1
        else:
            results["timeout"] += 1
        results["steps"].append(out.steps)
        if not out.completed:
            results["fail_seeds"].append(s.seed)
    n = len(scenarios)
    return {
        "scenarios": n,
        "completion_rate": round(results["completed"] / n, 3),
        "collision_rate": round(results["collided"] / n, 3),
        "offroad_rate": round(results["offroad"] / n, 3),
        "timeout_rate": round(results["timeout"] / n, 3),
        "mean_steps": round(sum(results["steps"]) / n, 1),
        "fail_seeds": results["fail_seeds"],
    }


def crossing_trace(scenario, trace: list) -> dict:
    """The dodge-handoff facts of one episode: the last lateral transition
    before the episode ends and the end state."""
    end = trace[-1]
    transitions = [
        (i, e)
        for i, e in enumerate(trace)
        if abs(e["target_off"] - e["cur_off"]) > 0.05
    ]
    return {
        "last_transition": (
            {
                "step": transitions[-1][0],
                **{k: v for k, v in transitions[-1][1].items()},
            }
            if transitions
            else None
        ),
        "end": end,
        "crossings": len(transitions),
    }


def main() -> None:
    t0 = time.time()
    scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]
    fail_scenarios = [sample_scenario(seed) for seed in FAIL_SEEDS]

    # The attribution test: sandwiches in the four failing scenarios.
    sandwich_2m = [s.seed for s in fail_scenarios if is_sandwich(s, 2.0)]
    sandwich_3m = [s.seed for s in fail_scenarios if is_sandwich(s, 3.0)]

    # The distribution fact: where do the failures live?
    cluster_seeds = [s.seed for s in scenarios if is_cluster(s)]
    non_cluster_fail = [
        s.seed for s in scenarios
        if not is_cluster(s) and s.seed in FAIL_SEEDS
    ]

    # The four decision traces.
    traces = {}
    for s in fail_scenarios:
        tr = []
        out = simulate(s, make_expert_v7(
            s, precise=False, transition=False, trace=tr
        ))
        traces[s.seed] = {
            "outcome": (
                "completed" if out.completed
                else "collided" if out.collided
                else "offroad"
            ),
            "end_x": round(out.x_reached, 2),
            "collision_facts": crossing_trace(s, tr),
            "last_20_steps": tr[-20:],
        }

    # The residual failure: the guard's own hole on seed 133 under the
    # combined repair. The transition guard's "cross fast" branch accelerates
    # the car into a swept obstacle once the conflict is inside 8m, and seed
    # 133 is the one scenario where that trade loses to the base controller.
    s133 = sample_scenario(133)
    tr133 = []
    out133 = simulate(s133, make_expert_v7(
        s133, precise=True, transition=True, trace=tr133
    ))
    residual = {
        "seed": 133,
        "outcome": (
            "completed" if out133.completed
            else "collided" if out133.collided
            else "offroad"
        ),
        "end_x": round(out133.x_reached, 2),
        "collision_facts": crossing_trace(s133, tr133),
        "obstacles": [
            {
                "x": round(ox, 2), "y": round(oy, 2),
                "r": round(r, 2), "vx": round(vx, 2),
                "off": round(oy - s133.lane_center(ox), 2),
            }
            for ox, oy, r, vx in s133.obstacles
        ],
        "decision_window": tr133[-14:],
    }

    # The repairs, alone and combined.
    base = _eval(lambda s: make_expert_v7(s, False, False), scenarios)
    precise_only = _eval(lambda s: make_expert_v7(s, True, False), scenarios)
    transition_only = _eval(lambda s: make_expert_v7(s, False, True), scenarios)
    v7 = _eval(lambda s: make_expert_v7(s, True, True), scenarios)
    v8_hold_safe = _eval(
        lambda s: make_expert_v7(s, True, True, variant="hold_safe"),
        scenarios,
    )
    v9_hold_close = _eval(
        lambda s: make_expert_v7(s, True, True, variant="hold_close"),
        scenarios,
    )
    v10_cruise4 = _eval(
        lambda s: make_expert_v7(s, True, True, variant="cruise4"),
        scenarios,
    )

    result = {
        "command": "python dodge_handoff.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "attribution_test": {
            "sandwich_tol_2m_fail_seeds": sandwich_2m,
            "sandwich_tol_3m_fail_seeds": sandwich_3m,
        },
        "distribution": {
            "cluster_seed_count": len(cluster_seeds),
            "non_cluster_seed_count": 50 - len(cluster_seeds),
            "fail_seeds_in_cluster": [
                seed for seed in FAIL_SEEDS if seed in cluster_seeds
            ],
            "fail_seeds_outside_cluster": non_cluster_fail,
        },
        "policy_rates": {
            "base": base,
            "precise_only": precise_only,
            "transition_only": transition_only,
            "v7_precise_and_transition": v7,
            "v8_hold_safe": v8_hold_safe,
            "v9_hold_close": v9_hold_close,
            "v10_cruise4": v10_cruise4,
        },
        "residual_failure": residual,
        "per_seed_traces": traces,
        "wall_clock_s": round(time.time() - t0, 2),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-dodge-handoff.json").open("w") as f:
        json.dump(result, f, indent=2)

    print("attribution:", json.dumps(
        {"sandwich_2m": sandwich_2m, "sandwich_3m": sandwich_3m}, indent=2
    ))
    print("distribution:", json.dumps(
        {"cluster_count": len(cluster_seeds),
         "fails_in_cluster": [s for s in FAIL_SEEDS if s in cluster_seeds],
         "fails_outside_cluster": non_cluster_fail}, indent=2
    ))
    for name, row in (
        ("base", base),
        ("precise_only", precise_only),
        ("transition_only", transition_only),
        ("v7", v7),
    ):
        print(f"{name}: comp {row['completion_rate']} coll {row['collision_rate']} "
              f"fails {row['fail_seeds']}")
    for seed in FAIL_SEEDS:
        t = traces[seed]
        print(f"seed {seed}: {t['outcome']} at x={t['end_x']} "
              f"crossings={t['collision_facts']['crossings']} "
              f"last_transition={t['collision_facts']['last_transition']}")
    print("wall_clock_s:", result["wall_clock_s"])


if __name__ == "__main__":
    main()
