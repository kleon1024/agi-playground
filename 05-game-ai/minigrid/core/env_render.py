"""Render a MiniGrid partial observation as compact text, and build the
small closed vocabulary that text is drawn from -- MiniGrid's analogue of
`../../01-grpo/core/env_text.py` for the fully-observed grid-world.

Unlike the fully-observed grid-world (whole board in one prompt, one text
completion plans the whole episode open-loop), MiniGrid only ever reveals a
7x7 patch in front of the agent. A single open-loop completion cannot work
here -- the agent must act on what it currently sees, then re-observe after
each move. So the "prompt" is not fixed once per episode: it is rebuilt
after every step from the environment's own new observation, and appended
to a single growing token sequence the same policy reads and extends one
action token at a time (see `train_minigrid.py`).
"""

from __future__ import annotations

from minigrid.core.constants import IDX_TO_OBJECT

_OBJ_CHAR = {
    "unseen": "?",
    "empty": ".",
    "wall": "#",
    "floor": ".",
    "goal": "G",
    "lava": "L",
}

ACTIONS = "FLR"  # forward, turn-left, turn-right -- pickup/drop/toggle/done unused by Empty
_SPECIALS = ["<pad>", "<eos>"]


def render_step(obs: dict, step: int) -> str:
    """One step's observation as text: the 7x7 object-id grid (row-major,
    agent-relative -- MiniGrid's own convention), the agent's facing
    direction, and the step count, ending in the cue the policy completes
    with one action character."""
    grid = obs["image"][:, :, 0]
    rows = []
    for row in grid:
        rows.append("".join(_OBJ_CHAR.get(IDX_TO_OBJECT.get(int(v), ""), "X") for v in row))
    board = "\n".join(rows)
    return f"OBS:\n{board}\nDIR:{obs['direction']}\nSTEP:{step}\nACTION:"


def _alphabet() -> list[str]:
    """Every character that can appear across a real rendered episode,
    scanned rather than hand-typed (env_text.py's own stated reason: a
    hand-typed guess previously dropped a real character)."""
    chars: set[str] = set(ACTIONS)
    for obj_char in _OBJ_CHAR.values():
        chars.add(obj_char)
    chars.add("X")
    chars.update("OBS:\nDIR:STEP:ACTION:")
    chars.update("0123456789")
    return sorted(chars)


VOCAB = _SPECIALS + _alphabet()
stoi = {ch: i for i, ch in enumerate(VOCAB)}
itos = {i: ch for ch, i in stoi.items()}
PAD_ID = stoi["<pad>"]
EOS_ID = stoi["<eos>"]
assert PAD_ID == 0 and EOS_ID == 1


def encode(text: str) -> list[int]:
    return [stoi[ch] for ch in text]


def decode_char(i: int) -> str:
    return itos[i]
