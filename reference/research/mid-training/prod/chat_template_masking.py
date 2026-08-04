"""The same job as core/mid_training_data.py, through the tools it stands in for.

`core/mid_training_data.py` tags every turn by hand (`<role:kind>`) and splits
text on whitespace to decide what gets a loss. Two things there are toy
stand-ins for a real pipeline:

1. **The tokenizer.** A real pipeline uses subword merges, not whitespace
   splits, so a token boundary rarely lines up with a word boundary. This
   script trains an actual byte-level BPE tokenizer (via HuggingFace
   `tokenizers`, the library `transformers` itself is built on) on the same
   toy trajectories, and works out the mask at the token level the merges
   actually produce.
2. **The template.** A real pipeline renders messages through a Jinja chat
   template — the same templating engine `transformers.apply_chat_template`
   uses internally — rather than hand-formatting `f"<{role}:{kind}>"`
   strings. This script renders one with `jinja2` directly.

The other change is structural, and it is the more interesting one: instead
of tagging every assistant turn with a `kind` ("think" / "act" / "observe" /
"answer") the way core/ does, this script gives the tool's result its own
message role (`"tool"`), the way most production chat templates already do
for function-calling. Masking then falls out of one rule instead of two:
*mask every token whose message role is not `"assistant"`.* User turns and
tool observations both disappear from the loss the same way, for the same
reason — see README section 5.

This script never calls a live tool and never downloads a pretrained
tokenizer; the "real tool" here is the tokenizer and templating libraries, not
a hosted model, so the mechanism is checkable without network access to
anything but PyPI. `transformers.apply_chat_template(...,
return_assistant_tokens_mask=True)` computes the same assistant/non-assistant
split from character offsets internally when a template marks its generation
spans; this script computes that split by hand, from the same primitives, so
the mechanism stays visible.

Requires: `tokenizers`, `jinja2` (not in this repo's base dependency group —
install separately, e.g. `uv run --with tokenizers,jinja2 python
chat_template_masking.py`).

Run:  uv run --with tokenizers,jinja2 python chat_template_masking.py
"""

from __future__ import annotations

import jinja2
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

IGNORE_INDEX = -100

# A real chat template renders a list of {"role", "content"} messages. Giving
# the tool result its own role, rather than folding it into an assistant
# turn's "observe" segment, is the structural difference from core/'s design
# — see the module docstring.
CHAT_TEMPLATE = (
    "{% for message in messages %}<|{{ message.role }}|>\n"
    "{{ message.content }}\n"
    "{% endfor %}"
)

# The same "tallest mountain" example core/mid_training_data.py uses, so the
# two scripts are comparable output for output.
FIRST_ORDER_TRAJECTORY = [
    {"role": "user", "content": "What is Earth's tallest mountain above sea level?"},
    {
        "role": "assistant",
        "content": (
            "I don't know this offhand; I should look up 'tallest_mountain'.\n"
            'lookup("tallest_mountain")'
        ),
    },
    {"role": "tool", "content": "Mount Everest."},
    {"role": "assistant", "content": "The answer is: Mount Everest."},
]

HIGH_ORDER_TRAJECTORY = [
    {"role": "user", "content": "What is Earth's tallest mountain above sea level?"},
    {
        "role": "assistant",
        "content": "I'll try 'gold_symbol' first.\n" 'lookup("gold_symbol")',
    },
    {"role": "tool", "content": "Au."},
    {
        "role": "assistant",
        "content": (
            "That does not answer the question; the right key is "
            "'tallest_mountain'.\n" 'lookup("tallest_mountain")'
        ),
    },
    {"role": "tool", "content": "Mount Everest."},
    {"role": "assistant", "content": "The answer is: Mount Everest."},
]


def train_toy_tokenizer(corpus: list[str]) -> Tokenizer:
    """A real byte-level BPE tokenizer, trained on the trajectories at hand.

    This is the toy-scale stand-in for a production tokenizer: same
    algorithm (byte-level BPE, the GPT-2/RoBERTa family's choice, also used
    by `tokenizers`-backed HuggingFace tokenizers), fit to a corpus of five
    sentences instead of a web-scale one.
    """
    tokenizer = Tokenizer(models.BPE())
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=400, min_frequency=1)
    tokenizer.train_from_iterator(corpus, trainer)
    return tokenizer


def message_spans(messages: list[dict[str, str]]) -> tuple[str, list[tuple[int, int, str]]]:
    """Render the chat template once, and recover each message's character span.

    `transformers.apply_chat_template`'s assistant-mask feature marks
    generation spans inside the template itself. This does the equivalent by
    rendering every message-count prefix and taking the length delta — valid
    because `CHAT_TEMPLATE` only ever appends per message, never rewrites
    earlier text. A template that could rewrite already-rendered text (rare,
    but not forbidden by Jinja) would need the real span-tracking machinery
    instead of this shortcut.
    """
    env = jinja2.Environment()
    template = env.from_string(CHAT_TEMPLATE)
    spans: list[tuple[int, int, str]] = []
    previous_length = 0
    for i in range(1, len(messages) + 1):
        rendered_prefix = template.render(messages=messages[:i])
        spans.append((previous_length, len(rendered_prefix), messages[i - 1]["role"]))
        previous_length = len(rendered_prefix)
    full_text = template.render(messages=messages)
    return full_text, spans


def render_and_mask(
    messages: list[dict[str, str]], tokenizer: Tokenizer
) -> tuple[list[int], list[int]]:
    """Tokenize a rendered chat template and mask every non-assistant token.

    `tokenizer.encode(...).offsets` gives each token's character span in the
    original string — the real-tokenizer equivalent of core/'s per-word
    labels. A token is trainable if its span starts inside a message whose
    role is `"assistant"`.
    """
    full_text, spans = message_spans(messages)
    encoding = tokenizer.encode(full_text)

    def role_at(offset: int) -> str:
        for start, end, role in spans:
            if start <= offset < end:
                return role
        return spans[-1][2]  # a trailing newline past the last span

    labels = [
        token_id if role_at(start) == "assistant" else IGNORE_INDEX
        for token_id, (start, _end) in zip(encoding.ids, encoding.offsets)
    ]
    return encoding.ids, labels


def describe(name: str, messages: list[dict[str, str]], tokenizer: Tokenizer) -> None:
    print(f"--- {name} ---")
    for message in messages:
        tag = "loss  " if message["role"] == "assistant" else "masked"
        preview = message["content"].replace("\n", " / ")
        print(f"[{tag}] {message['role']:<9s} {preview}")

    ids, labels = render_and_mask(messages, tokenizer)
    masked = sum(1 for label in labels if label == IGNORE_INDEX)
    total = len(ids)
    print(
        f"tokens={total} masked={masked} ({masked / total:.0%}) "
        f"trainable={total - masked}\n"
    )


def main() -> None:
    corpus = [
        message["content"]
        for trajectory in (FIRST_ORDER_TRAJECTORY, HIGH_ORDER_TRAJECTORY)
        for message in trajectory
    ]
    tokenizer = train_toy_tokenizer(corpus)

    describe("first-order action synthesis", FIRST_ORDER_TRAJECTORY, tokenizer)
    describe(
        "high-order action synthesis (with a wrong first attempt)",
        HIGH_ORDER_TRAJECTORY,
        tokenizer,
    )


if __name__ == "__main__":
    main()
