"""The experiment validity gate: is this A/B result readable?

Stage 09's report decides whether an offline build earned a claim. This gate
decides the online counterpart: whether an A/B result can be believed at all.
An experiment that reports p < 0.05 is not automatically evidence. Three
ordinary failures make the number lie, and each is findable before the
outcome test is read:

1. The split lies (sample ratio mismatch, SRM). The bucketing hash assigns
   51.5% of users to treatment while the config says 50/50. Every comparison
   built on the skewed split is biased, and the allocation-ratio chi-square
   test catches it with far less traffic than the outcome test needs.
2. The analysis unit does not match the randomization unit. Users are
   randomized but sessions are analyzed as if independent. Correlated
   sessions inside a user make the naive standard error too small, so the
   p-value lies toward significance. Comparing a clustered (per-user)
   standard error against the naive one exposes the gap.
3. Serial dependence in switchback experiments. When the randomization unit
   is a time block (marketplaces, ads, any two-sided setting), block
   outcomes autocorrelate and per-minute analysis overstates significance
   again. The deeper fix is time-series-aware block analysis.

The gate returns INVALID and names the first failing check, or
INTERPRETABLE when all three conditions hold. The fixtures are synthetic
specs, generated deterministically by this script; the gate itself is what
runs against a real experiment log.

Usage:
    uv run python core/ab_validity.py [--fixture broken|fixed|switchback]
    uv run python core/ab_validity.py --fixture broken --emit-log /tmp/ab-broken.json

The `--emit-log` flag writes the generated session log so the production
path in `prod/experiment_validity.py` can read a persisted log, the way a
metrics store would hand one to the analysis pipeline.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
CRITICAL_SE_RATIO = 1.2  # clustered SE above this vs the naive SE flags the unit
CRITICAL_RHO1 = 0.2  # block-mean lag-1 autocorrelation above this flags serial dependence
ALPHA = 0.05


def erfc(x: float) -> float:
    """Complementary error function; stdlib since Python 3.2."""
    return math.erfc(x)


def chi2_sf_1df(chi2: float) -> float:
    """Survival function of a chi-square with one degree of freedom.

    For df=1 the survival function has a closed form: P(X > x) =
    2 * (1 - Phi(sqrt(x))) = erfc(sqrt(x / 2)). General df needs the
    regularized incomplete gamma, which is what scipy hides; the production
    path uses scipy so this closed form stays a teaching choice.
    """
    return erfc(math.sqrt(chi2 / 2.0))


def generate_log(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministically generate a session log from a small fixture spec."""
    rng = random.Random(spec["seed"])
    rows: list[dict[str, Any]] = []
    if not spec.get("switchback", False):
        user_sd = spec.get("user_sd", 0.3)
        session_sd = spec.get("session_sd", 2.0)
        p_treat = spec["actual_treatment"]
        for u in range(spec["users"]):
            effect = rng.gauss(0.0, user_sd)
            arm = "treatment" if rng.random() < p_treat else "control"
            for _ in range(rng.randint(*spec["sessions_per_user"])):
                rows.append(
                    {
                        "unit": f"u{u}",
                        "arm": arm,
                        "block": None,
                        "outcome": effect + rng.gauss(0.0, session_sd),
                    }
                )
    else:
        # A switchback: the randomization unit is a time block, the analysis
        # rows are minutes. The outcome is an AR(1) series so minutes within
        # a block and block means themselves both autocorrelate.
        blocks = spec["blocks"]
        minutes = spec["minutes_per_block"]
        phi = spec["ar_phi"]
        total = blocks * minutes
        series: list[float] = [0.0] * total
        x = 0.0
        for t in range(total):
            x = phi * x + rng.gauss(0.0, spec["outcome_sd"])
            series[t] = x
        for b in range(blocks):
            arm = "treatment" if rng.random() < spec["actual_treatment"] else "control"
            for m in range(minutes):
                rows.append(
                    {
                        "unit": f"b{b}",
                        "arm": arm,
                        "block": b,
                        "outcome": series[b * minutes + m],
                    }
                )
    return rows


def srm_check(log: list[dict[str, Any]], expected: float) -> dict[str, Any]:
    """Allocation-ratio check: does the observed split match the declared one?"""
    counts = {"control": 0, "treatment": 0}
    seen: set[str] = set()
    for row in log:
        if row["unit"] not in seen:
            seen.add(row["unit"])
            counts[row["arm"]] += 1
    n = sum(counts.values())
    exp_treat = n * expected
    exp_ctrl = n * (1.0 - expected)
    chi2 = (counts["treatment"] - exp_treat) ** 2 / exp_treat + (
        counts["control"] - exp_ctrl
    ) ** 2 / exp_ctrl
    p = chi2_sf_1df(chi2)
    return {
        "control": counts["control"],
        "treatment": counts["treatment"],
        "chi2": chi2,
        "p": p,
        "pass": p >= ALPHA,
    }


