---
status: verified
level: applied
base: none
label: Agent harness
verified: 2026-07-30
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

The schema is doing the same job the description is, one level down: a
narrow contract makes an invalid call hard to *express*. `run(command:
string)` accepts everything, so every check has to happen after the model has
already proposed something arbitrary; `search_text(query, path, file_glob,
max_results)` narrows the permission, produces a structured result, and turns
"the model asked for something impossible" into a field-level error message
instead of a shell string somebody has to reason about. SWE-agent (Yang et
al., 2024) named this surface — the agent-computer interface — as its own
design problem rather than a wrapper around a terminal, and it is why the
three tools here declare arguments, side effects, a timeout, and an output
limit rather than exposing a shell and hoping. MCP (Anthropic, Nov 2024)
standardizes how such tools are *exposed* across hosts; it does not decide
whether a call is safe, and its own spec says so. The host stays the policy
boundary — which is [what stops it?](what-stops-it/).

Schema adherence is a probabilistic property of the model, not a guarantee,
so `harness.py` needs a defined recovery path for a malformed call rather
than crashing on the first bad parse:

- Invalid JSON in `Action Input:` → `parse_response` returns `kind="unparsed"`
  with the JSON error, fed back as the next observation.
- An unknown tool name → an observation naming the tools that do exist.
- A schema mismatch (missing required argument, wrong type) →
  `validate_arguments` in `tools.py` — a deliberately small JSON-Schema
  subset, enough to catch what a model actually gets wrong without a full
  implementation — raises `ToolError`, turned into an observation the model
  can act on.

In every case the loop continues rather than crashing. This is a
from-scratch textual protocol (`Action: <name>` / `Action Input: <json>`)
rather than a native function-calling response — it works against any
model at the cost of the parsing step a native tool-call field would
remove. See [`prod/README.md`](prod/README.md) for that tradeoff in
production harnesses.

Retrying is only free before something executed. A parse or validation
failure never reached a tool, so feeding the error back and letting the model
try again costs a turn and nothing else. Once a call has actually run and its
outcome is ambiguous — did the write land, did the request go out — the same
retry can duplicate the effect rather than correct it. That is why the
recovery path above stops at "return the error as an observation" and does
not add a blind retry loop: the boundary between *safe to redo* and *already
done* belongs to an idempotency key or an explicit state inspection, not to a
counter.

## The trace is the record, because the harness is the variable

This stage opened with the claim that harness design accounts for more
benchmark variance than most papers disclose. That has a practical
consequence for what the loop writes down. A transcript is not just a
debugging aid here; it is the evidence that a given score belongs to a given
harness, so it needs stable event types rather than free prose:

```text
model_request
model_response
action_proposed
action_rejected | action_executed
observation
completion | budget_exhausted | human_required
```

Those names are what make a comparison attributable. To learn anything from
two runs you change exactly one thing between them — the model with the
harness fixed, a tool description with the model fixed, the context policy
with both fixed, the permission policy with everything else fixed — and read
completion, policy adherence, tool errors, retries, latency, cost, and human
interventions off the traces. A model comparison that swaps the tool set at
the same time cannot say which change moved the number. [Stage
07](../07-eval/) is where this becomes an actual measurement discipline with
a baseline it refuses to skip; the point here is that the loop has to *emit*
the record before anything downstream can hold a variable fixed. The best
trace is not the longest one — it is the shortest one that still shows why
each action was allowed and how completion was verified.

## Twenty steps of observations will not fit

Every observation the loop injects stays in the transcript, and file contents
are not small. Eventually the next request exceeds the budget and the harness
must decide what to delete — a policy `ContextManager` keeps as a named,
swappable function rather than an `if` inside the loop.

[What fits in context](what-fits-in-context/) is that policy: collapsing a
superseded file read before discarding any decision, the message floor that
stops compaction from erasing the agent's own last move, and the just-in-time
tool design that makes per-observation compaction workable at all.

## The loop can act. What stops it?

Everything above makes the agent *capable* and *honest*: it reads files, runs
commands, and cannot invent an observation it did not receive. None of that
makes it safe — a grounding rule stops a fabricated result, not a real
command that should never have run.

[What stops it?](what-stops-it/) is the containment half — the jail and the
`pathlib` trap it exists for, the allowlist and why a denylist could not work,
the three risk tiers and a default that denies, and why three tools rather than
thirty is a containment decision before it is an accuracy one. It also states
the gap the composition leaves open, which is the part worth reading twice.

## One loop is stuck. Would a second one help?

Everything above is one loop answering to one context, one permission ladder,
one budget. Delegating part of the work to a second loop like itself is the
obvious next move and the most oversold one in this field, so it gets its own
chapter rather than a rule of thumb.

The contract is what makes it checkable. A delegated task has to name its
output artifact, the files or systems it may touch, what it must not do, the
command that verifies its result, and the format in which it reports what it
could not resolve. The child returns a *result*, not authority — the parent
still integrates and verifies. Miss any of those and you have not decomposed
the task, you have duplicated it with a handoff in the middle.

[Would a second agent help?](would-a-second-agent-help/) takes that further
than a rule of thumb can, because the question it asks is whether the second
agent bought anything at all or only doubled the bill — measured, at equal
total spend, against a supervisor implementation you can run on a CPU.

