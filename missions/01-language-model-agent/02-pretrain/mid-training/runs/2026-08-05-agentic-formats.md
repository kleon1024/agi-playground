# Run — agentic trajectory formats, separator conversion, truncation, noise

**Date:** 2026-08-05
**Hardware:** macOS 15.6.1, MacBookPro18,3 (Apple M1 Pro, arm64). CPU-only; no GPU involved.
**Software:** Python 3.11.14, stdlib only.
**Cost:** \$0 (local lane).

## Purpose

The README's sections 5 and 7 claim three families of agentic data enter a
training mix — natural notebook transcripts, synthetic tool-use trajectories,
and SWE-style trajectories with recovery — and that separators, truncation,
and noise are format decisions a corpus pipeline makes. This run renders all
three families exactly as a pipeline would emit them, and demonstrates each
decision with a flag, so those claims are output a reader can reproduce
rather than prose.

## Command

```bash
cd missions/01-language-model-agent/02-pretrain/mid-training
python3 core/format_agentic_text.py --category tool-use
python3 core/format_agentic_text.py --category swe
python3 core/format_agentic_text.py --category swe --separators neutral
python3 core/format_agentic_text.py --category swe --noise timeout --max-result-chars 60
python3 core/format_agentic_text.py --category tool-use --noise empty
python3 core/format_agentic_text.py --category notebook
python3 core/mid_training_data.py
uv run --with tokenizers,jinja2 python prod/chat_template_masking.py
```

Wall clock: 0.04s per script invocation (the seven commands above total under
0.3s); the prod run adds ~0.5s under `uv run --with`. Every run deterministic
— no randomness, no network, no API (the prod run pulls `tokenizers` and
`jinja2` from PyPI once).

## Rendered output

### 1. Natural corpus text — Jupyter notebook transcript

`--category notebook` prints the cell transcript as it exists in the crawl.
No separators are added, because this is already the corpus; the `# In[n]:` /
`# Out[n]:` markers carry the action/error/inspect/fix arc on their own:

```text
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
```

289 chars, 29 whitespace tokens. Recovery is present as ambient text — the
arc (wrong column name -> inspect columns -> retry with the right name) is
there, but nothing scaffolds it, which is why this family is a weak signal
the model absorbs by volume rather than a deliberate curriculum.

### 2. Synthetic tool-use trajectory — chat separators, clean

`--category tool-use` renders the schema and the think/call/observe/answer
loop against it, keeping the special tokens:

```text
<|user|>
Can you find flights from Singapore to Tokyo on Friday, and check the Tokyo weather that day?
<|tool_call|>
{"name": "search_flights", "arguments": {"origin": "SIN", "dest": "NRT", "date": "2026-08-07"}}
<|tool_result|>
{"flights": [{"flight": "SQ638", "dep": "09:30", "arr": "17:15", "price_usd": 412}, {"flight": "JL712", "dep": "14:20", "arr": "22:05", "price_usd": 388}]}
<|tool_call|>
{"name": "get_weather", "arguments": {"city": "Tokyo", "date": "2026-08-07"}}
<|tool_result|>
{"forecast": "rain", "temp_c": [24, 29]}
<|assistant|>
Two flights on Friday: SQ638 departs 09:30 ($412) and JL712 departs 14:20 ($388). Tokyo has rain on Friday, 24-29 C, so bring an umbrella.
```

686 chars, 85 whitespace tokens, no recovery step. This is the clean-success
shape: nothing goes wrong, so nothing teaches the model what to do when a
tool returns something unexpected.

### 3. SWE trajectory — chat separators, clean

`--category swe` renders the loop that includes an error, an inspection, a
fix, and a re-run:

```text
<|user|>
Fix the failing test in test_parser.py
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
FAILED test_parser.py::test_empty_input - AttributeError: 'NoneType' object has no attribute 'strip'
<|tool_call|>
{"name": "read_file", "arguments": {"path": "parser.py", "lines": "40-55"}}
<|tool_result|>
42  def parse(text):
43      text = text.strip()
44      if not text:
45          return []
<|assistant|>
parse() does not handle a None input. Fix it so an empty result is returned for None.
<|tool_call|>
{"name": "str_replace", "arguments": {"path": "parser.py", "old": "def parse(text):\n    text = text.strip()", "new": "def parse(text):\n    if text is None:\n        return []\n    text = text.strip()"}}
<|tool_result|>
Edit applied.
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
1 passed in 0.12s
<|assistant|>
Fixed. parse() now returns [] for a None input.
```

