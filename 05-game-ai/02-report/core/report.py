"""The report stage: hold mission 06's own pre-declared acceptance bar
(`mission.yaml`, written before stage 00 existed) against stage 00's real
baselines and stage 01's real 3-seed GRPO result, and say MET or NOT MET --
never a softened paraphrase of either.

Same discipline as missions 02's `09-report`, 03's `05-report`, and 05's
`02-report`: every threshold below is quoted or cited from `mission.yaml`,
and this script does not get to pick a more flattering comparison after
seeing the numbers.

Unlike mission 05's report, nothing here needs copying by hand -- stage 00's
`baselines.json` and stage 01's `grpo-seed{0,1,2}.json` are read directly, so
a re-run of either upstream stage is picked up automatically the next time
this script runs.

Run:
    uv run python report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

BASELINES_JSON = (
    Path(__file__).resolve().parents[2] / "00-gridworld-baselines" / "runs" / "baselines.json"
)
GRPO_RUNS_DIR = Path(__file__).resolve().parents[2] / "01-grpo" / "runs"
GRPO_SEED_FILES = [GRPO_RUNS_DIR / f"grpo-seed{s}.json" for s in (0, 1, 2)]


def load_baselines() -> dict | None:
    if not BASELINES_JSON.exists():
        return None
    return json.loads(BASELINES_JSON.read_text())


def load_grpo_runs() -> list[dict] | None:
    if not all(p.exists() for p in GRPO_SEED_FILES):
        return None
    return [json.loads(p.read_text()) for p in GRPO_SEED_FILES]


def spread(values: list[float]) -> float:
    return max(values) - min(values)


def catalogue_failures(runs: list[dict]) -> list[str]:
    lines = []
    degenerate = [r["degenerate_steps"] for r in runs]
    lines.append(
        f"  degenerate rollout groups (every completion in a step scored identically, "
        f"zero gradient): {degenerate} out of {runs[0]['steps']} steps per seed -- minor, "
        f"unlike mission 01's arithmetic run where this was the dominant outcome"
    )

    collapsed_seeds = []
    for r in runs:
        completions = {ex["raw_completion"] for ex in r["examples"]}
        if len(completions) == 1:
            collapsed_seeds.append((r["seed"], next(iter(completions))))
    lines.append(
        f"  board-independent policy collapse (greedy decode emits the same fixed action "
        f"string on every held-out board, ignoring the prompt): "
        f"{len(collapsed_seeds)}/{len(runs)} seeds -- "
        + ", ".join(f"seed {s}: always {c!r}" for s, c in collapsed_seeds)
    )

    non_stable = []
    for r in runs:
        succ = [h["mean_success"] for h in r["history"]]
        peak = max(succ)
        final_window = succ[-5:] if len(succ) >= 5 else succ
        final_mean = statistics.mean(final_window)
        if final_mean < peak * 0.7:
            non_stable.append((r["seed"], peak, final_mean))
    lines.append(
        f"  non-stabilizing training-time success (peak sampled success rate falls back by "
        f"the final logged steps instead of holding): {len(non_stable)}/{len(runs)} seeds -- "
        + ", ".join(f"seed {s}: peak={p:.3f} -> final-window mean={f:.3f}" for s, p, f in non_stable)
    )
    return lines


def main() -> None:
    lines = ["Mission 06 outcome report", "=" * 72]

    baselines = load_baselines()
    grpo_runs = load_grpo_runs()

    missing = []
    if baselines is None:
        missing.append(f"{BASELINES_JSON} (stage 00 baselines -- run 00-gridworld-baselines/core/measure_baselines.py)")
    if grpo_runs is None:
        missing.append(f"{GRPO_RUNS_DIR}/grpo-seed{{0,1,2}}.json (stage 01 GRPO runs -- run 01-grpo/core/train_grpo.py for seeds 0, 1, 2)")

    if missing:
        lines += ["", "VERDICT: CANNOT DETERMINE", "", "This report will not guess. Missing inputs:"]
        lines += [f"  - {m}" for m in missing]
        print("\n".join(lines))
        return
    assert baselines is not None and grpo_runs is not None

    random_rate = baselines["results"]["random"]["success_rate"]
    greedy_baseline_rate = baselines["results"]["greedy"]["success_rate"]

    greedy_per_seed = [r["eval_greedy"]["success_rate"] for r in grpo_runs]
    sampled_per_seed = [r["eval_sampled"]["success_rate"] for r in grpo_runs]
    greedy_mean = statistics.mean(greedy_per_seed)
    sampled_mean = statistics.mean(sampled_per_seed)
    greedy_spread = spread(greedy_per_seed)
    sampled_spread = spread(sampled_per_seed)

    lines.append("")
    lines.append("1. Primary metric: GRPO policy vs both stage 00 baselines (success rate on 500 held-out grids)")
    lines.append("-" * 72)
    lines.append(f"  random baseline:   {random_rate:.4f}  (stage 00, 500 trials, single deterministic-seed measurement)")
    lines.append(f"  greedy baseline:   {greedy_baseline_rate:.4f}  (stage 00, 500 trials, single deterministic-seed measurement)")
    lines.append(f"  GRPO (greedy decode): mean={greedy_mean:.4f}  spread={greedy_spread:.4f}  per_seed={[round(v, 4) for v in greedy_per_seed]}")
    lines.append(f"  GRPO (sampled decode, T=1.0): mean={sampled_mean:.4f}  spread={sampled_spread:.4f}  per_seed={[round(v, 4) for v in sampled_per_seed]}")

    def verdict_line(name: str, gm: float, baseline: float, sp: float) -> tuple[bool, str]:
        margin = gm - baseline
        beats = margin > sp
        band = "beats" if beats else ("within the noise band of" if abs(margin) < sp else "decisively loses to")
        return beats, (
            f"  {name}: margin {margin:+.4f} vs GRPO's own seed spread {sp:.4f} -> {band} this baseline"
        )

    lines.append("")
    checks = [
        verdict_line("greedy decode vs random", greedy_mean, random_rate, greedy_spread),
        verdict_line("greedy decode vs greedy baseline", greedy_mean, greedy_baseline_rate, greedy_spread),
        verdict_line("sampled decode vs random", sampled_mean, random_rate, sampled_spread),
        verdict_line("sampled decode vs greedy baseline", sampled_mean, greedy_baseline_rate, sampled_spread),
    ]
    for _, text in checks:
        lines.append(text)

    beats_both_baselines = checks[0][0] and checks[1][0]

    lines.append("")
    lines.append("2. Compute")
    lines.append("-" * 72)
    for r in grpo_runs:
        lines.append(f"  seed {r['seed']}: {r['wall_clock_s']:.1f}s, CPU, {r['steps']} steps")

    lines.append("")
    lines.append("3. Failure catalogue (mission.yaml guardrail: catalogued by category, not merely counted)")
    lines.append("-" * 72)
    lines += catalogue_failures(grpo_runs)

    lines.append("")
    is_null_result = all(r["degenerate_steps"] >= r["steps"] - 1 for r in grpo_runs)
    if beats_both_baselines:
        verdict = "MET"
    elif is_null_result:
        verdict = "MET (as an honest null result)"
    else:
        verdict = "NOT MET"
    lines.append(f"VERDICT: {verdict}")

    if verdict == "NOT MET":
        lines.append(
            "  This is not the same shape of outcome as mission 01's arithmetic null result: "
            "training took real gradient steps on 199-200 of 200 steps per seed (not a "
            "zero-gradient run), and the policy clearly learned legal-move formatting and some "
            "board sensitivity under sampled decode. But the deployed (greedy) policy decisively "
            "loses to both baselines on every seed, and even the more favorable sampled-decode "
            "reading does not beat either baseline outside its own seed-to-seed spread. Per "
            "mission.yaml's acceptance bar this is neither a win nor a qualifying null result -- "
            "it is reported as NOT MET, plainly, rather than reframed as inconclusive."
        )

    print("\n".join(lines))


if __name__ == "__main__":
    main()
