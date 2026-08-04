"""A report generator that is allowed to say "I don't know."

Every stage before this one (00 through 08) produces an artifact: a split, a
candidate set, a score, a slate. This stage produces a *verdict* about the
mission as a whole -- and the mission's `mission.yaml` already fixed, in
advance, exactly what would count: beat both baselines by more than seed
variance, breach no guardrail, stay inside the latency and cost budget,
catalogue the failures. "The system works" is not a claim anyone can check;
this script is what turns the contract's prose into something that is.

The central design constraint is the same one
`foundations/05-is-the-difference-real/core/ablation.py` teaches for a single data
decision, applied here to a whole mission: a report that always returns a
winner has hidden the problem rather than solved it. Below, the verdict space
is not {met, not met} but {met, not met, CANNOT DETERMINE}, and the third
value names exactly which input is missing rather than silently defaulting to
one of the other two. Run this against the mission's actual current state
(the default) and it returns CANNOT DETERMINE because no integrated outcome
artifact contains the seed-level primary metric, both baselines, every
guardrail, end-to-end cost, and failure catalogue. Stage-level mechanism runs
do exist; they are deliberately insufficient for a mission verdict. That is
not a bug in the script. Manufacturing a conclusion from partial artifacts
would be worse than saying nothing.

Guardrails are checked as veto conditions, not additional scores: a headline
win on nDCG@10 with one guardrail breached renders as NOT MET, in the same
report, so it cannot be read any other way.

## The run-artifact JSON shape this script reads

    {
      "mission": "02-personalized-discovery",
      "primary_metric": {
        "name": "nDCG@10",
        "candidate": [0.412, 0.398, ...],           // one value per seed
        "baselines": {
          "popularity": [0.301, 0.309, ...],
          "item_item_cf": [0.356, 0.348, ...]
        }
      },
      "guardrails": {
        "coverage":              {"candidate": 0.87, "baseline": 0.83},
        "diversity":              {"candidate": 0.70, "baseline": 0.75},
        "cold_start":             {"candidate": 0.305, "baseline": 0.298},
        "ad_load":                {"candidate": 0.10, "baseline": 0.10},
        "demographic_features":   {"features_used": ["item_popularity_7d", ...]}
      },
      "latency_ms": {"p50": 68, "p95": 245},
      "cost_usd_per_request": 0.00052,
      "failure_cases": [
        {"segment": "...", "observation": "...", "hypothesis": "..."}
      ]
    }

Every field is optional in the sense that its absence is a valid, reportable
state (CANNOT DETERMINE, naming that field) rather than a crash.

## Guardrails come from mission.yaml, not from this file

`parse_guardrails` reads the mission's own `guardrails:` list out of
`mission.yaml` at run time -- this script does not hardcode "there are five
guardrails," it hardcodes how to *check* the guardrails mission.yaml happens
to declare, by matching a keyword in each guardrail's prose to a checker
function below. A guardrail whose text matches no known keyword is reported
as "no automated checker for this guardrail" rather than silently skipped or
silently passed -- the same discipline as the missing-input case, applied to
a single guardrail instead of the whole report. Everything that is not
sensibly re-derived from the guardrail's own prose at parse time (the metric
name, the baseline identities, the latency and cost budgets, the minimum seed
count) is a constant declared just below `CONTRACT DRIFT GUARD`, and
`check_contract_sync` refuses to produce a verdict at all if mission.yaml's
prose no longer contains the substrings those constants were read from -- so
an edit to the contract that this file was not updated to match fails loudly
instead of quietly grading against a stale rule.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

MISSION_DIR = Path(__file__).resolve().parents[2]
MISSION_YAML = MISSION_DIR / "mission.yaml"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

Z95 = 1.96  # normal-approximation critical value for a 95% interval

# --- CONTRACT DRIFT GUARD -----------------------------------------------
# These are read from mission.yaml by eye, not re-parsed at run time, because
# they are scalars embedded in prose rather than a list this script can walk.
# check_contract_sync() below is the tripwire: if mission.yaml stops
# containing the substrings these constants came from, the report refuses to
# run rather than silently grading against numbers the contract no longer
# states.
PRIMARY_METRIC_NAME = "nDCG@10"
MIN_SEEDS = 5
BASELINES = {
    "popularity": "global popularity ranking",
    "item_item_cf": "item-item collaborative-filtering baseline",
}
LATENCY_P50_MS = 100
LATENCY_P95_MS = 300
COST_BUDGET_USD = 0.001
BANNED_DEMOGRAPHIC_FEATURES = {
    "age", "gender", "race", "ethnicity", "income", "religion",
    "marital_status", "sexual_orientation", "disability_status", "national_origin",
}


class ContractDriftError(RuntimeError):
    """mission.yaml no longer matches this script's hardcoded constants."""


