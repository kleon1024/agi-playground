---
status: draft
base: none
---

# What turns a model into something that acts?

**Goal:** build a minimal agent harness from scratch — the loop, tool
schemas, sandboxed execution, context management, and a permission model —
that wraps the model served in [`05-serve`](../05-serve/), and come out able
to read a production harness (Claude Code, OpenHands, SWE-agent) as a set of
elaborations on the same five decisions, not a black box.

A harness is the software around the model that turns a next-token predictor
into something that acts. *Stop Comparing LLM Agents Without Disclosing the
Harness* (2026) makes the stakes concrete: two teams reporting different
scores for "the same model" on "the same benchmark" are, in the field's own
recent literature, often just running different harnesses. Loop shape, tool
set, context-management policy, and retry logic account for more benchmark
variance than most papers disclose — which makes harness design the
independent variable, not an implementation detail hidden behind a score.
This stage builds that independent variable once, by hand, and is deliberately
sized at mini-swe-agent scale: three tools, one loop, one context policy, one
permission ladder — not because a bigger tool set would be better, but
because it wouldn't be (see "Why more tools" below).

## What you build

`core/tools.py` — three tools, each declared the way a tool-calling API
expects: name, description, a JSON-Schema-shaped parameter spec, and a risk
tier.

- **`read_file`** and **`list_dir`** — read-only, auto-allowed, confined to a
  sandbox root.
- **`run_command`** — the one tool that can do real damage, so it is the one
  with real sandboxing: an allowlist checked on the parsed first token, no
  `shell=True`, a hard timeout, output truncation, and a working-directory
  jail. All four are executable code in `run_command`'s body, not a comment
  asserting that sandboxing happens somewhere.

`core/harness.py` — the loop: `observe → decide → act → observe`, plus the
four things that make it a harness rather than a `while True` around an API
call — the grounding rule, context management, a permission model, and a
model-agnostic backend.

## The loop, and its stop condition

The loop is ReAct (Yao et al., 2022): the model reasons (`Thought:`), takes
an action (`Action:` / `Action Input:`), receives a real observation, and
reasons again with that observation in hand. This is what corrects the
failure mode of either pure alternative — reasoning alone can't check its
claims against the world, and action alone can't adapt when a tool call fails
or returns something unexpected, because nothing in the trace prompts the
model to reconsider.

`run_agent` in `harness.py` has exactly two ways out, both explicit:

- **`Final Answer:`** — the model signals it's done. This is the intended
  exit.
- **`max_steps`** — the loop stops even if the model never says it's done. A
  loop with only the first stop condition hangs indefinitely the moment a
  model gets stuck retrying a failed action or never converges on
  "done" — which is a normal failure mode, not a rare one.

## The grounding rule: the single most important mechanic in this file

A ReAct-style model is prompted to stop right after `Action Input: ...` and
wait for the harness to inject the real `Observation:`. Nothing about
sampling stops it from continuing to write its own `Observation:` line and
inventing a plausible-looking result — confidently, and indistinguishably
from a real one, until the next action it takes is grounded in a fact that
never happened. This is the harness's entire grounding guarantee, and it
breaks silently if this one detail is wrong.

`enforce_grounding` in `harness.py` closes it with two layers:

1. **Ask the backend to stop generating at the boundary.** `stop=
   ["Observation:"]` is passed into every `Backend.generate` call. A real
   chat-completions API honors a stop sequence, so this is the cheap fix —
   it saves the tokens the model would have spent hallucinating in the first
   place.
2. **Never trust that it did.** Truncate anything at or after the stop token
   out of whatever comes back, unconditionally, before parsing an action out
   of it. This is the layer that actually matters: a backend that ignores
   `stop` — an old API version, a bug, a model that just keeps
   generating — must not be able to slip a fabricated observation past the
   harness. `python core/harness.py --demo grounding` runs a `FakeBackend`
   with `honor_stop=False` that fabricates its own `Observation:` and
   `Final Answer:` in one shot; watch the transcript to see the fabricated
   answer get discarded and the real `list_dir` result take its place.

A smarter model does not fix this on its own — it's a harness discipline, not
a model capability, and it has to be enforced in the harness regardless of
how good the model gets.

Step through the boundary once before reading the tool implementation. The
component distinguishes model-generated proposal from harness-generated
observation; collapsing those two states destroys grounding.

<!-- interactive: AgentLoopSimulator -->

## Tool schemas: descriptions are load-bearing

