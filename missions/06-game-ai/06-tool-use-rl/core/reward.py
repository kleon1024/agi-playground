"""The verifiable reward for the tool-use decision task -- this stage's
analogue of `../../01-grpo/core/reward.py`'s grid-world reward. Same
additive, two-part shape (format nudges toward the right kind of output,
outcome is what actually matters), but the outcome half is new: it is not a
check against the problem's real arithmetic target at all.

Why not: this stage holds GRPO, the environment's *action space size*, and
the additive-reward shape fixed, and changes exactly one thing relative to
stage 01 -- the decision the policy is scored on. If `outcome_reward` graded
whether the policy's own arithmetic was right, this stage would be training
(and confounding) two mechanisms at once: arithmetic competence and the
tool-invocation decision. Instead, `simulated_accuracy` stands in for "how
good this policy's mental arithmetic already is" as a deterministic function
of difficulty alone -- a synthetic proxy for a policy's own imperfect
arithmetic, not a measurement of any real LLM's actual arithmetic error rate.
The policy never sees this function; it only sees the difficulty label in
the prompt and must learn which side of the tool-cost threshold each level
falls on.
"""

from __future__ import annotations

import random

# Fixed, stated penalty for invoking the tool -- representing the latency or
# API cost a real system would pay. Paid in full every time the tool is
# used, regardless of difficulty: the tool's cost is a property of the tool,
# not of the problem.
TOOL_COST = 0.30


def simulated_accuracy(digit_count: int) -> float:
    """Deterministic-per-difficulty-level accuracy for a policy that answers
    directly, without the tool: linear in digit count, floored at 0.05 so
    even the hardest level leaves a real (if small) chance of being right by
    luck, and capped implicitly at 0.97 (digit_count=1) so the easiest level
    is not a guaranteed win either -- an infallible easy case would let a
    policy learn "answer on easy" from a reward signal with zero variance,
    the same degenerate-group failure mode `grpo.py` already guards against.

    digit_count : accuracy
        1  : 0.97
        2  : 0.82
        3  : 0.67
        4  : 0.52
        5  : 0.37

    At TOOL_COST=0.30 (tool reward = 0.70 flat), this crosses the tool's flat
    reward between level 2 (0.82, answer wins) and level 3 (0.67, tool
    wins) -- the exact threshold a calibrated policy must learn to place.
    """
    return max(0.05, 0.97 - 0.15 * (digit_count - 1))



# The decision alphabet is one character each -- `A` (answer directly) and
# `T` (invoke the tool) -- not the spelled-out words `ANSWER`/`TOOL`. An
# early version of this file used the full words and every one of 200 GRPO
# steps came back degenerate on the first real run: a randomly initialized
# character-level model sampling from a ~40-symbol vocabulary has almost no
# chance of ever emitting a specific 4-6 character sequence in the right
# order (`P(hit) ~ (1/40)^4`), so `format_reward` scored 0.0 on every one of
# 8 rollouts in every group, `std(rewards) == 0`, and GRPO never took a
# gradient step -- a real finding, but the wrong one: it would have
# re-measured mission 01's own "a cold start almost never spells a specific
# multi-character tag" result under a new name, not exercised the actual
# question this stage asks (does the policy learn to condition a decision on
# difficulty). The grid-world's own `ACTIONS = "UDLR"` sidesteps exactly this
# by making every legal move a single character, so *any* of several
# characters earns credit, not one exact spelling -- this file copies that
# design rather than the arithmetic lesson's tagged-word one.
_DECISION_CHARS = {"A": "ANSWER", "T": "TOOL"}


def format_reward(text: str) -> float:
    """Mirrors the grid-world's tiered, single-character format reward
    (`../../01-grpo/core/reward.py`), applied to a 2-character legal
    alphabet instead of 4.

    1.0 -- stripped text is exactly one character, `A` or `T`.
    0.5 -- at least one legal character (`A` or `T`) appears somewhere in a
           longer, otherwise-noisy completion.
    0.0 -- neither `A` nor `T` appears anywhere.
    """
    stripped = text.strip()
    if stripped in _DECISION_CHARS:
        return 1.0
    if any(ch in _DECISION_CHARS for ch in text):
        return 0.5
    return 0.0


def extract_decision(text: str) -> str | None:
    """The first legal decision character in generation order resolves the
    decision -- `ANSWER` for `A`, `TOOL` for `T` -- the same "take the first
    legal token and ignore the rest" leniency the grid-world's
    `extract_actions` applies to a whole action string, here applied to
    picking one decision out of a possibly noisy single completion. `None`
    only when the completion contains neither character at all."""
    for ch in text:
        if ch in _DECISION_CHARS:
            return _DECISION_CHARS[ch]
    return None


def outcome_reward(
    decision: str | None, digit_count: int, rng: random.Random
) -> tuple[float, bool | None]:
    """Returns (reward, correct). `correct` is `None` for a malformed
    decision, since there is nothing to grade.

    TOOL always returns the exact right answer -- reward is `1.0 -
    TOOL_COST`, deterministic, no draw from `rng` at all. ANSWER draws a
    *fresh* Bernoulli(`simulated_accuracy(digit_count)`) outcome from `rng`
    every single time it is chosen -- not a fixed property of the problem
    instance repeated identically across a rollout group. That is what gives
    a group of several ANSWER-choosing rollouts on the same problem real
    reward variance to learn from, instead of every one of them scoring
    identically and the group coming back degenerate by construction.
    """
    if decision is None:
        return 0.0, None
    if decision == "TOOL":
        return 1.0 - TOOL_COST, True
    correct = rng.random() < simulated_accuracy(digit_count)
    return (1.0 if correct else 0.0), correct


def compute_reward(
    text: str, digit_count: int, rng: random.Random, format_weight: float = 0.2
) -> tuple[float, dict]:
    f = format_reward(text)
    decision = extract_decision(text)
    o, correct = outcome_reward(decision, digit_count, rng)
    total = format_weight * f + o
    return total, {"format": f, "outcome": o, "decision": decision, "correct": correct, "total": total}