997 chars, 121 whitespace tokens, recovery present (the FAILED result is
followed by an inspection and a corrected call). This is the family the README
calls the highest-value shape.

### 4. Separator conversion — neutral variant

`--category swe --separators neutral` renders the identical trajectory with
plain `<user>`, `<tool_call>`, `<tool_result>` tags instead of the special
tokens. 975 chars, 121 whitespace tokens — the content is unchanged, only the
format contract differs, which is the point of the conversion: a neutral
shape cannot collide with the chat template post-training later commits to.

### 5. Truncation and noise — the recovery shape survives

`--category swe --noise timeout --max-result-chars 60` turns the first tool
result into a timeout and caps every result at 60 characters:

```text
<|user|>
Fix the failing test in test_parser.py
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
ToolError: request timed out after 60s
<|tool_call|>
{"name": "read_file", "arguments": {"path": "parser.py", "lines": "40-55"}}
<|tool_result|>
42  def parse(text):
43      text = text.strip()
44      if 
<|assistant|>
parse() does not handle a None input. Fix it so an empty result is returned for None.
<|tool_call|>
{"name": "str_replace", "arguments": {"path": "parser.py", "old": "def parse(text):\n    text = text.strip()", "new": "def parse(text):\n    if text is None:\n        return []\n    text = text.strip()"}}
<|tool_result|>
Edit applied.
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
1 passed in 0.12s
<|assistant|>
Fixed. parse() now returns [] for a None input.
```

904 chars, 112 whitespace tokens, recovery still present: the model sees a
failed first call, reads a truncated file, applies the fix anyway, and the
re-run succeeds. Truncation shortened the read_file result mid-sentence and
the agent still had to continue from the fragment — which is the behavior a
real tool pipeline produces and the exact failure mode a clean-only corpus
never exposes.

`--category tool-use --noise empty` shows the same shape on the simpler
trajectory: the empty result forces the loop to continue and the final
answer still lands. 531 chars, 68 whitespace tokens, recovery present.

## Metrics

Whitespace tokenization (the same stand-in `core/mid_training_data.py` uses):

| rendering | chars | tokens | recovery |
|---|---:|---:|---|
| notebook (raw corpus text) | 289 | 29 | yes, as ambient arc |
| tool-use, chat, clean | 686 | 85 | no |
| tool-use, chat, empty result | 531 | 68 | yes |
| swe, chat, clean | 997 | 121 | yes |
| swe, neutral, clean | 975 | 121 | yes |
| swe, chat, timeout + 60-char truncation | 904 | 112 | yes |

`core/mid_training_data.py` (FAS/HAS synthesis and loss masking, unchanged):

```
--- first-order action synthesis ---
tokens=31 masked=15 (48%) trainable=16
--- high-order action synthesis (with a wrong first attempt) ---
tokens=41 masked=19 (46%) trainable=22
```

`prod/chat_template_masking.py` (the same masking through a real BPE
tokenizer and Jinja chat template, with the tool result as its own `tool`
message role):

```
--- first-order action synthesis ---
tokens=72 masked=24 (33%) trainable=48
--- high-order action synthesis (with a wrong first attempt) ---
tokens=106 masked=32 (30%) trainable=74
```

The higher token counts (72 vs 31) are the subword tokenizer and the template
rendering; the masked share falling (48% -> 33%) is the `tool`-role rule
masking fewer tokens than the hand-tagged `<assistant:observe>` spans — same
mechanism, different granularity, which is the prod/core contrast the chapter
draws.

## Notes

- **Noise placement matters.** Replacing the *first* tool result keeps the
  trajectory a recovery story (error -> inspect -> fix -> success); replacing
  every result collapses it into all-failures, which teaches nothing.
- **Truncation is a budget, not a choice.** At 60 chars the read_file result
  ends mid-sentence and the trajectory still resolves, which is exactly what
  a fixed token budget does to real tool output.
- **Separator conversion changes the format contract, not the content.** The
  neutral rendering is 22 chars shorter and identical in tokens; the choice
  is about not betting on a chat template that has not been chosen yet.
- **The prod template was already using the tool-role convention.** The
  `prod/` script gives the observation its own `tool` message role rather
  than an assistant `observe` kind, so masking falls out of one rule —
  non-assistant roles are never loss targets — matching what most production
  function-calling templates do.
- This run renders scripted representative formats and demonstrates the
  mechanics; it does not measure whether any particular mix ratio or noise
  rate improves a trained model — that claim is out of scope for a single
  machine (see the README's evidence boundary).