Each tool in `build_tools` declares a `description` the model actually reads
to decide *when* and *how* to call it — not documentation for a human, a
functional part of the interface. `run_command`'s description names its
allowlist explicitly, which is what tells a model to reach for `grep`
through `run_command` rather than inventing a nonexistent fourth tool.

Schema adherence is a probabilistic property of the model, not a guarantee,
so `harness.py` needs a defined recovery path for a malformed call rather
than crashing on the first bad parse:

- Invalid JSON in `Action Input:` → `parse_response` returns `kind="unparsed"`
  with the JSON error, fed back as the next observation.
- An unknown tool name → an observation naming the tools that do exist.
- A schema mismatch (missing required argument, wrong type) →
  `validate_arguments` in `tools.py` — a deliberately small
  object/properties/required/type subset of JSON Schema, enough to catch
  what a model actually gets wrong without a full JSON Schema
  implementation — raises `ToolError`, which `run_agent` catches and turns
  into an observation the model can act on.

In every case the loop continues rather than crashing. This is deliberately
a from-scratch textual protocol (`Action: <name>` / `Action Input: <json>`)
rather than a native function-calling API response — it works against any
model, tool-calling fine-tuned or not, at the cost of the parsing step a
native tool-call field would remove. See [`prod/README.md`](prod/README.md)
for how production harnesses trade this off.

## Sandboxing `run_command`: real controls, not a comment

`resolve_in_jail` in `tools.py` is worth reading closely for a specific
`pathlib` trap: `Path("/root") / "/etc/passwd"` silently discards the left
side and returns `Path("/etc/passwd")`, because joining with an absolute path
*replaces* rather than extends. A jail that just joins paths and checks the
result for `..` would miss this; `resolve_in_jail` rejects absolute inputs
outright before ever joining, then resolves (following symlinks) and checks
ancestry — closing the absolute-path escape, the `..`-walk escape, and the
symlink-escape in one function.

