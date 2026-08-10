"""Rendering agentic trajectories into pretraining text.

Agentic data enters a training mix in three shapes, and only one of them is
synthesized by hand (see `mid_training_data.py`). This module renders all
three the way a corpus pipeline would emit them, so the format decisions the
README makes in prose are things you can see token by token:

1. **Natural corpus text** — Jupyter notebook cell transcripts already in the
   web crawl. The `# In[n]:` / `# Out[n]:` markers are the raw document; no
   separators are added because the text is already the corpus.
2. **Synthetic tool-use trajectories** — a user request, an assistant tool
   call against a declared schema, the result, and a final answer. This is
   where the `<|user|>`, `<|tool_call|>`, `<|tool_result|>` separator choice
   lives.
3. **SWE-style agent trajectories** — the same loop over shell and file tools,
   including an error, an inspection, a fix, and a re-run. This is the shape
   with recovery in it.

Three format decisions are demonstrated, matching the README:

- **Separators.** `--separators chat` keeps the special tokens a trajectory
  was recorded with; `--separators neutral` replaces them with plain tags
  that cannot collide with whatever chat template post-training later picks.
  The two renderings are the same content with a different format contract.
- **Truncation.** `--max-result-chars` caps every tool result. Tool outputs
  in production are longer than any fixed budget, so truncation is a
  deterministic slice, not an option.
- **Noise.** `--noise` replaces the *first* tool result with one of the three
  failures a live tool returns (real error, timeout, empty) and leaves the
  rest clean, so the rendered trajectory is the recovery shape: an early
  failure, an inspection, and a corrected step. A corpus of clean-success
  trajectories teaches the loop but never teaches recovery; the noisy
  variants are what an annealed mix adds.

The metrics table uses whitespace tokenization, the same stand-in
`mid_training_data.py` uses: the mechanism (separator conversion, truncation,
noise, recovery) does not depend on the tokenizer.

Run:
    python format_agentic_text.py
    python format_agentic_text.py --category swe --separators neutral
    python format_agentic_text.py --noise timeout --max-result-chars 60
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

NOTEBOOK = """\
# In[3]:
df = pd.read_csv("sales.csv")
df.groupby("region")["revenue"].sum()

# Out[3]:
KeyError: 'revenue'

# In[4]:
df.columns
# Out[4]:
Index(['region', 'rev_usd', 'date'], dtype='object')

