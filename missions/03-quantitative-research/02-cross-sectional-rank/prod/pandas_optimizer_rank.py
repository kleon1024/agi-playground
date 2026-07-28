"""Production companion for ``core/cross_sectional_rank.py``.

Requires ``pandas numpy cvxpy``. Groupby rank replaces readable core loops;
the optimizer imposes position caps, sector neutrality, and gross exposure
together. Sequential clipping in the core is intentionally not equivalent:
subsequent de-meaning can break a cap and clipping again breaks neutrality.
"""

from __future__ import annotations

import cvxpy as cp
import pandas as pd


def rank_signal(frame: pd.DataFrame) -> pd.Series:
    """Date-local ranks prevent level-scale drift from changing a fixed rule."""
    return frame.groupby("date")["signal"].rank(pct=True) - 0.5


def constrained_weights(alpha: pd.Series, sector: pd.Series, cap: float = 0.10) -> pd.Series:
    """Maximise alignment with alpha under simultaneous, inspectable constraints."""
    n = len(alpha)
    weights = cp.Variable(n)
    constraints = [weights <= cap, weights >= -cap, cp.sum(weights) == 0, cp.norm1(weights) <= 2]
    for label in sector.drop_duplicates():
        positions = [i for i, value in enumerate(sector) if value == label]
        constraints.append(cp.sum(weights[positions]) == 0)
    problem = cp.Problem(cp.Maximize(alpha.to_numpy() @ weights), constraints)
    problem.solve(solver="CLARABEL")
    if weights.value is None:
        raise RuntimeError(f"optimizer status: {problem.status}")
    return pd.Series(weights.value, index=alpha.index)


if __name__ == "__main__":
    print("Load a point-in-time panel, rank by date, then solve one rebalance at a time.")
