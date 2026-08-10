"""Measure both of mission 06's required baselines -- always-answer and
always-tool -- over many independently sampled problems, and report real
mean reward per level and overall. This is the number stage 06's GRPO run
has to beat, the same role `../../00-gridworld-baselines/core/measure_baselines.py`
plays for the grid-world.

Also prints an analytic *reference* number: what a policy that could see
`simulated_accuracy` directly (rather than only the difficulty label a real
policy reads) would get by always taking whichever action has the higher
expected value at each level. This is not one of the two required baselines
-- it uses information no real policy has access to -- but it is what
states the real headroom a trained policy has to close, and it is exact
rather than simulated, since both branches' expected values are closed-form
given `TOOL_COST` and `simulated_accuracy`.

Run:
    uv run python measure_baselines.py --trials 5000
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baselines import always_tool_policy, never_tool_policy
from env_text import DIGIT_LEVELS, sample_problem
from reward import TOOL_COST, compute_reward, simulated_accuracy


def evaluate(policy_name: str, policy_fn, trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    reward_sum = 0.0
    per_level = {d: {"n": 0, "reward_sum": 0.0} for d in DIGIT_LEVELS}
    for _ in range(trials):
        problem = sample_problem(rng)
        text = policy_fn(problem)
        reward, _breakdown = compute_reward(text, problem.digit_count, rng)
        reward_sum += reward
        lvl = per_level[problem.digit_count]
        lvl["n"] += 1
        lvl["reward_sum"] += reward
    per_level_mean = {
        d: (v["reward_sum"] / v["n"] if v["n"] else None) for d, v in per_level.items()
    }
    return {
        "policy": policy_name,
        "trials": trials,
        "mean_reward": reward_sum / trials,
        "per_level_mean_reward": per_level_mean,
    }


def analytic_calibrated_reference(
    tool_cost: float = TOOL_COST,
    digit_levels: tuple[int, ...] = DIGIT_LEVELS,
    format_weight: float = 0.2,
) -> dict:
    """`mean_reward_with_format` assumes the oracle's completion is always
    clean (format=1.0), the same assumption both fixed baselines' scripted
    text satisfies -- that is what makes it comparable to `results["never_tool"]
    ["mean_reward"]` and `results["always_tool"]["mean_reward"]` below, both
    of which already include that same +format_weight offset."""
    per_level_outcome = {d: max(simulated_accuracy(d), 1.0 - tool_cost) for d in digit_levels}
    outcome_mean = sum(per_level_outcome.values()) / len(digit_levels)
    return {
        "policy": "calibrated_oracle (reference only, not a required baseline; "
        "sees simulated_accuracy directly, a real policy sees only the "
        "difficulty label)",
        "mean_reward_outcome_only": outcome_mean,
        "mean_reward_with_format": format_weight * 1.0 + outcome_mean,
        "per_level_outcome_only": per_level_outcome,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--out", type=Path, default=Path(__file__).resolve().parent.parent / "runs" / "baselines.json"
    )
    args = ap.parse_args()

    t0 = time.perf_counter()
    results = {
        "never_tool": evaluate("never_tool", never_tool_policy, args.trials, args.seed),
        "always_tool": evaluate("always_tool", always_tool_policy, args.trials, args.seed),
    }
    elapsed = time.perf_counter() - t0
    oracle = analytic_calibrated_reference()

    for name, r in results.items():
        print(f"{name:>11}: mean_reward={r['mean_reward']:.4f}  per_level={r['per_level_mean_reward']}")
    print(
        "calibrated-oracle (reference, outcome-only): "
        f"mean={oracle['mean_reward_outcome_only']:.4f}  per_level={oracle['per_level_outcome_only']}"
    )
    print(
        "calibrated-oracle (reference, with format term, comparable to the two "
        f"baselines above): mean={oracle['mean_reward_with_format']:.4f}"
    )
    print(f"wall-clock: {elapsed:.4f}s")

    out = {
        "trials": args.trials,
        "seed": args.seed,
        "tool_cost": TOOL_COST,
        "digit_levels": list(DIGIT_LEVELS),
        "accuracy_model": {d: simulated_accuracy(d) for d in DIGIT_LEVELS},
        "wall_clock_s": elapsed,
        "results": results,
        "calibrated_oracle_reference": oracle,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