`run_command` adds a fourth control on top of the jail: an **allowlist**
checked against the parsed first token, not a denylist. A denylist ("no
`rm -rf`") is a losing game — there is no bound on the ways to spell "delete
everything." An allowlist inverts the burden: the command only runs if it
names something already decided to be safe. This only works because the
harness never passes `shell=True` — with a shell, `"echo hi; rm -rf /"` is
one command as far as the OS is concerned, and checking `argv[0]` against an
allowlist would only ever see `echo`. Shell metacharacters are rejected
outright as well, so a command like that fails fast with a clear message
instead of silently doing something the allowlist never anticipated. A
timeout bounds a hung process; output truncation keeps a giant file from
flooding the model's context.

One gap is left honest rather than hidden: only `argv[0]` is allowlisted, so
`cat /etc/passwd` still runs `cat` from an allowed name while reading a path
outside the jail — arguments aren't validated against `resolve_in_jail`.
Hardening that is exercise 3.

## Context management: eager vs. just-in-time, and compaction

`ContextManager` tracks a token budget (`estimate_tokens` is a chars/4
stand-in — wiring in stage 01's real tokenizer is exercise 1) and compacts
when the budget is exceeded. The policy is a named, swappable function
(`drop_oldest_tool_results`), not inline logic buried in the loop:

1. **Collapse superseded reads.** If a later message reads a path that an
   earlier observation already read, the earlier one is replaced with a
   one-line stale marker — the newest read of any file is kept, because an
   agent that read a file twice only needs the second read.
2. **Drop the oldest non-system turn**, one at a time, until under budget —
   never the system prompt, and never past a floor of 3 messages (the model
   needs, at minimum, its own last action and the observation it produced).

This is the lightweight, sliding-window-plus-summarization-adjacent style of
compaction most 2026 production harnesses run, not MemGPT's full explicit
paging interface (Packer et al., 2023) where the model itself calls functions
to move information between working and archival memory — a heavier
mechanism this stage doesn't need at a 3-tool scale, but worth knowing
exists. It's also worth naming the eager/JIT split this stage sits on:
`read_file`/`list_dir` are just-in-time by construction — the agent fetches
only the file it decides it needs, exactly when it asks — rather than the
harness stuffing the whole sandbox root into context upfront. That trade
(exact, debuggable, more round-trips) versus an eager embedding index (fewer
round-trips, goes stale) is a real, contested choice among production coding
agents, covered in `capabilities/act-coordinate/README.md`.

## The permission ladder and blast radius

Every `Tool` in `tools.py` carries a `RiskTier`: `AUTO` (read-only, always
allowed), `CONFIRM` (state-changing, needs sign-off), `DENY` (refused
unconditionally). `check_permission` in `harness.py` enforces it, and
`default_confirm` — the harness's default — **denies every `CONFIRM`-tier
call**. That default is deliberate: a non-interactive run (a test, this
file's own demo) must fail closed rather than silently execute something
nobody approved just because nobody was there to say no. Swap in a real
`confirm` function (a CLI y/n prompt, a policy check) to actually run
`run_command`.

This is the practical version of risk-tiered confirmation from the
capability README: auto-approve reversible reads, require confirmation
before anything that changes state, hard-deny what should never run
regardless of confirmation. The tier lives on the tool, not on the specific
call — which is a simplification worth naming: a real harness eventually
wants tier-by-argument distinctions too (`run_command` running `cat` is very
different from `run_command` running `pytest`), which this stage's uniform
per-tool tier doesn't capture. That's exercise 2.

## Why more tools does not make a better agent

Three tools, not thirty. Tool count adds selection complexity and failure
surface — which tool, ambiguous overlaps between them — faster than it adds
capability. A well-scoped 3-tool loop reliably beats a much larger one on
tasks within its scope, which is why mini-swe-agent's small toolset (and
this stage's) is a design choice, not a limitation waiting to be fixed by
adding more. `run_command`'s description leans on this directly: it names
`grep` as reachable *through* the allowlist rather than adding a fourth tool
for search, because one well-designed escape hatch composes better than a
growing enumeration of narrow tools.

## Production notes

[`prod/README.md`](prod/README.md) maps each design decision above — the
loop, the tools, the grounding rule, context management, permissions — to how
mini-swe-agent, OpenHands, and Claude Code's published harness-design
write-ups handle the same decision at production scale. No benchmark numbers
are claimed there or here; this stage has no `runs/` entry yet (see
`missions/01-language-model-agent/mission.yaml`), and none is due until
`06-harness-aware-evaluation`'s discipline is actually applied in `07-eval`.

## Reproducing

Every command below runs with the deterministic `FakeBackend` — no GPU, no
API key, no network:

```bash
# the basic loop: list_dir -> read_file -> Final Answer
python core/harness.py

# watch the grounding rule catch a hallucinated Observation and discard it
python core/harness.py --demo grounding

# a custom task and step budget against the same fake backend
python core/harness.py --task "What tools does this harness expose?" --max-steps 4
```

To point the harness at a real model instead — stage 05's served model, or
any OpenAI-compatible endpoint — set the environment and drop `--demo`:

```bash
AGENT_BASE_URL=http://localhost:8000/v1 AGENT_MODEL=<served-model-id> \
    python core/harness.py --task "List what's in this directory."
```

`AGENT_BASE_URL` unset is what selects the fake backend; this is the one
place the harness reads environment variables (`backend_from_env` in
`harness.py`), so switching backends is configuration, never a code change.

## Exercises

1. **Wire in a real tokenizer.** Replace `estimate_tokens`'s chars/4
   heuristic with stage 01's `bpe.py` encoder as `ContextManager`'s
   `token_counter`. Does the budget behave differently on code-heavy versus
   prose-heavy observations?
2. **Tier-by-argument permissions.** `run_command` is uniformly `CONFIRM`
   today. Extend `check_permission` (or add a policy hook) so a read-only
   command like `cat` or `grep` auto-allows while a repo-mutating one still
   confirms — argue where the line should sit, and what closes the gap if
   your classifier is wrong.
3. **Harden the honest gap.** `run_command` only allowlists `argv[0]`.
   Extend it to validate any argument that looks like a path against
   `resolve_in_jail`, and write a command that currently escapes the jail
   (e.g. reading a file outside `root` via an otherwise-allowlisted binary)
   to confirm your fix actually closes it.
4. **Add a fourth tool, on purpose.** Add a dedicated `grep` tool instead of
   routing search through `run_command`, give it its own risk tier, and
   argue in a comment why it does or doesn't earn its place given "why more
   tools does not make a better agent" above.
5. **Run it against a real model.** Point `AGENT_BASE_URL` at stage 05's
   served model or an API you hold a key for. Does a real model ever try to
   write its own `Observation:` line, and does the grounding rule catch it
   the same way the `--demo grounding` script demonstrates?

## Next

[Stage 07 — eval](../07-eval/): closing the loop with a harness-disclosed
evaluation of the agent built here, alongside the model-level evals from
earlier stages.