## Production notes

[`prod/README.md`](prod/README.md) maps each design decision above — the
loop, the tools, the grounding rule, context management, permissions — to how
mini-swe-agent, OpenHands, and Claude Code's published harness-design
write-ups handle the same decision at production scale.
[`LANDSCAPE.md`](LANDSCAPE.md) names four production harnesses rather than
one, deliberately: harness design is the independent variable this stage
argues about, so anchoring to a single project's choices would beg the
question.

## A real run

Point this harness at a served checkpoint instead of `FakeBackend`: the
mechanism holds, the model does not. Two tasks with ground truth stated
first ("how many Python files here" = 2; "which file defines
`resolve_in_jail`" = `tools.py`), three seeds each over
[`serve_for_agent.py`](runs/serve_for_agent.py): **0/6**. Every rollout
exhausted `max_steps` without one parseable `Action:`/`Final Answer:` —
this SFT checkpoint never saw the ReAct scaffold, so grounding never fired.
[Full transcripts.](runs/2026-07-30-real-agent-run.md)

**Reused elsewhere:** the loop, tool, and permission contract on this page is
the one
[personalized discovery's rule engine](../../02-personalized-discovery/07-rule-engine/)
and [the code-agent mission](../../04-code-agent/) both adopt — same inputs,
same objective, different tools. The chapter stays here, where it was worked
and measured, and those missions link to it.

## What does agentic training data actually need to teach?

The real run above did not just fail to solve its two tasks — it failed to
produce the *shape* of a tool call at all, and that specific failure is the
teaching example: it shows what a model that never saw agentic-formatted
training data actually outputs when a harness asks it to follow one.

Here is step 1 of `count-py-files` seed 1001, verbatim from
[`runs/transcripts/count-py-files-seed1001.json`](runs/transcripts/count-py-files-seed1001.json):

```
raw_response: "This is a list of 1000 Python files. It is a list of 128000
files. The name of the file is \":\""
grounding_triggered: false
observation: "Observation: could not parse a tool call -- no Action or Final
Answer found in the response"
```

That is fluent, on-topic prose — the model "knows" the question is about
Python files — but it contains no `Thought:`, no `Action:`, no
`Action Input:`. Every one of the 36 real steps across all 6 rollouts in that
run reads like this or worse: hedges, repetition loops, and one literal
`Action:<Tool name>` placeholder (`count-py-files` seed 1002, step 5) that is
the closest any generation came to the protocol — a template fragment, not a
call naming a real tool.

Contrast that with what a correctly shaped ReAct turn looks like
structurally. `harness.py`'s `DEMO_SCRIPT` is the canned script `FakeBackend`
plays back when `AGENT_BASE_URL` is unset — **scripted text, not model
output** — but it drives the same `list_dir`/`read_file` tools for real:

```python
DEMO_SCRIPT = [
    "Thought: let's see what's in the sandbox root.\nAction: list_dir\n"
    'Action Input: {"path": "."}',
    ...
]
```

Structurally: `Thought:` -> `Action:` -> `Action Input:` (JSON) -> real tool
execution -> `Observation:` injected by the harness -> the next `Thought:`.
Nothing about that shape is exotic; it is exactly what `parse_response`
looks for. The checkpoint used in the real run was SFT'd on
`HuggingFaceH4/no_robots` (see [`03-sft`](../03-sft/)) — chat-formatted
instruction/response pairs, never a single `Thought:`/`Action:`/`Observation:`
trajectory. It never saw the format, so it never learned to produce it, no
matter how relevant its prose is to the question being asked.

That is the honest conclusion this gap supports: this is a training-data
format problem, not a prompting problem. The system prompt handed to the
model in the real run states the `Action:`/`Action Input:` protocol
explicitly, so the failure is not a model failing to parse English
instructions — it is a model with no imitation target for a scaffold it has
never once seen a labeled example of, regardless of how the prompt is
worded. Closing this gap is a training-data composition question — mixing
agentic-formatted trajectories into the SFT corpus — not a harness or
prompt-engineering fix.

**Evidence boundary:** this shows one 88M-parameter checkpoint, SFT'd on one
non-agentic instruction dataset, failing at temperature 0.7 across 3 seeds on
two tool-only tasks. It does not show that agentic-formatted SFT data alone
would fix it, and it does not isolate training-data format from model scale
as the cause — both remain open, same as stated in
[the run log](runs/2026-07-30-real-agent-run.md).

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
2. **Run it against a real model.** Point `AGENT_BASE_URL` at stage 05's
   served model or an API you hold a key for. Does a real model ever try to
   write its own `Observation:` line, and does the grounding rule catch it
   the same way the `--demo grounding` script demonstrates?

## Next

[What stops it?](what-stops-it/) covers the sandbox, the permission ladder,
and the trust boundary this chapter deliberately set aside. Then
[would a second agent help?](would-a-second-agent-help/) if you are about to
add one. After that, [stage 07 — eval](../07-eval/): closing the loop with a
harness-disclosed evaluation of the agent built here, alongside the
model-level evals from earlier stages.
