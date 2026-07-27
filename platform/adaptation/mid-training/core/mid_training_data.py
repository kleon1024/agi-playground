"""Synthesizing agentic trajectories, and masking the loss on what comes back.

Mid-training's data does not exist as recorded transcripts — nobody has
hundreds of billions of tokens of human-supervised tool use lying around. It
is synthesized, and the README (section 4) names two published routes:

**First-order Action Synthesis (FAS)** builds a think -> act -> observe ->
answer trajectory straight from a knowledge source. The "observe" step is
generated to stay consistent with that source; no tool ever actually runs.
`first_order_action_synthesis` below is exactly this: one lookup, one clean
trajectory.

**High-order Action Synthesis (HAS)** starts from a trajectory like that one
and expands it into a decision process: a plausible but wrong first attempt,
an observation that shows the mismatch, and a corrected step — not a second
clean imitation of the right answer. `high_order_action_synthesis` below
builds exactly that shape: wrong guess, wrong observation, an explicit
correction in the next think step, then the same lookup FAS would have made
first.

Either route produces a transcript with three kinds of assistant-side text:
what the model decided (think), what it did (act), and what came back
(observe). Training loss on all three teaches the model to generate
convincing tool output, which is the failure section 5 describes. The fix —
also section 5 — is to mask the loss on observation tokens: the model still
reads them, so it still learns to condition its next think/act step on real
tool results, but no gradient asks it to have produced that text itself.
`render_and_mask` below builds exactly that (ids, labels) pair, with `-100`
(the ignored index for `torch.nn.functional.cross_entropy` and
`torch.nn.CrossEntropyLoss`) over every observation span and every user turn.

Everything here — the five-fact knowledge base, the whitespace tokenizer, the
from-scratch vocabulary — is a stand-in sized for reading in one sitting. The
mechanism does not change when the knowledge source is a real corpus, the
tool is a real API, and the tokenizer is the one in prod/. Only the token
count does, by roughly nine orders of magnitude (five facts here; ~300B
tokens in the Agentic CPT report the README cites).

Run:  python mid_training_data.py
"""

from __future__ import annotations

from dataclasses import dataclass

IGNORE_INDEX = -100  # cross_entropy's default ignore_index

# A five-fact knowledge base: (question, fact). Small enough to read in full,
# which is the point — the synthesis logic below does not care how many
# entries this dict has.
KB: dict[str, tuple[str, str]] = {
    "boiling_point_water": (
        "What temperature does water boil at, at sea level?",
        "100 degrees Celsius.",
    ),
    "speed_of_light": (
        "How fast does light travel in a vacuum?",
        "about 299,792 kilometers per second.",
    ),
    "author_of_hamlet": ("Who wrote Hamlet?", "William Shakespeare."),
    "tallest_mountain": (
        "What is Earth's tallest mountain above sea level?",
        "Mount Everest.",
    ),
    "gold_symbol": ("What is the chemical symbol for gold?", "Au."),
}


@dataclass
class Turn:
    """One step of a trajectory.

    `role` distinguishes the user's question from everything the assistant
    produces or receives. `kind` distinguishes think/act/observe/answer
    *within* the assistant's side, which is what render_and_mask needs to
    decide, turn by turn, whether the text was authored by the model.
    """

    role: str  # "user" | "assistant"
    kind: str  # "question" | "think" | "act" | "observe" | "answer"
    text: str


def lookup(key: str) -> str | None:
    """The knowledge source FAS reads from. Never a live tool call."""
    entry = KB.get(key)
    return entry[1] if entry else None


def first_order_action_synthesis(key: str) -> list[Turn]:
    """One clean think -> act -> observe -> answer trajectory, built from KB.

    This is FAS: the observation is generated from the knowledge source
    directly, in the same synthesis pass as the think and act steps that
    precede it, rather than returned by a tool that actually executed.
    """
    question, fact = KB[key]
    return [
        Turn("user", "question", question),
        Turn("assistant", "think", f"I don't know this offhand; I should look up '{key}'."),
        Turn("assistant", "act", f'lookup("{key}")'),
        Turn("assistant", "observe", fact),
        Turn("assistant", "answer", f"The answer is: {fact}"),
    ]


def high_order_action_synthesis(key: str, wrong_key: str) -> list[Turn]:
    """Expand a first-order trajectory into a decision process with feedback.

    HAS does not imitate the right answer once; it starts from a plausible
    wrong attempt (`wrong_key`), shows the observation that reveals the
    mismatch, and only then makes the corrected lookup `first_order_action_
    synthesis` would have made on its own. The explicit feedback step (the
    second `think`) is what a plain-imitation trajectory never contains.
    """
    question, fact = KB[key]
    wrong_fact = lookup(wrong_key) or "no result"
    return [
        Turn("user", "question", question),
        Turn("assistant", "think", f"I'll try '{wrong_key}' first."),
        Turn("assistant", "act", f'lookup("{wrong_key}")'),
        Turn("assistant", "observe", wrong_fact),
        Turn(
            "assistant",
            "think",
            f"That does not answer the question; the right key is '{key}'.",
        ),
        Turn("assistant", "act", f'lookup("{key}")'),
        Turn("assistant", "observe", fact),
        Turn("assistant", "answer", f"The answer is: {fact}"),
    ]


def is_trainable(turn: Turn) -> bool:
    """Assistant-authored spans get loss; the user's turn and every
    observation do not — see the module docstring and README section 5."""
    return turn.role == "assistant" and turn.kind != "observe"


def render_and_mask(trajectory: list[Turn]) -> tuple[list[int], list[int]]:
    """Whitespace-tokenize a trajectory into (ids, labels).

    A real tokenizer uses subword merges instead of whitespace splits (see
    prod/chat_template_masking.py) — the mechanism this function exists to
    show, which spans get a loss and which do not, does not depend on that
    choice. Each turn also emits a `<role:kind>` marker token, itself always
    masked, the same way a chat template's role header is never a loss target
    in post-training's SFT (see `../post-training/core`).
    """
    tokens: list[str] = []
    trainable: list[bool] = []
    for turn in trajectory:
        tokens.append(f"<{turn.role}:{turn.kind}>")
        trainable.append(False)
        for word in turn.text.split():
            tokens.append(word)
            trainable.append(is_trainable(turn))

    vocab: dict[str, int] = {}
    for token in tokens:
        vocab.setdefault(token, len(vocab))

    ids = [vocab[token] for token in tokens]
    labels = [ids[i] if trainable[i] else IGNORE_INDEX for i in range(len(ids))]
    return ids, labels


def describe(name: str, trajectory: list[Turn]) -> None:
    """Print a trajectory and the mask it produces, so the mechanism in
    sections 4 and 5 is something you read rather than take on faith."""
    print(f"--- {name} ---")
    for turn in trajectory:
        tag = "loss  " if is_trainable(turn) else "masked"
        print(f"[{tag}] {turn.role}:{turn.kind:<8s} {turn.text}")

    ids, labels = render_and_mask(trajectory)
    masked = sum(1 for label in labels if label == IGNORE_INDEX)
    total = len(ids)
    print(
        f"tokens={total} masked={masked} ({masked / total:.0%}) "
        f"trainable={total - masked}\n"
    )


def main() -> None:
    fas = first_order_action_synthesis("tallest_mountain")
    describe("first-order action synthesis", fas)

    has = high_order_action_synthesis("tallest_mountain", wrong_key="gold_symbol")
    describe("high-order action synthesis (with a wrong first attempt)", has)


if __name__ == "__main__":
    main()
