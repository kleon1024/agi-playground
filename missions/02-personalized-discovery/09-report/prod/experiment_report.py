"""Production experiment report over a persisted mission artifact.

This path uses pandas for arm-level tables and SciPy for Welch tests. The core
implementation remains the contract reference because it exposes every branch
without third-party machinery. A production service would persist the same
artifact shape in a metrics store and render this result in Evidently, Arize,
or a warehouse-backed internal report.

Requires: pandas, scipy

Run:
    python experiment_report.py ../core/fixtures/met.json
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from scipy import stats

BASELINES = ("popularity", "item_item_cf")
MIN_SEEDS = 5
P50_BUDGET_MS = 100
P95_BUDGET_MS = 300
COST_BUDGET_USD = 0.001
BANNED_FEATURES = {
    "age",
    "disability_status",
    "ethnicity",
    "gender",
    "income",
    "marital_status",
    "national_origin",
    "race",
    "religion",
    "sexual_orientation",
}


@dataclass(frozen=True)
class Comparison:
    baseline: str
    candidate_mean: float
    baseline_mean: float
    difference: float
    p_value: float


def normal_power(effect: float, standard_error: float, alpha: float = 0.05) -> float:
    """Approximate two-sided power at the observed standard error.

    This is diagnostic, not a substitute for a pre-experiment power analysis:
    planning must use a declared minimum detectable effect rather than the
    observed effect.
    """
    if standard_error <= 0:
        return 1.0 if effect else alpha
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    noncentrality = abs(effect) / standard_error
    return float(stats.norm.sf(z_alpha - noncentrality) + stats.norm.cdf(-z_alpha - noncentrality))


def compare_arms(candidate: list[float], baseline: list[float], name: str) -> Comparison:
    if len(candidate) < MIN_SEEDS or len(baseline) < MIN_SEEDS:
        raise ValueError(f"{name}: at least {MIN_SEEDS} values per arm are required")
    test = stats.ttest_ind(candidate, baseline, equal_var=False)
    return Comparison(
        baseline=name,
        candidate_mean=float(pd.Series(candidate).mean()),
        baseline_mean=float(pd.Series(baseline).mean()),
        difference=float(pd.Series(candidate).mean() - pd.Series(baseline).mean()),
        p_value=float(test.pvalue),
    )


def guardrail_failures(artifact: dict[str, Any]) -> list[str]:
    guardrails = artifact["guardrails"]
    failures: list[str] = []
    for key in ("coverage", "cold_start"):
        if guardrails[key]["candidate"] < guardrails[key]["baseline"]:
            failures.append(f"{key}: candidate is below baseline")
    diversity = guardrails["diversity"]
    if diversity["candidate"] < 0.9 * diversity["baseline"]:
        failures.append("diversity: regression exceeds 10%")
    ad_load = guardrails["ad_load"]
    if not math.isclose(ad_load["candidate"], ad_load["baseline"], abs_tol=1e-12):
        failures.append("ad_load: differs across arms")
    used = set(guardrails["demographic_features"]["features_used"])
    if overlap := sorted(used & BANNED_FEATURES):
        failures.append(f"demographic_features: banned features used: {', '.join(overlap)}")
    return failures


def evaluate(artifact: dict[str, Any]) -> tuple[str, pd.DataFrame, list[str]]:
    primary = artifact["primary_metric"]
    candidate = primary["candidate"]
    comparisons = [
        compare_arms(candidate, primary["baselines"][name], name)
        for name in BASELINES
    ]
    rows = []
    for comparison in comparisons:
        candidate_sd = float(pd.Series(candidate).std(ddof=1))
        baseline = primary["baselines"][comparison.baseline]
        baseline_sd = float(pd.Series(baseline).std(ddof=1))
        se = math.sqrt(candidate_sd**2 / len(candidate) + baseline_sd**2 / len(baseline))
        rows.append(
            {
                **comparison.__dict__,
                "observed_power": normal_power(comparison.difference, se),
            }
        )
    table = pd.DataFrame(rows).set_index("baseline")

    failures = guardrail_failures(artifact)
    latency = artifact["latency_ms"]
    if latency["p50"] > P50_BUDGET_MS or latency["p95"] > P95_BUDGET_MS:
        failures.append("latency: declared budget exceeded")
    if artifact["cost_usd_per_request"] > COST_BUDGET_USD:
        failures.append("cost: declared budget exceeded")
    if not artifact.get("failure_cases"):
        failures.append("failure_cases: none catalogued")
    for comparison in comparisons:
        if comparison.difference <= 0 or comparison.p_value >= 0.05:
            failures.append(f"{comparison.baseline}: candidate does not clear the 5% Welch test")
    return ("NOT MET" if failures else "MET"), table, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text())
    verdict, table, failures = evaluate(artifact)
    print(table.to_string(float_format=lambda value: f"{value:.4f}"))
    print(f"\nVERDICT: {verdict}")
    for failure in failures:
        print(f"- {failure}")


if __name__ == "__main__":
    main()
