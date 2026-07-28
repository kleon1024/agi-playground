---
status: draft
label: Multi-agent
---

# One agent is stuck. Would a second one help?

And how would you know it was not simply twice the cost?

[Agent systems](../README.md) built one bounded loop: observe, decide,
propose, validate, execute, record, decide again. Everything in that loop
answers to a single parent — one context, one permission ladder, one budget.
This chapter asks what changes the moment a parent delegates part of the work
to another loop like itself, and stays sceptical throughout, because
multi-agent systems are one of the most oversold ideas in this field. A
second agent is not a free multiplier on capability. It is a specific trade,
and the trade is only worth it under conditions this chapter tries to name
precisely.

## 1. What a second agent actually buys

Three reasons are real, and they are different reasons, not three names for
the same benefit.

**Context isolation.** A sub-agent's tool output — a file dump, a log, a
search result — never enters the parent's context. Only the sub-agent's
conclusion does. The parent's window is spent reasoning about results, not
re-reading the evidence that produced them. This is the same trade the
harness README makes for `read_file`: fetch only what is needed, when it is
needed. Delegation applies the identical discipline across an agent boundary
instead of a tool boundary.

**Parallelism over genuinely independent work.** If two subtasks touch no
shared state and neither's output feeds the other, running them concurrently
shortens wall-clock time without changing what gets computed. This only pays
off when the independence is real — a claim the next section makes
checkable rather than assumed.

**Independent perspective.** A second agent that has not seen the first
agent's reasoning can catch an error the first agent is anchored on, or
propose an approach the first agent's framing ruled out. The value comes
specifically from the second agent *not* having seen the first one's trace
— which puts this in tension with context isolation: an independent
perspective needs a full second attempt, not a compressed summary of the
first one.

## 2. The costs, which are usually understated

**Every handoff is a lossy serialization.** A sub-agent's understanding —
everything it inferred while doing the work — has to survive being written
down as text and read back by another process. Anything the sub-agent
"just knew" from working through the problem step by step and did not
explicitly state does not cross the boundary.

**Error compounds along a chain.** A parent that verifies nothing forwards
a sub-agent's mistake unchanged. A pipeline of three agents does not have
one chance to get it wrong; it has three, plus every handoff between them.

**Cost multiplies while quality does not.** Every additional agent adds
tokens for its own reasoning plus the tax of its handoff, whether or not
that agent improves the outcome. Nothing about adding a fourth agent
guarantees a fourth agent's worth of quality.

**Debuggability collapses.** A single-agent trace has one place to look
when something goes wrong. A multi-agent trace has N agents and N-1 (or
more) handoffs, any of which could be where a fact was lost, a task was
misread, or a conclusion was overstated on the way up.

## 3. The orchestration contract

A parent and child do not share ownership of the same things. The parent
owns the task scope handed down, the child's tool permissions, its budget,
its stop condition, and the shape of the result it must return. The child
owns how it gets there — which of its own bounded loop's steps it takes,
in what order, subject only to what the parent granted it.

Structured returns beat prose returns for the same reason a typed tool
schema beats a free-text command in the single-agent harness: the parent
has to act on what comes back, and prose that a person would read without
difficulty is not something a program can safely branch on. A return worth
trusting names its status, its artifact, and what it could not verify — not
a paragraph the parent must re-interpret before it can decide anything.

The parallel-safety rule follows from what each side owns: two subtasks may
run in parallel only when they share no output and neither depends on the
other's intermediate decisions. Anything else is sequential work wearing a
parallel costume — it will appear to run concurrently and still produce a
result that depends on execution order, the same silent-corruption failure
mode the capability README warns about for tool calls, one level up.

## 4. Topologies, and the decision rule for each

**Single agent.** The default. Use it until a specific limitation of the
loop — not a general sense that "an agent team sounds more capable" —
names a concrete reason to add a second one.

**Supervisor with workers.** One parent decomposes a task into independent
pieces, dispatches them, and integrates structured returns. Use this when
the work genuinely divides into pieces with disjoint outputs — the
supervisor's job is coordination, not redoing the workers' reasoning.

**Pipeline.** Each stage's output is the next stage's input, strictly in
order. Use this when the task is a sequence of transformations where each
step depends on the previous one's result — there is no parallelism to
exploit, but the context each stage needs shrinks to just its own input,
not the whole history.

**Debate or panel.** Multiple agents attempt the same task independently,
and a judge compares full answers rather than compressed summaries. Use
this specifically for the independent-perspective benefit, and only when
that benefit is worth paying for every participant's full context at the
comparison step — this is the one topology that spends context to buy
diversity rather than saving it.

<!-- interactive: AgentTopology -->

## 5. How you would know it helped

The comparison that matters holds total token cost equal. A multi-agent
system compared against a single agent working with a fraction of the
budget is not a fair test — of course the smaller-budget agent does worse.
The honest question is: at the same total spend, does the multi-agent
version produce a better result than a single agent given that entire
budget to work with directly? [Section 9 of the parent
chapter](../README.md) makes the same point about evaluating a harness: a
comparison that changes more than one variable at a time cannot attribute
the result to any of them. Comparing topologies without holding cost fixed
is that same mistake, applied to agent count instead of tool set.

`core/orchestrator.py` makes this concrete rather than asserted. Its demo
task graph — scan two independent modules, merge the results, then re-scan
one module under a stricter rule with nothing declaring that as a
dependency on the first scan — runs a small supervisor-and-workers
implementation on a CPU with a scripted, deterministic backend. Running it
produces two real facts: the scheduler correctly refuses to run the re-scan
alongside the original scan, because both write the same output even
though neither names the other as a dependency; and the total token cost
of doing this work through the supervisor (737, from this file's own demo)
comes out well above the same four answers computed by one agent directly
(97) — a real 7.6x, computed by the code, not asserted by this prose.

That ratio is a property of this toy's fixed per-handoff tax, not a claim
about any production system's overhead. What generalizes is the shape of
the comparison: wall-clock fell from four sequential steps to three
batches, while token cost rose, because parallelism and cost are not the
same axis and a topology can win on one while losing on the other.

## 6. Evidence boundary

`core/orchestrator.py` demonstrates that the parallel-safety rule and the
structured-return contract are checkable properties of a task graph and a
worker response, and that total token cost is computable rather than
assumed. It does not demonstrate that any topology improves task success
on real work — that requires running real agents against real tasks at
matched budget, which has not happened here and has no `runs/` entry. The
widget's numbers are illustrative, derived from a small set of stated
constants, and labeled as such; they are not measurements of any deployed
system.

## Production notes

[`prod/README.md`](prod/README.md) maps the loop, the contract, and the
topologies above to how LangGraph, AutoGen/AG2, CrewAI, and Claude Code's
own sub-agent feature handle the same decisions at production scale.

## Check your mental model

1. Which of the three benefits in section 1 does a debate/panel topology
   buy, and which does it explicitly give up in exchange?
2. Why does a shared write between two tasks force sequencing even when
   neither task's `depends_on` names the other?
3. What must a structured return contain that a well-written paragraph
   answering the same question would not reliably contain?
4. Why is comparing a 3-agent system against a single agent at one-third
   the token budget not evidence that the 3-agent system is better?
5. Which topology minimizes lossy handoffs, and what does it give up to get
   that?

## Next

[Mission 01, eval](../../../missions/01-language-model-agent/07-eval/)
builds the harness-disclosed, baseline-required evaluation discipline this
chapter's equal-budget comparison depends on. It was built for a
single-agent harness; extending its refuse-to-emit-without-a-baseline
discipline to a multi-agent transcript is unbuilt work, not a claim already
proven here.
