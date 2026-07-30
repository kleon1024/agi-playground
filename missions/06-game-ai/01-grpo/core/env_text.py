"""Render a grid as the text prompt the policy reads, and build the small,
closed vocabulary that text is drawn from -- the grid-world analogue of
mission 01 04-rl's own character-level arithmetic vocabulary
(`grpo.py`'s `_CHARS`).

The vocabulary is built the same way `grpo.py` builds its own: specials
first (`<pad>`, `<eos>`), then the rest sorted. That ordering is not
cosmetic -- it is what makes `PAD_ID == 0` and `EOS_ID == 1` in this vocab
too, which is the reason `rollout_group`/`token_logprobs`/`grpo_loss`
(imported unmodified from `grpo.py` in `train_grpo.py`) need no patching at
all: those functions reference `grpo.PAD_ID`/`grpo.EOS_ID` as module
globals, and this vocab happens to place the same two ids at the same two
positions rather than requiring anyone to override them.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-gridworld-baselines" / "core"))
from gridworld import ACTIONS, Grid, sample_grid

_SPECIALS = ["<pad>", "<eos>"]


def render_prompt(grid: Grid, max_steps: int) -> str:
    return f"BOARD:\n{grid.render_text()}\nPLAN ({max_steps} MOVES MAX):"


def _alphabet() -> list[str]:
    """Every character that can appear in a prompt or a well-formed
    completion. Scanned from real rendered prompts across a range of grid
    sizes and step budgets (the same "build from real strings, not a
    hand-typed guess" approach mission 05 stage 01's tokenizer uses) rather
    than transcribed by hand, after a hand-typed first attempt silently
    dropped the space character in "PLAN (12 MOVES MAX):"."""
    chars: set[str] = set(ACTIONS)
    rng = random.Random(0)
    for size in (3, 5, 8):
        for num_walls in (0, 2, 4):
            for max_steps in (1, 12, 30):
                grid = sample_grid(rng, size=size, num_walls=num_walls)
                chars.update(render_prompt(grid, max_steps))
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
