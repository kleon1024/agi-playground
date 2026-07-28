"""Fit impact from fills, then optimize expected costs inside position sizing."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def fit_square_root_impact(participation: np.ndarray, slippage: np.ndarray, volatility: np.ndarray) -> float:
    """Estimate Y from the firm's timestamped fills, not this lesson's assumption."""
    x = volatility * np.sqrt(np.maximum(participation, 1e-12))
    return float(np.dot(x, slippage) / np.dot(x, x))


def cost_aware_weights(alpha: np.ndarray, adv: np.ndarray, volatility: np.ndarray, gross: float = 1.0) -> np.ndarray:
    """Costs enter the objective; subtracting them after optimizing changes the answer."""
    def objective(w):
        turnover = np.abs(w)
        impact = np.sum(0.6 * volatility * np.sqrt(turnover / np.maximum(adv, 1.0)) * turnover)
        return -float(alpha @ w) + impact
    result = minimize(objective, np.zeros_like(alpha), constraints={"type": "ineq", "fun": lambda w: gross - np.abs(w).sum()})
    return result.x
