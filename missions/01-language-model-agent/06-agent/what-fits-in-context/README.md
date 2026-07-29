---
status: draft
level: applied
base: none
label: What fits in context
---

# What do you throw away when the transcript stops fitting?

An agent that runs for twenty steps accumulates twenty observations, and file
contents are not small. At some point the next request will not fit, and the
harness has to decide what to delete. Delete the wrong thing and the agent
forgets the task; delete nothing and the loop dies at step twelve.

This is a policy question, and the useful move is to make it a *named,
swappable* policy rather than an `if` buried in the loop.

**Before this:** [what turns a model into something that acts?](../README.md),
through the grounding rule. You need to know that observations are
harness-generated and injected, because those are the messages this chapter
decides how to discard.

## A budget, and a function that enforces it

`ContextManager` tracks a token budget and compacts when it is exceeded.
`estimate_tokens` is a chars/4 stand-in — wiring in
[stage 01](../../01-tokenizer/)'s real tokenizer is exercise 1 of the parent
chapter, and the two disagree most on exactly the content an agent reads most:
code.

The policy itself is `drop_oldest_tool_results`, and it does two things in
order:

1. **Collapse superseded reads.** If a later message reads a path an earlier
   observation already read, the earlier one is replaced with a one-line stale
   marker. The newest read of any file is kept — an agent that read a file
   twice only needs the second read.
2. **Drop the oldest non-system turn**, one at a time, until under budget. Never
   the system prompt, and never past a floor of 3 messages: the model needs, at
   minimum, its own last action and the observation it produced.

**Worked.** Suppose the budget is 4,000 tokens and the transcript holds a
system prompt (200), six actions (60 each), and six observations, two of which
read the same 1,800-token file. Step 1 alone reclaims 1,800 by collapsing the
first read to a marker — more than step 2 would reclaim by discarding three
entire turns, and without losing a single decision the agent made. That
ordering is the whole design: collapse redundancy before you destroy history.

The floor of 3 is what stops the policy from being clever enough to break the
loop. Compact below it and the model is asked to continue from a transcript
that contains no evidence of what it just did.

## Where this sits among the alternatives

This is the lightweight, sliding-window-plus-summarization-adjacent style of
compaction most 2026 production harnesses run. The heavier alternative is
MemGPT's explicit paging interface (Packer et al., 2023), where the model
*itself* calls functions to move information between working and archival
memory. That buys deliberate retention — the model chooses what survives — and
costs a tool surface, a failure mode, and tokens spent on memory management
instead of the task. At a three-tool scale it is not worth it. At a
hundred-step scale it starts to be.

## The eager versus just-in-time split

This chapter's policy is downstream of a choice made in the tool design.
`read_file` and `list_dir` are **just-in-time** by construction: the agent
fetches only the file it decides it needs, exactly when it asks. The harness
never stuffs the whole sandbox root into context up front.

The alternative is **eager** retrieval — an embedding index built ahead of
time, queried once, its results placed in context before the agent reasons.

| | Just-in-time | Eager index |
|---|---|---|
| Round-trips | more | fewer |
| Freshness | exact, always current | goes stale |
| Debuggability | every read is in the transcript | retrieval is opaque |
| What compaction must handle | many small observations | one large block |

Neither is settled among production coding agents, and
[act and coordinate](../../../../capabilities/act-coordinate/) treats the choice
on its own terms. What matters here is that a just-in-time harness produces
*many small, individually droppable observations*, which is precisely what
makes a per-observation compaction policy workable.

## Check your mental model

1. Why does the policy collapse superseded reads before dropping old turns,
   rather than the other way round?
2. What breaks if the message floor is removed?
3. `estimate_tokens` uses chars/4. On which kind of observation would you
   expect that to be most wrong, and in which direction?
4. An eager index would reduce round-trips. What would it cost this
   compaction policy?

## Evidence boundary and next step

No agent run exists yet, so nothing here has been measured against a real
transcript. The policy is implemented and demonstrable with the deterministic
`FakeBackend`; whether the ordering in step 1 versus step 2 matters at real
scale is a claim awaiting `runs/`.

Return to [the loop can act — what stops it?](../README.md#the-loop-can-act-what-stops-it),
which is the containment question this one deliberately does not touch.
