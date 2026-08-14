---
status: draft
level: frontier
base: none
label: Harness comparison
---

# The same five decisions, filled in differently. Does the harness move the score?

**Question:** [stage 03](../agent-loop/) built one harness by hand — a
loop, three tools, a sandbox boundary, a context budget, a permission
ladder. Claude Code, Codex, Cursor, and the agent SDKs market themselves as
different products, but if the software around the model is really the
independent variable in agent scores, then reading any production harness
should be the same exercise as reading our own: the same five decisions,
filled in differently. Is that true — and does the difference move the
score more than the model does?

**The artifact this stage follows** is the comparison table: every harness
read as the same five decisions, with the mission's stage 03 harness and
its recorded runs as the reference column
([when-the-harness-moved-the-score](when-the-harness-moved-the-score/)).

**Before this:** stage 03 built the reference harness and verified it. This
stage reads other people's harnesses against it.

## The five decisions, as a reading lens

The claim that unlocks the stage: a harness is not a product, it is five
decisions. The mission's harness makes them explicitly, and every
production harness makes the same five, differently:

| Decision | The mission's harness | Claude Code / Codex |
|---|---|---|
| Loop | run → score → retry, capped | built-in agent loop, plan mode |
| Tools | read, write, run_command, jailed | Read/Edit/Bash + MCP servers |
| Sandbox | path jail, no network | filesystem scope, SOCKS5 network policy |
| Context | prompt + tool results, token budget | CLAUDE.md scopes / AGENTS.md + rolling memory |
| Permission | programmatic guardrails on the diff | approval policy ladder (untrusted / on-request / never) |

Read that way, the marketing difference collapses: Claude Code and Codex
are the same harness with different defaults in the same five columns
([reading-claude-code](reading-claude-code/),
[reading-codex](reading-codex/)). The editor-first agents, the open
harnesses (OpenHands, SWE-agent), and the SDKs
([reading-cursor-and-open-source-harnesses](reading-cursor-and-open-source-harnesses/),
[pi-and-the-agent-sdks](pi-and-the-agent-sdks/)) all fill the same table.
The skill the stage teaches is not knowing one product — it is being able
to ask, of any agent system, which of the five columns it owns and which
it delegates.

## The harness moves the score: two measured cases

The claim that the harness is the independent variable is not an opinion;
it has two sharp measurements.

The first is OpenAI's ARC-AGI-3 post: changing harness settings alone
moved a score from 13.3% to 38.3% while using 6x fewer tokens
([when-the-harness-moved-the-score](when-the-harness-moved-the-score/)).
Same model, same benchmark, different harness columns — the loop, the
tools, the context management. That 3x is the harness effect, measured.

The second is the field's own split-screen: SWE-bench-Live reports
state-of-the-art systems at 19.25% on the live set versus 43.20% on the
static Verified split. The gap is usually reported as "models got worse on
live tasks"; the stage's reading is that the gap is a harness property —
the static set leaks the task into context in ways the live set does not,
so the same system scores differently depending on what the harness is
allowed to see.

## The mission's own measured delta

The stage can cite one number from its own side, and it is the same shape
at one-task scale: stage 03's recorded harness-versus-no-harness runs
([stage 01's baseline](../no-harness/)) show the loop moving resolve from
0/6 to 6/6 at the cheap tier — a harness effect larger than any model-tier
effect the mission measured. The ARC-AGI-3 3x and the mission's 0/6→6/6
are the same phenomenon: the software around the model is worth more than
the model swap, at every scale measured.

## What this stage does and does not establish

It establishes the reading skill: five decisions as the lens, two external
cases that prove the harness effect, and the mission's own recorded delta
as the run-backed anchor. The external numbers are dated surveys with
sources cited; the mission's delta is run-backed.

It does not claim one harness is best — the table has no winner column,
because the right defaults depend on the task and the risk, which the next
stage prices. And it does not claim every score difference is harness:
the point is narrower and sharper — *you cannot attribute a score until
you have read the five columns*, and most published comparisons never show
them.

**Next:** the harness is read; the question becomes which model tier should
run inside it, and what each resolved task actually costs —
[cheap or expensive](../cheap-or-expensive/).