# In[5]:
df.groupby("region")["rev_usd"].sum()
# Out[5]:
region
APAC    1284000
EMEA     957000
"""


TOOL_SCHEMA = """\
{"name": "search_flights", "parameters": {"origin": "string", "dest": "string", "date": "string"}}
{"name": "get_weather", "parameters": {"city": "string", "date": "string"}}
"""

TOOL_USE = [
    ("user", "Can you find flights from Singapore to Tokyo on Friday, and check the Tokyo weather that day?"),
    ("tool_call", '{"name": "search_flights", "arguments": {"origin": "SIN", "dest": "NRT", "date": "2026-08-07"}}'),
    (
        "tool_result",
        (
            '{"flights": [{"flight": "SQ638", "dep": "09:30", "arr": "17:15", "price_usd": 412}, '
            '{"flight": "JL712", "dep": "14:20", "arr": "22:05", "price_usd": 388}]}'
        ),
    ),
    ("tool_call", '{"name": "get_weather", "arguments": {"city": "Tokyo", "date": "2026-08-07"}}'),
    ("tool_result", '{"forecast": "rain", "temp_c": [24, 29]}'),
    (
        "assistant",
        (
            "Two flights on Friday: SQ638 departs 09:30 ($412) and JL712 departs 14:20 ($388). "
            "Tokyo has rain on Friday, 24-29 C, so bring an umbrella."
        ),
    ),
]


SWE = [
    ("user", "Fix the failing test in test_parser.py"),
    ("tool_call", '{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}'),
    (
        "tool_result",
        "FAILED test_parser.py::test_empty_input - AttributeError: 'NoneType' object has no attribute 'strip'",
    ),
    ("tool_call", '{"name": "read_file", "arguments": {"path": "parser.py", "lines": "40-55"}}'),
    (
        "tool_result",
        "42  def parse(text):\n43      text = text.strip()\n44      if not text:\n45          return []",
    ),
    (
        "assistant",
        "parse() does not handle a None input. Fix it so an empty result is returned for None.",
    ),
    (
        "tool_call",
        (
            '{"name": "str_replace", "arguments": {"path": "parser.py", '
            '"old": "def parse(text):\\n    text = text.strip()", '
            '"new": "def parse(text):\\n    if text is None:\\n        return []\\n    text = text.strip()"}}'
        ),
    ),
    ("tool_result", "Edit applied."),
    ("tool_call", '{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}'),
    ("tool_result", "1 passed in 0.12s"),
    ("assistant", "Fixed. parse() now returns [] for a None input."),
]


CHAT_SEP = {
    "user": "<|user|>",
    "assistant": "<|assistant|>",
    "tool_call": "<|tool_call|>",
    "tool_result": "<|tool_result|>",
}

NEUTRAL_SEP = {
    "user": "<user>",
    "assistant": "<assistant>",
    "tool_call": "<tool_call>",
    "tool_result": "<tool_result>",
}

NOISE_RESULTS = {
    "none": None,
    "error": "ToolError: rate limit exceeded, retry after 30s",
    "timeout": "ToolError: request timed out after 60s",
    "empty": "",
}


@dataclass
class Rendered:
    """A rendered trajectory plus the numbers that make it comparable."""

    name: str
    text: str
    chars: int
    tokens: int
    has_recovery: bool
    notes: str = field(default="")


def render(turns: list[tuple[str, str]], separators: dict[str, str]) -> str:
    """Join turns into training text with the chosen separator contract."""
    blocks: list[str] = []
    for role, text in turns:
        blocks.append(separators[role])
        blocks.append(text)
    return "\n".join(blocks)


def apply_result_policy(
    turns: list[tuple[str, str]],
    *,
    max_result_chars: int | None,
    noise: str,
) -> list[tuple[str, str]]:
    """Truncate every result and replace the first one with noise, in place.

    Truncation is a fixed budget every tool result pays; noise is one failure
    at the first result, so the trajectory keeps its error -> inspect ->
    correct shape instead of collapsing into all-failures.
    """
    noisy = NOISE_RESULTS[noise]
    out: list[tuple[str, str]] = []
    first_result_seen = False
    for role, text in turns:
        if role != "tool_result":
            out.append((role, text))
            continue
        if noisy is not None and not first_result_seen:
            text = noisy
            first_result_seen = True
        if max_result_chars is not None:
            text = text[:max_result_chars]
        out.append((role, text))
    return out


def count(text: str) -> tuple[int, int]:
    return len(text), len(text.split())


def has_recovery(turns: list[tuple[str, str]]) -> bool:
    """True when an error-looking result is followed by another tool call."""
    for i, (role, text) in enumerate(turns):
        if (
            role == "tool_result"
            and ("Error" in text or "FAILED" in text or not text)
            and any(r == "tool_call" for r, _ in turns[i + 1 :])
        ):
            return True
    return False


def demo_trajectories(separators: dict[str, str]) -> list[Rendered]:
    rendered: list[Rendered] = []
    for name, turns in (("tool-use", TOOL_USE), ("swe", SWE)):
        text = render(turns, separators)
        chars, tokens = count(text)
        rendered.append(
            Rendered(
                name=name,
                text=text,
                chars=chars,
                tokens=tokens,
                has_recovery=has_recovery(turns),
            )
        )
    return rendered


def print_metrics(rows: list[Rendered]) -> None:
    print(f"\n{'name':<12} {'chars':>6} {'tokens':>6} {'recovery':>8}  notes")
    for row in rows:
        print(
            f"{row.name:<12} {row.chars:>6} {row.tokens:>6} "
            f"{row.has_recovery!s:>8}  {row.notes}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--category",
        choices=("notebook", "tool-use", "swe"),
        default="tool-use",
        help="which trajectory family to render (default: tool-use)",
    )
    parser.add_argument(
        "--separators",
        choices=("chat", "neutral"),
        default="chat",
        help="keep special tokens or replace them with neutral tags (default: chat)",
    )
    parser.add_argument(
        "--max-result-chars",
        type=int,
        default=None,
        help="cap every tool result at N characters (default: no truncation)",
    )
    parser.add_argument(
        "--noise",
        choices=tuple(NOISE_RESULTS),
        default="none",
        help="replace clean tool results with a real failure (default: none)",
    )
    args = parser.parse_args()

    sep = CHAT_SEP if args.separators == "chat" else NEUTRAL_SEP

    if args.category == "notebook":
        chars, tokens = count(NOTEBOOK)
        print("--- notebook (raw corpus text, no separators added) ---")
        print(NOTEBOOK)
        print_metrics(
            [
                Rendered(
                    "notebook",
                    NOTEBOOK,
                    chars,
                    tokens,
                    has_recovery=True,
                    notes="error-to-fix arc present as ambient text",
                )
            ]
        )
        return

    turns = TOOL_USE if args.category == "tool-use" else SWE
    name = args.category
    turns = apply_result_policy(turns, max_result_chars=args.max_result_chars, noise=args.noise)
    text = render(turns, sep)
    chars, tokens = count(text)

    print(f"--- {name} ({args.separators} separators, noise={args.noise}, "
          f"max_result_chars={args.max_result_chars}) ---")
    print(text)
    print_metrics(
        [
            Rendered(
                name=name,
                text=text,
                chars=chars,
                tokens=tokens,
                has_recovery=has_recovery(turns),
                notes=(
                    "recovery survives" if has_recovery(turns)
                    else "no recovery step in this rendering"
                ),
            )
        ]
    )


if __name__ == "__main__":
    main()