def unit_check(log: list[dict[str, Any]]) -> dict[str, Any]:
    """Naive per-row SE vs clustered per-unit SE on the treatment effect."""
    arms = [r["arm"] for r in log]
    outcomes = [r["outcome"] for r in log]
    t = [o for a, o in zip(arms, outcomes) if a == "treatment"]
    c = [o for a, o in zip(arms, outcomes) if a == "control"]

    def var(xs: list[float]) -> float:
        m = mean(xs)
        return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)

    pooled = ((len(t) - 1) * var(t) + (len(c) - 1) * var(c)) / (len(t) + len(c) - 2)
    naive_se = math.sqrt(pooled * (1.0 / len(t) + 1.0 / len(c)))

    by_unit: dict[str, list[float]] = {}
    for row in log:
        by_unit.setdefault(row["unit"], []).append(row["outcome"])
    unit_means = {u: mean(v) for u, v in by_unit.items()}
    arm_of = {row["unit"]: row["arm"] for row in log}
    tu = [m for u, m in unit_means.items() if arm_of[u] == "treatment"]
    cu = [m for u, m in unit_means.items() if arm_of[u] == "control"]
    clustered_se = math.sqrt(var(tu) / len(tu) + var(cu) / len(cu))
    ratio = clustered_se / naive_se if naive_se > 0 else float("inf")
    return {
        "naive_se": naive_se,
        "clustered_se": clustered_se,
        "ratio": ratio,
        "pass": ratio <= CRITICAL_SE_RATIO,
    }


def serial_check(log: list[dict[str, Any]]) -> dict[str, Any]:
    """Lag-1 autocorrelation of block means (switchback experiments only)."""
    by_block: dict[int, list[float]] = {}
    arm_of_block: dict[int, str] = {}
    for row in log:
        if row["block"] is None:
            return {"rho1": 0.0, "pass": True, "skipped": True}
        by_block.setdefault(row["block"], []).append(row["outcome"])
        arm_of_block[row["block"]] = row["arm"]
    block_means = {b: sum(v) / len(v) for b, v in by_block.items()}
    arm_means: dict[str, float] = {}
    for b, m in block_means.items():
        arm_means[arm_of_block[b]] = arm_means.get(arm_of_block[b], 0.0) + m
    for a in arm_means:
        arm_means[a] /= sum(1 for b in block_means if arm_of_block[b] == a)
    residual = [m - arm_means[arm_of_block[b]] for b, m in block_means.items()]
    xs = residual[:-1]
    ys = residual[1:]
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    rho1 = num / den if den > 0 else 0.0
    return {"rho1": rho1, "pass": abs(rho1) <= CRITICAL_RHO1, "skipped": False}


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def render(spec: dict[str, Any], log: list[dict[str, Any]]) -> None:
    expected = spec["expected_treatment"]
    srm = srm_check(log, expected)
    unit = unit_check(log)
    serial = serial_check(log)

    total = srm["control"] + srm["treatment"]
    pct_treat = 100.0 * srm["treatment"] / total
    pct_ctrl = 100.0 * srm["control"] / total
    print(f"experiment: {spec['experiment']}  (units={total}, rows={len(log)})")
    print(f"  expected split: control {100 * (1 - expected):.1f}% / treatment "
          f"{100 * expected:.1f}%")
    print(f"  1. allocation ratio: observed {pct_ctrl:.2f}% / {pct_treat:.2f}%  "
          f"chi2={srm['chi2']:.2f} p={srm['p']:.3g}  -> "
          f"{'PASS' if srm['pass'] else 'FAIL (SRM)'}")
    print(f"  2. analysis unit: naive SE {unit['naive_se']:.4f}, clustered SE "
          f"{unit['clustered_se']:.4f} ({unit['ratio']:.2f}x)  -> "
          f"{'PASS' if unit['pass'] else 'FAIL (unit mismatch)'}")
    if serial["skipped"]:
        print("  3. serial dependence: N/A (unit-level experiment)")
    else:
        print(f"  3. serial dependence: block-mean lag-1 rho1={serial['rho1']:.2f}  -> "
              f"{'PASS' if serial['pass'] else 'FAIL (autocorrelation)'}")

    failures = []
    if not srm["pass"]:
        failures.append(
            f"sample ratio mismatch (SRM): observed {pct_treat:.2f}% treatment vs "
            f"expected {100 * expected:.2f}%, chi2={srm['chi2']:.2f}, p={srm['p']:.3g}"
        )
    if not unit["pass"]:
        failures.append(
            f"analysis unit mismatch: clustered SE {unit['clustered_se']:.4f} is "
            f"{unit['ratio']:.2f}x the naive SE {unit['naive_se']:.4f}"
        )
    if not serial["pass"]:
        failures.append(
            f"serial dependence: block-mean lag-1 autocorrelation rho1="
            f"{serial['rho1']:.2f}"
        )
    if failures:
        print(f"\nverdict: INVALID -- {failures[0]}")
        if len(failures) > 1:
            print("  also failing: " + "; ".join(failures[1:]))
    else:
        print("\nverdict: INTERPRETABLE -- the p-value can be read, subject to "
              "the stage's evidence boundary (synthetic fixture, not a real run)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        choices=("broken", "fixed", "switchback"),
        default="broken",
    )
    parser.add_argument("--emit-log", help="write the generated log to this JSON path")
    args = parser.parse_args()

    spec = json.loads((FIXTURES / f"{args.fixture}.json").read_text())
    log = generate_log(spec)
    if args.emit_log:
        # A metrics store would persist the log with its metadata: which
        # experiment, which split was declared. The production path reads
        # this envelope, never the spec.
        envelope = {
            "experiment": spec["experiment"],
            "expected_treatment": spec["expected_treatment"],
            "rows": log,
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    render(spec, log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
