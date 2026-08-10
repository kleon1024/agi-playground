"""Production experiment validity gate over a persisted experiment log.

This path reads the log a metrics store would hand the analysis pipeline
(emit it from the core script: `core/ab_validity.py --fixture broken
--emit-log /tmp/ab-broken.json`) and runs the same three checks with the
tools a real experimentation platform uses: pandas for the grouped tables
and SciPy for the chi-square and t-tests. The core implementation remains
the contract reference because it exposes every branch without third-party
machinery; this file is what an online service would actually run, and the
verdict it prints must match the core gate's.

Requires: pandas, scipy

Run:
    python experiment_validity.py /tmp/ab-broken.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CRITICAL_SE_RATIO = 1.2
CRITICAL_RHO1 = 0.2
ALPHA = 0.05


def srm_check(df: pd.DataFrame, expected: float) -> dict[str, object]:
    """Allocation-ratio check: observed split vs the declared expected split."""
    units = df.drop_duplicates("unit")
    counts = units["arm"].value_counts().to_dict()
    n = sum(counts.values())
    exp_treat = n * expected
    exp_ctrl = n * (1.0 - expected)
    chi2, p = stats.chisquare(
        [counts.get("control", 0), counts.get("treatment", 0)],
        f_exp=[exp_ctrl, exp_treat],
    )
    return {"control": counts.get("control", 0), "treatment": counts.get("treatment", 0),
            "chi2": float(chi2), "p": float(p), "pass": p >= ALPHA}


def unit_check(df: pd.DataFrame) -> dict[str, object]:
    """Naive per-row SE vs clustered per-unit SE on the treatment effect."""
    treat = df.loc[df["arm"] == "treatment", "outcome"]
    ctrl = df.loc[df["arm"] == "control", "outcome"]
    pooled = np.sqrt(
        ((len(treat) - 1) * treat.var(ddof=1) + (len(ctrl) - 1) * ctrl.var(ddof=1))
        / (len(treat) + len(ctrl) - 2)
    )
    naive_se = pooled * math.sqrt(1 / len(treat) + 1 / len(ctrl))

    unit_means = df.groupby("unit")["outcome"].mean()
    arm_of = df.drop_duplicates("unit").set_index("unit")["arm"]
    tu = unit_means[arm_of == "treatment"]
    cu = unit_means[arm_of == "control"]
    clustered_se = math.sqrt(tu.var(ddof=1) / len(tu) + cu.var(ddof=1) / len(cu))
    ratio = clustered_se / naive_se if naive_se > 0 else float("inf")
    return {"naive_se": float(naive_se), "clustered_se": float(clustered_se),
            "ratio": float(ratio), "pass": ratio <= CRITICAL_SE_RATIO}


def serial_check(df: pd.DataFrame) -> dict[str, object]:
    """Lag-1 autocorrelation of block means (switchback experiments only)."""
    if df["block"].isna().all():
        return {"rho1": 0.0, "pass": True, "skipped": True}
    block_means = df.groupby("block")["outcome"].mean()
    arm_of = df.drop_duplicates("block").set_index("block")["arm"]
    residual = block_means - block_means.groupby(arm_of).transform("mean")
    xs, ys = residual.values[:-1], residual.values[1:]
    rho1 = float(np.corrcoef(xs, ys)[0, 1]) if len(xs) > 2 else 0.0
    return {"rho1": rho1, "pass": abs(rho1) <= CRITICAL_RHO1, "skipped": False}


def render(df: pd.DataFrame, expected: float, label: str) -> None:
    srm = srm_check(df, expected)
    unit = unit_check(df)
    serial = serial_check(df)
    total = srm["control"] + srm["treatment"]
    pct_treat = 100.0 * srm["treatment"] / total
    pct_ctrl = 100.0 * srm["control"] / total
    print(f"experiment: {label}  (units={total}, rows={len(df)})")
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
        failures.append("sample ratio mismatch (SRM)")
    if not unit["pass"]:
        failures.append(f"analysis unit mismatch ({unit['ratio']:.2f}x SE gap)")
    if not serial["pass"]:
        failures.append(f"serial dependence (rho1={serial['rho1']:.2f})")
    print(f"\nverdict: {'INVALID -- ' + failures[0] if failures else 'INTERPRETABLE'}")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: experiment_validity.py <log.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    rows = envelope["rows"]
    df = pd.DataFrame(rows)
    expected = envelope["expected_treatment"]
    render(df, expected, envelope["experiment"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