def check_contract_sync(mission_text: str) -> None:
    checks = {
        "primary metric name": PRIMARY_METRIC_NAME in mission_text,
        "minimum seed count": "at least 5 seeds" in mission_text,
        "popularity baseline": BASELINES["popularity"] in mission_text,
        "item-item baseline": BASELINES["item_item_cf"] in mission_text,
        "latency p50 budget": "under 100ms" in mission_text,
        "latency p95 budget": "under 300ms" in mission_text,
        "cost budget": "$0.001" in mission_text,
    }
    drifted = [name for name, ok in checks.items() if not ok]
    if drifted:
        raise ContractDriftError(
            "mission.yaml no longer matches this report generator's constants "
            f"for: {', '.join(drifted)}. Update report.py's constants before "
            "trusting any verdict it produces."
        )


# --- minimal mission.yaml reader ----------------------------------------
# Not a general YAML parser: mission.yaml only ever uses folded scalars (`>`)
# and one-level dash lists, and these two functions know only those shapes.

def _raw_block(text: str, key: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:[ \t]*>?[ \t]*\n((?:[ \t]+.*\n|[ \t]*\n)*)")
    m = pattern.search(text)
    if not m:
        raise ValueError(f"mission.yaml has no top-level key {key!r}")
    return m.group(1)


def parse_guardrails(mission_text: str) -> list[str]:
    """Every bullet under `guardrails:`, each folded into one string."""
    items: list[str] = []
    current: list[str] | None = None
    for line in _raw_block(mission_text, "guardrails").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if line.lstrip().startswith("- "):
            if current is not None:
                items.append(" ".join(current))
            current = [line.lstrip()[2:].strip()]
        elif current is not None:
            current.append(stripped)
    if current is not None:
        items.append(" ".join(current))
    return items


def load_mission_text() -> str:
    return MISSION_YAML.read_text()


# --- statistics: does the candidate beat a baseline by more than noise? ---

@dataclass
class BaselineComparison:
    label: str
    mean_candidate: float
    mean_baseline: float
    diff: float
    margin: float
    detectable: bool


def compare_to_baseline(candidate: list[float], baseline: list[float], label: str) -> BaselineComparison:
    mean_c, mean_b = statistics.mean(candidate), statistics.mean(baseline)
    var_c, var_b = statistics.variance(candidate), statistics.variance(baseline)
    se = ((var_c / len(candidate)) + (var_b / len(baseline))) ** 0.5
    margin = Z95 * se
    diff = mean_c - mean_b
    return BaselineComparison(label, mean_c, mean_b, diff, margin, abs(diff) > margin)


# --- guardrail checkers ---------------------------------------------------
# Each returns ("pass" | "breach", detail). A checker is matched to a
# guardrail's prose by keyword in _match_checker, never by position, so
# reordering guardrails in mission.yaml cannot silently swap which check runs
# against which bullet.

def _check_not_below_baseline(entry: dict, _text: str) -> tuple[str, str]:
    c, b = entry["candidate"], entry["baseline"]
    if c >= b:
        return "pass", f"candidate {c:.3f} >= baseline {b:.3f}"
    return "breach", f"candidate {c:.3f} < baseline {b:.3f} -- degrades below the floor this guardrail protects"


def _check_diversity_regression(entry: dict, text: str) -> tuple[str, str]:
    c, b = entry["candidate"], entry["baseline"]
    m = re.search(r"(\d+)%", text)
    pct = int(m.group(1)) if m else 10  # the guardrail's own stated threshold, read from its prose
    threshold = b * (1 - pct / 100)
    if c >= threshold:
        return "pass", f"candidate {c:.3f} within {pct}% of baseline {b:.3f} (floor {threshold:.3f})"
    return "breach", f"candidate {c:.3f} regressed more than {pct}% below baseline {b:.3f} (floor {threshold:.3f})"


def _check_held_fixed(entry: dict, _text: str, tol: float = 0.02) -> tuple[str, str]:
    c, b = entry["candidate"], entry["baseline"]
    if abs(c - b) <= tol:
        return "pass", f"ad load held fixed: candidate {c:.3f} vs baseline {b:.3f}"
    return "breach", f"ad load differs ({c:.3f} vs {b:.3f}) -- organic-quality comparison is confounded by revenue"


def _check_no_banned_features(entry: dict, _text: str) -> tuple[str, str]:
    used = set(entry.get("features_used", []))
    hit = used & BANNED_DEMOGRAPHIC_FEATURES
    if hit:
        return "breach", f"banned demographic feature(s) used as ranking features: {sorted(hit)}"
    return "pass", "no banned demographic feature present in features_used"


_CHECKER_KEYWORDS: list[tuple[str, str, callable]] = [
    ("demographic", "demographic_features", _check_no_banned_features),
    ("ad load", "ad_load", _check_held_fixed),
    ("cold-start", "cold_start", _check_not_below_baseline),
    ("cold start", "cold_start", _check_not_below_baseline),
    ("diversity", "diversity", _check_diversity_regression),
    ("coverage", "coverage", _check_not_below_baseline),
]


def _match_checker(guardrail_text: str) -> tuple[str, callable] | None:
    low = guardrail_text.lower()
    for keyword, artifact_key, fn in _CHECKER_KEYWORDS:
        if keyword in low:
            return artifact_key, fn
    return None


# --- the verdict -----------------------------------------------------------

@dataclass
class GuardrailResult:
    text: str
    key: str | None
    status: str  # "pass" | "breach" | "missing" | "no_checker"
    detail: str


@dataclass
class Verdict:
    outcome: str  # "MET" | "NOT MET" | "CANNOT DETERMINE"
    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    guardrails: list[GuardrailResult] = field(default_factory=list)
    baseline_comparisons: dict[str, BaselineComparison] = field(default_factory=dict)
    latency_ms: dict | None = None
    cost_usd_per_request: float | None = None
    failure_cases: list | None = None


def evaluate(artifact: dict | None, mission_text: str) -> Verdict:
    check_contract_sync(mission_text)
    guardrail_specs = parse_guardrails(mission_text)

    if artifact is None:
        return Verdict(
            outcome="CANNOT DETERMINE",
            missing=[
                (
                    "no integrated mission-outcome JSON artifact exists. Stage-level "
                    "mechanism and latency runs are present, but none contains the "
                    "seed-level nDCG@10 for the candidate and both baselines, every "
                    "guardrail measurement, end-to-end cost, and the required "
                    "failure-case catalogue"
                )
            ],
            guardrails=[GuardrailResult(g, None, "missing", "no run artifact to read") for g in guardrail_specs],
        )

    missing: list[str] = []

    # primary metric
    baseline_comparisons: dict[str, BaselineComparison] = {}
    pm = artifact.get("primary_metric")
    if not pm or "candidate" not in pm or "baselines" not in pm:
        missing.append(f"primary_metric: artifact has no candidate/baseline seed arrays for {PRIMARY_METRIC_NAME}")
    else:
        candidate = pm["candidate"]
        if len(candidate) < MIN_SEEDS:
            missing.append(
                f"primary_metric: candidate has {len(candidate)} seed(s), contract requires at least {MIN_SEEDS}"
            )
        else:
            for key, label in BASELINES.items():
                arr = pm["baselines"].get(key)
                if arr is None:
                    missing.append(f"primary_metric: no baseline samples for '{label}' (expected key '{key}')")
                elif len(arr) < MIN_SEEDS:
                    missing.append(
                        f"primary_metric: baseline '{key}' has {len(arr)} seed(s), "
                        f"contract requires at least {MIN_SEEDS}"
                    )
                else:
                    baseline_comparisons[key] = compare_to_baseline(candidate, arr, label)

    # guardrails
    artifact_guardrails = artifact.get("guardrails", {})
    guardrail_results: list[GuardrailResult] = []
    for text in guardrail_specs:
        matched = _match_checker(text)
        if matched is None:
            guardrail_results.append(GuardrailResult(text, None, "no_checker", "no automated checker implemented for this guardrail; requires manual audit"))
            continue
        key, fn = matched
        entry = artifact_guardrails.get(key)
        if entry is None:
            guardrail_results.append(GuardrailResult(text, key, "missing", f"artifact has no 'guardrails.{key}' measurement"))
            missing.append(f"guardrails.{key}: not present in run artifact")
            continue
        status, detail = fn(entry, text)
        guardrail_results.append(GuardrailResult(text, key, status, detail))

    # latency / cost / failure cases
    latency = artifact.get("latency_ms")
    if not latency or "p50" not in latency or "p95" not in latency:
        missing.append("latency_ms: not measured")
    cost = artifact.get("cost_usd_per_request")
    if cost is None:
        missing.append("cost_usd_per_request: not measured")
    failure_cases = artifact.get("failure_cases")
    if not failure_cases:
        missing.append(
            "failure_cases: none catalogued -- a report with no failure cases "
            "has either not looked or is not telling you"
        )

    if missing:
        return Verdict(
            outcome="CANNOT DETERMINE",
            missing=missing,
            guardrails=guardrail_results,
            baseline_comparisons=baseline_comparisons,
            latency_ms=latency,
            cost_usd_per_request=cost,
            failure_cases=failure_cases,
        )

    # Every required input is present. Decide, with guardrails as vetoes.
    reasons: list[str] = []
    for key, cmp_ in baseline_comparisons.items():
        if not (cmp_.detectable and cmp_.diff > 0):
            reasons.append(
                f"does not beat baseline '{key}' ({cmp_.label}) by more than seed "
                f"variance: diff={cmp_.diff:+.4f}, 95% margin=+/-{cmp_.margin:.4f}"
            )
    for g in guardrail_results:
        if g.status == "breach":
            reasons.append(f"guardrail breached ({g.key}): {g.detail}")
        elif g.status == "no_checker":
            reasons.append(f"guardrail not machine-checked, requires manual audit: {g.text}")
    if latency["p50"] > LATENCY_P50_MS:
        reasons.append(f"latency p50 {latency['p50']}ms exceeds budget {LATENCY_P50_MS}ms")
    if latency["p95"] > LATENCY_P95_MS:
        reasons.append(f"latency p95 {latency['p95']}ms exceeds budget {LATENCY_P95_MS}ms")
    if cost > COST_BUDGET_USD:
        reasons.append(f"cost ${cost:.5f}/request exceeds budget ${COST_BUDGET_USD}/request")

    outcome = "NOT MET" if reasons else "MET"
    return Verdict(
        outcome=outcome,
        reasons=reasons,
        guardrails=guardrail_results,
        baseline_comparisons=baseline_comparisons,
        latency_ms=latency,
        cost_usd_per_request=cost,
        failure_cases=failure_cases,
    )


# --- rendering and CLI ------------------------------------------------------

def find_real_artifact() -> dict | None:
    """Scan this mission's stage directories for a runs/*.json artifact.

    Returns None when stage-level runs exist but no integrated outcome JSON
    artifact has been published.
    """
    for runs_dir in sorted(MISSION_DIR.glob("*/runs")):
        for candidate in sorted(runs_dir.glob("*.json")):
            return json.loads(candidate.read_text())
    return None


def render(verdict: Verdict) -> str:
    lines = [f"VERDICT: {verdict.outcome}", ""]

    if verdict.missing:
        lines.append("Cannot determine because the following inputs are missing:")
        for m in verdict.missing:
            lines.append(f"  - {m}")
        lines.append("")

    if verdict.baseline_comparisons:
        lines.append(f"Primary metric ({PRIMARY_METRIC_NAME}):")
        for key, cmp_ in verdict.baseline_comparisons.items():
            verb = "beats" if (cmp_.detectable and cmp_.diff > 0) else "does NOT beat"
            lines.append(
                f"  vs {key} ({cmp_.label}): candidate={cmp_.mean_candidate:.4f} "
                f"baseline={cmp_.mean_baseline:.4f} diff={cmp_.diff:+.4f} "
                f"+/-{cmp_.margin:.4f} (95%) -- {verb} by more than seed variance"
            )
        lines.append("")

    if verdict.guardrails:
        lines.append("Guardrails:")
        for g in verdict.guardrails:
            lines.append(f"  [{g.status.upper():^10}] {g.text}")
            lines.append(f"               {g.detail}")
        lines.append("")

    if verdict.latency_ms is not None:
        lines.append(
            f"Latency: p50={verdict.latency_ms.get('p50')}ms (budget {LATENCY_P50_MS}ms), "
            f"p95={verdict.latency_ms.get('p95')}ms (budget {LATENCY_P95_MS}ms)"
        )
    if verdict.cost_usd_per_request is not None:
        lines.append(f"Cost: ${verdict.cost_usd_per_request:.5f}/request (budget ${COST_BUDGET_USD}/request)")
    if verdict.failure_cases:
        lines.append(f"Failure cases catalogued: {len(verdict.failure_cases)}")
        for fc in verdict.failure_cases:
            lines.append(f"  - {fc.get('segment')}: {fc.get('observation')}")

    if verdict.reasons:
        lines.append("")
        lines.append("Reasons the verdict is NOT MET:")
        for r in verdict.reasons:
            lines.append(f"  - {r}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--fixture",
        choices=["met", "breached"],
        help="evaluate a bundled synthetic complete fixture instead of the mission's real state",
    )
    source.add_argument(
        "--artifact",
        type=Path,
        help="evaluate an arbitrary run-artifact JSON file at this path",
    )
    args = parser.parse_args()

    mission_text = load_mission_text()

    if args.fixture:
        path = FIXTURES_DIR / f"{args.fixture}.json"
        artifact = json.loads(path.read_text())
        print(f"# Evaluating synthetic fixture: {path.name} -- NOT a real run\n")
    elif args.artifact:
        artifact = json.loads(args.artifact.read_text())
        print(f"# Evaluating supplied artifact: {args.artifact}\n")
    else:
        artifact = find_real_artifact()
        print("# Evaluating this mission's actual current state (scanned every stage's runs/)\n")

    verdict = evaluate(artifact, mission_text)
    print(render(verdict))
    return {"MET": 0, "NOT MET": 1, "CANNOT DETERMINE": 2}[verdict.outcome]


if __name__ == "__main__":
    sys.exit(main())
