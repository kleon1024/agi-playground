"""Prompt rendering and vocabulary for the tool-use decision task -- the same
role `../../01-grpo/core/env_text.py` plays for the grid-world: build the
small, closed character vocabulary the policy reads and writes, ordered
specials-first so `PAD_ID == 0` and `EOS_ID == 1` here too. That is what lets
`grpo.py`'s `rollout_group`/`token_logprobs`/`grpo_loss` (imported unmodified
in `train_grpo.py`) run against yet another vocabulary with no patching --
those functions reference `grpo.PAD_ID`/`grpo.EOS_ID` as module globals, not
per-vocab constants.

The task itself: a small arithmetic problem at one of 5 difficulty levels
(1-5 digit operands), where the policy must decide -- not compute -- whether
to answer directly or invoke a calculator tool. `reward.py` is where that
decision gets scored; this file only renders the problem and the difficulty
label the policy conditions its decision on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

_SPECIALS = ["<pad>", "<eos>"]

# 5 difficulty levels, one per operand digit count. Uniform over these 5 in
# `sample_problem` -- no level is rarer than another, so a policy that only
# ever sees, say, 1/5th of its training signal from the hardest level is a
# fact about the reward gap at that level, not about how often it is asked.
DIGIT_LEVELS = (1, 2, 3, 4, 5)

# Addition and multiplication only, per this stage's own scope (mission.yaml
# does not ask for subtraction here) -- and, load-bearing, the operator and
# the actual arithmetic target are never read by the reward function at all.
# See reward.py's module docstring for why: this stage trains the *decision*
# to invoke a tool, not arithmetic itself, so grading the policy's own
# arithmetic would test a different mechanism than the one under study.
_OPS = {"+": lambda a, b: a + b, "*": lambda a, b: a * b}


@dataclass(frozen=True)
class Problem:
    prompt: str
    digit_count: int
    target: int  # the real answer -- computed for display/logging only


def _sample_operand(rng: random.Random, digit_count: int) -> int:
    lo = 1 if digit_count == 1 else 10 ** (digit_count - 1)
    hi = 10**digit_count - 1
    return rng.randint(lo, hi)


def render_prompt(a: int, op: str, b: int, digit_count: int) -> str:
    return f"PROBLEM: {a} {op} {b} = ? (DIFFICULTY: {digit_count} DIGITS) DECIDE:"


def sample_problem(rng: random.Random, digit_levels: tuple[int, ...] = DIGIT_LEVELS) -> Problem:
    digit_count = rng.choice(digit_levels)
    a = _sample_operand(rng, digit_count)
    b = _sample_operand(rng, digit_count)
    op = rng.choice(list(_OPS))
    target = _OPS[op](a, b)
    return Problem(prompt=render_prompt(a, op, b, digit_count), digit_count=digit_count, target=target)


def _alphabet() -> list[str]:
    """Every character that can appear in a rendered prompt, scanned from real
    sampled problems across all 5 digit levels (the same "build from real
    strings, not a hand-typed guess" approach `01-grpo/core/env_text.py`
    uses) -- plus `A` and `T`, the two-character decision alphabet
    (`reward.py`'s `_DECISION_CHARS`) the policy must *write*, which never
    appears in a prompt and would otherwise be silently missing from the
    vocabulary.
    """
    chars: set[str] = {"A", "T"}
    rng = random.Random(0)
    for _ in range(500):
        chars.update(sample_problem(rng).prompt)
    return sorted(chars)


VOCAB = _SPECIALS + _alphabet()
stoi = {ch: i for i, ch in enumerate(VOCAB)}
itos = {i: ch for ch, i in stoi.items()}
PAD_ID = stoi["<pad>"]
EOS_ID = stoi["<eos>"]
assert PAD_ID == 0 and EOS_ID == 1, "grpo.py hardcodes PAD_ID=0, EOS_ID=1 -- this vocab must match"


def encode(text: str) -> list[int]:
    return [stoi[ch] for ch in text]


def decode(ids: list[int]) -> str:
    out = []
    for i in ids:
        if i == EOS_ID:
            break
        if i == PAD_ID:
            continue
        out.append(itos[i])
    return "".join(out)
