"""The report stage: read a run artifact, apply the mission's own contract, and
say MET, NOT MET, or CANNOT DETERMINE — never a number without one of the three.

This stage is not free to invent a verdict. `mission.yaml` declared the
baselines and the guardrails before any of stages 00-04 existed, and this
script's only job is to hold the actual measured artifact against that
pre-declared bar and refuse to soften the comparison. Every threshold checked
below is quoted from `mission.yaml`, not paraphrased, in the `GUARDRAILS`
table and in `evaluate_primary_metric`.

The documented artifact shape this stage reads
-------------------------------------------------------------------------
A JSON object with five top-level sections. `REQUIRED_FIELDS` below is the
executable version of this list; the two stay in sync by hand, and a missing
field here is a missing field there.

    {
      "baselines": {
        "buy_and_hold":   {"sharpe_net_folds": [float, ...>=5],
                            "max_drawdown": {"depth": float, "start": str,
                                             "trough": str, "end": str}},
        "momentum_12_1":  {"sharpe_net_folds": [float, ...>=5]}
      },
      "candidate": {
        "sharpe_net_folds": [float, ...>=5],
        "sharpe_gross_folds": [float, ...same length],
        "deflated_sharpe": float,
        "deflated_sharpe_significance": float,   # achieved confidence level
        "n_variants_searched": int,
        "max_drawdown": {"depth": float, "start": str, "trough": str, "end": str},
        "max_position_pct_of_adv": float,
        "point_in_time_violations": int,
        "universe_survivorship_bias_free": bool
      },
      "cost": {"data_and_compute_usd_per_fold": float,
               "modeled_txn_cost_bps": float,
               "modeled_impact_participation_rate": float},
      "latency": {"p50_ms": float, "p95_ms": float},
      "regimes": [
        {"name": str, "start": str, "end": str,
         "candidate_sharpe": float, "momentum_sharpe": float,
         "buy_hold_sharpe": float},
        ...
      ]
    }

In a fully built mission, stage 04 (`cost-and-capacity`) would be the last
producer feeding this shape — signal, ranking, validation, and cost all
folded into one artifact. Nothing yet emits it: stages 01-04 are candidate
signal construction, cross-sectional ranking, walk-forward validation, and
cost modeling, and this report stage was written and run before any of them
existed. Pointing this script at the path such an artifact would live at,
by default, is exactly how it demonstrates the refusal below on the mission's
actual current state rather than on a rigged example.

Run:
    python report.py                                   # real mission state
    python report.py --artifact fixtures/complete_met.json
    python report.py --artifact fixtures/complete_breached.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

# The significance level `mission.yaml`'s deflated-Sharpe guardrail asks for
# "a stated significance level" without naming one — that number is this
# report's to declare, and 0.95 is the value it commits to. Disclosed here
# because a report that quietly picks its own bar is exactly the kind of
# unstated tuning this repository's chapters are built to avoid.
DEFLATED_SHARPE_SIGNIFICANCE = 0.95

MIN_FOLDS = 5  # "a single fold is not a result" — mission.yaml, primary_metric

DEFAULT_ARTIFACT = Path(__file__).resolve().parent.parent / "runs" / "mission-outcome.json"

# Dotted paths this report cannot proceed without, and what each one is for.
REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("baselines.buy_and_hold.sharpe_net_folds", "passive-floor baseline, per fold"),
    ("baselines.buy_and_hold.max_drawdown.depth", "passive-floor drawdown, for the drawdown guardrail"),
    ("baselines.momentum_12_1.sharpe_net_folds", "the baseline that actually has to be beaten, per fold"),
    ("candidate.sharpe_net_folds", "the number the primary metric is decided on"),
    ("candidate.sharpe_gross_folds", "required beside net, per the net-vs-gross guardrail"),
    ("candidate.deflated_sharpe", "the number that matters, not the raw Sharpe of the winner"),
    ("candidate.deflated_sharpe_significance", "achieved confidence level for the deflated Sharpe"),
    ("candidate.n_variants_searched", "what the deflated Sharpe is correcting for"),
    ("candidate.max_drawdown.depth", "risk-taking guardrail input"),
    ("candidate.max_position_pct_of_adv", "capacity guardrail input"),
    ("candidate.point_in_time_violations", "point-in-time integrity guardrail input"),
    ("candidate.universe_survivorship_bias_free", "survivorship-bias guardrail input"),
    ("cost.data_and_compute_usd_per_fold", "cost budget, real dollars"),
    ("cost.modeled_txn_cost_bps", "cost budget, modeled transaction cost"),
    ("cost.modeled_impact_participation_rate", "cost budget, modeled market impact"),
    ("latency.p50_ms", "latency budget, real measurement"),
    ("latency.p95_ms", "latency budget, real measurement"),
    ("regimes", "the mandatory regime-level failure-case breakdown"),
]


def _dig(obj: Any, dotted_path: str) -> Any:
    """Walk a dotted path through nested dicts; return a sentinel on any miss."""
    node = obj
    for key in dotted_path.split("."):
        if not isinstance(node, dict) or key not in node:
            return _MISSING
        node = node[key]
    return node


_MISSING = object()


def load_artifact(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text().strip()
    if not text:
        return None
    return json.loads(text)


def find_missing_inputs(artifact: dict | None) -> list[str]:
    """Every required dotted path this artifact does not actually supply."""
    if artifact is None:
        return [f"{path} ({why})" for path, why in REQUIRED_FIELDS]
    missing = []
    for path, why in REQUIRED_FIELDS:
        if _dig(artifact, path) is _MISSING:
            missing.append(f"{path} ({why})")
    return missing


def _fold_check(artifact: dict) -> str | None:
    """`mission.yaml`: "a single fold is not a result" — enforce >= 5 folds
    on every series the primary metric and guardrails are computed from."""
    series = {
        "baselines.buy_and_hold.sharpe_net_folds": artifact["baselines"]["buy_and_hold"]["sharpe_net_folds"],
        "baselines.momentum_12_1.sharpe_net_folds": artifact["baselines"]["momentum_12_1"]["sharpe_net_folds"],
        "candidate.sharpe_net_folds": artifact["candidate"]["sharpe_net_folds"],
    }
    for name, values in series.items():
        if len(values) < MIN_FOLDS:
            return f"{name} has {len(values)} fold(s); mission.yaml requires at least {MIN_FOLDS}"
    return None


# ---------------------------------------------------------------------------
# Primary metric: beat BOTH baselines, by more than fold-to-fold noise
# ---------------------------------------------------------------------------


class BaselineResult:
    def __init__(self, name: str, baseline_mean: float, candidate_mean: float,
                 candidate_stdev: float, margin: float, passed: bool):
        self.name = name
        self.baseline_mean = baseline_mean
        self.candidate_mean = candidate_mean
        self.candidate_stdev = candidate_stdev
        self.margin = margin
        self.passed = passed


def evaluate_primary_metric(artifact: dict) -> list[BaselineResult]:
    """acceptance: "Beats BOTH baselines on net-of-cost Sharpe by more than
    the fold-to-fold standard deviation." The fold-to-fold standard deviation
    used here is the candidate's own net-Sharpe spread across folds — the
    same nuisance quantity `foundations/is-the-difference-real` measures for a
    data-mixture decision, applied here to a trading-signal decision instead.
    A margin no larger than that spread is exactly the "this could just be
    the fold you happened to draw" case the harness exists to catch.
    """
    candidate_folds = artifact["candidate"]["sharpe_net_folds"]
    candidate_mean = statistics.mean(candidate_folds)
    candidate_stdev = statistics.stdev(candidate_folds)
    results = []
    for key, label in (("buy_and_hold", "buy-and-hold (passive floor)"),
                        ("momentum_12_1", "12-1 momentum (the baseline that matters)")):
        baseline_folds = artifact["baselines"][key]["sharpe_net_folds"]
        baseline_mean = statistics.mean(baseline_folds)
        margin = candidate_mean - baseline_mean
        results.append(BaselineResult(
            name=label,
            baseline_mean=baseline_mean,
            candidate_mean=candidate_mean,
            candidate_stdev=candidate_stdev,
            margin=margin,
            passed=margin > candidate_stdev,
        ))
    return results


# ---------------------------------------------------------------------------
# Guardrails: vetoes, not scores. One failure fails the whole report.
# ---------------------------------------------------------------------------


class GuardrailResult:
    def __init__(self, quote: str, threshold: str, measured: str, passed: bool):
        self.quote = quote
        self.threshold = threshold
        self.measured = measured
        self.passed = passed


def evaluate_guardrails(artifact: dict) -> list[GuardrailResult]:
    c = artifact["candidate"]
    baseline_dd = artifact["baselines"]["buy_and_hold"]["max_drawdown"]["depth"]
    results = []

    # Quoted verbatim from mission.yaml's `guardrails:` list.
    results.append(GuardrailResult(
        quote='"a strategy profitable only before costs fails this guardrail '
              'outright, regardless of its gross number"',
        threshold="net-of-cost Sharpe > 0",
        measured=f"net {statistics.mean(c['sharpe_net_folds']):.2f} / "
                 f"gross {statistics.mean(c['sharpe_gross_folds']):.2f} (mean across folds)",
        passed=statistics.mean(c["sharpe_net_folds"]) > 0,
    ))

    results.append(GuardrailResult(
        quote='"Per-name position size must not exceed 5% of that name\'s '
              'trailing 20-day average dollar volume"',
        threshold="<= 5% of trailing 20-day ADV",
        measured=f"{c['max_position_pct_of_adv'] * 100:.1f}% of trailing 20-day ADV",
        passed=c["max_position_pct_of_adv"] <= 0.05,
    ))

    dd_threshold = 1.5 * baseline_dd
    results.append(GuardrailResult(
        quote='"Maximum drawdown across folds must not exceed 1.5x the '
              'passive baseline\'s drawdown over the same folds"',
        threshold=f"<= {dd_threshold * 100:.1f}% (1.5x baseline's {baseline_dd * 100:.1f}%)",
        measured=f"{c['max_drawdown']['depth'] * 100:.1f}% "
                 f"({c['max_drawdown']['start']} to {c['max_drawdown']['trough']})",
        passed=c["max_drawdown"]["depth"] <= dd_threshold,
    ))

    results.append(GuardrailResult(
        quote='"The deflated Sharpe ratio must stay positive at a stated '
              'significance level after correcting for the number of variants '
              'tried — an in-sample Sharpe with no deflated counterpart '
              'reported is treated as a failed guardrail, not a missing one"',
        threshold=f"deflated Sharpe > 0 at >= {DEFLATED_SHARPE_SIGNIFICANCE:.0%} "
                  f"significance (this report's declared bar; mission.yaml names "
                  f"the requirement, not the number)",
        measured=f"deflated Sharpe {c['deflated_sharpe']:.2f} at "
                 f"{c['deflated_sharpe_significance']:.0%}, "
                 f"over {c['n_variants_searched']} variants searched",
        passed=c["deflated_sharpe"] > 0 and c["deflated_sharpe_significance"] >= DEFLATED_SHARPE_SIGNIFICANCE,
    ))

    results.append(GuardrailResult(
        quote='"every datum a signal consumes at decision date t must carry a '
              'public availability timestamp at or before t, and any violation '
              'invalidates the fold it occurred in"',
        threshold="zero violations",
        measured=f"{c['point_in_time_violations']} violation(s)",
        passed=c["point_in_time_violations"] == 0,
    ))

    results.append(GuardrailResult(
        quote='"The backtest universe must include every name that was ever a '
              'member during the study window, not only names that survived to '
              'today"',
        threshold="survivorship-bias-free universe confirmed",
        measured="confirmed" if c["universe_survivorship_bias_free"] else "NOT confirmed",
        passed=bool(c["universe_survivorship_bias_free"]),
    ))

    return results


def regime_breakdown(artifact: dict) -> tuple[list[dict], dict]:
    regimes = artifact["regimes"]
    worst = min(regimes, key=lambda r: r["candidate_sharpe"])
    return regimes, worst


# ---------------------------------------------------------------------------
# Assembling and rendering the verdict
# ---------------------------------------------------------------------------


def render_report(artifact_path: Path) -> tuple[str, str]:
    """Return (report_text, verdict) where verdict is one of
    "MET", "NOT MET", "CANNOT DETERMINE"."""
    artifact = load_artifact(artifact_path)
    missing = find_missing_inputs(artifact)
    lines = [f"Mission 03 outcome report — artifact: {artifact_path}", "=" * 72]

    if missing:
        lines.append("")
        lines.append("VERDICT: CANNOT DETERMINE")
        lines.append("")
        lines.append("This report will not guess. The following inputs are missing:")
        for m in missing:
            lines.append(f"  - {m}")
        lines.append("")
        lines.append(
            "No stage in this mission has produced this artifact yet — stages "
            "01-04 (signal, ranking, validation, cost) are what would populate "
            "it. A report with a missing baseline, guardrail input, or regime "
            "breakdown is not a cautious report; it is a wrong one wearing a "
            "confident verdict, which is why this stage refuses to render one."
        )
        return "\n".join(lines), "CANNOT DETERMINE"

    fold_problem = _fold_check(artifact)
    if fold_problem:
        lines.append("")
        lines.append("VERDICT: CANNOT DETERMINE")
        lines.append("")
        lines.append(f"Insufficient folds: {fold_problem}")
        return "\n".join(lines), "CANNOT DETERMINE"

    baseline_results = evaluate_primary_metric(artifact)
    guardrail_results = evaluate_guardrails(artifact)
    regimes, worst_regime = regime_breakdown(artifact)
    c = artifact["candidate"]

    lines.append("")
    lines.append("1. Performance against each baseline (net-of-cost Sharpe, mean across folds)")
    lines.append("-" * 72)
    for b in baseline_results:
        verdict = "beats" if b.passed else "does NOT beat"
        lines.append(
            f"  vs {b.name}: candidate {b.candidate_mean:.2f} (sd {b.candidate_stdev:.2f}) "
            f"vs baseline {b.baseline_mean:.2f} -> margin {b.margin:+.2f} -> {verdict} "
            f"the fold-to-fold noise band"
        )

    lines.append("")
    lines.append("2. Every guardrail, threshold vs. measured (a veto, not a score)")
    lines.append("-" * 72)
    for g in guardrail_results:
        status = "PASS" if g.passed else "FAIL"
        lines.append(f"  [{status}] {g.quote}")
        lines.append(f"         threshold: {g.threshold}")
        lines.append(f"         measured:  {g.measured}")

    lines.append("")
    lines.append("3. Drawdowns, with dates")
    lines.append("-" * 72)
    cd = c["max_drawdown"]
    bd = artifact["baselines"]["buy_and_hold"]["max_drawdown"]
    lines.append(
        f"  candidate:      {cd['depth'] * 100:.1f}% drawdown, "
        f"{cd['start']} -> trough {cd['trough']} -> recovered {cd['end']}"
    )
    lines.append(
        f"  buy-and-hold:   {bd['depth'] * 100:.1f}% drawdown, "
        f"{bd['start']} -> trough {bd['trough']} -> recovered {bd['end']}"
    )

    lines.append("")
    lines.append("4. Regime-level failure cases (the mandatory section)")
    lines.append("-" * 72)
    for r in regimes:
        marker = " <- worst regime" if r is worst_regime else ""
        lines.append(
            f"  {r['name']} ({r['start']} to {r['end']}): candidate Sharpe "
            f"{r['candidate_sharpe']:.2f}, momentum {r['momentum_sharpe']:.2f}, "
            f"buy-and-hold {r['buy_hold_sharpe']:.2f}{marker}"
        )
    lines.append(
        "  An aggregate Sharpe averages across all of the above; it is the "
        "single least informative number in this report on its own."
    )

    lines.append("")
    lines.append("5. Cost and latency (measured, not estimated)")
    lines.append("-" * 72)
    cost = artifact["cost"]
    latency = artifact["latency"]
    lines.append(
        f"  compute: ${cost['data_and_compute_usd_per_fold']:.2f}/fold; "
        f"modeled txn cost {cost['modeled_txn_cost_bps']:.1f}bps; "
        f"modeled impact participation rate {cost['modeled_impact_participation_rate']:.2%}"
    )
    lines.append(f"  latency: p50 {latency['p50_ms']:.0f}ms, p95 {latency['p95_ms']:.0f}ms")
    lines.append(
        "  mission.yaml states what to measure here but not a numeric ceiling "
        "to gate on, so this report can confirm these were measured and cannot "
        "veto on them the way it does the guardrails above."
    )

    all_baselines_beaten = all(b.passed for b in baseline_results)
    all_guardrails_passed = all(g.passed for g in guardrail_results)
    verdict = "MET" if (all_baselines_beaten and all_guardrails_passed) else "NOT MET"

    lines.append("")
    lines.append(f"VERDICT: {verdict}")
    if verdict == "NOT MET":
        reasons = []
        if not all_baselines_beaten:
            reasons.append("did not clear the primary-metric margin over both baselines")
        if not all_guardrails_passed:
            failed = [g for g in guardrail_results if not g.passed]
            reasons.append(
                f"{len(failed)} guardrail(s) breached: "
                + "; ".join(g.quote for g in failed)
            )
        lines.append(
            "  A strategy that clears the return hurdle while breaching even "
            "one guardrail is a failure. " + " ".join(reasons)
        )

    return "\n".join(lines), verdict


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT,
                         help="path to the run artifact JSON (default: where "
                              "stage 04 would have written it)")
    args = parser.parse_args()
    report_text, _verdict = render_report(args.artifact)
    print(report_text)


if __name__ == "__main__":
    main()
