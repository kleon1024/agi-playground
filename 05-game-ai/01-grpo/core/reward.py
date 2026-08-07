"""The verifiable reward for the grid-world task -- this mission's analogue
of `grpo.py`'s `compute_reward` for arithmetic. Same two-part, additive
shape (format nudges toward the right kind of output, correctness is what
actually matters), same reason: a 0/1-only reward on the raw success
condition gives no gradient signal on the way to a well-formed completion,
and the failure mode of each half is worth keeping separate in the record
rather than folded into one number.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-gridworld-baselines" / "core"))
from gridworld import ACTIONS, Grid

_ACTION_SET = set(ACTIONS)


def format_reward(text: str) -> float:
    """The completion shares one vocabulary with the prompt (board symbols,
    template words, digits), so nothing stops the policy from emitting any
    of those characters instead of a move -- this is the check that it
    didn't.

    1.0 -- non-empty and every character is a legal action (U/D/L/R).
    0.5 -- non-empty and at least half the characters are legal actions.
    0.2 -- non-empty and at least one character is a legal action.
    0.0 -- empty, or no character is a legal action at all.
    """
    if not text:
        return 0.0
    legal = sum(1 for ch in text if ch in _ACTION_SET)
    if legal == len(text):
        return 1.0
    if legal >= len(text) / 2:
        return 0.5
    if legal > 0:
        return 0.2
    return 0.0


def extract_actions(text: str) -> str:
    """Only the characters that are legal moves, in order, dropping
    anything else -- the environment's `run_episode` only knows how to
    execute U/D/L/R, so a completion that wanders into other vocabulary
    (board symbols, template words) has those characters silently skipped
    rather than crashing the rollout."""
    return "".join(ch for ch in text if ch in _ACTION_SET)


def success_reward(text: str, grid: Grid, max_steps: int) -> float:
    actions = extract_actions(text)
    reached, _steps = grid.run_episode(actions, max_steps)
    return 1.0 if reached else 0.0


def compute_reward(
    text: str, grid: Grid, max_steps: int, format_weight: float = 0.2, success_weight: float = 1.0
) -> tuple[float, dict[str, float]]:
    f = format_reward(text)
    s = success_reward(text, grid, max_steps)
    total = format_weight * f + success_weight * s
    return total, {"format": f, "success": s, "total": total}
