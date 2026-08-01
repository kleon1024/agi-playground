---
status: verified
level: applied
base: none
label: What fits in context
verified: 2026-07-30
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

<details>
<summary>Answer</summary>

Because collapsing redundancy reclaims tokens without losing any decision the
agent made, while dropping a turn destroys history outright. The worked
example makes the gap concrete: collapsing one stale 1,800-token read reclaims
more budget than discarding three entire turns would, and it does so for
free — the agent only ever needed the *second* read of a file it read twice,
so the first read was already redundant information, not evidence. Doing the
cheap, lossless reclaim first means the destructive step (dropping oldest
turns) only runs when redundancy alone can't cover the overage.

</details>

2. What breaks if the message floor is removed?

<details>
<summary>Answer</summary>

The policy could compact past the point where the model has its own last
action and the observation it produced, which is the minimum evidence needed
to continue the task at all. Without the floor, an aggressive compaction
could ask the model to keep acting from a transcript that contains no record
of what it just did — the loop wouldn't crash, but the agent would be
reasoning blind, which is a worse failure than the one the floor is
guarding against (an overage that stays slightly over budget).

</details>

3. `estimate_tokens` uses chars/4. On which kind of observation would you
   expect that to be most wrong, and in which direction?

<details>
<summary>Answer</summary>

Code — the chapter says explicitly that a real tokenizer and the chars/4
stand-in "disagree most on exactly the content an agent reads most: code."
Code has a much higher density of short tokens (punctuation, operators,
indentation, short identifiers) than the prose chars/4 was calibrated
against, so a real tokenizer would count *more* tokens per character than
chars/4 assumes — meaning chars/4 underestimates the true token cost of code
observations, which is the direction that risks a budget breach the
estimator didn't see coming.

</details>

4. An eager index would reduce round-trips. What would it cost this
   compaction policy?

<details>
<summary>Answer</summary>

It would replace many small, individually droppable observations with one
large retrieved block, which is precisely what makes per-observation
compaction workable in the just-in-time design. The comparison table names
the tradeoff directly: what compaction must handle shifts from "many small
observations" to "one large block," losing the fine-grained ability to
collapse or drop individual stale reads one at a time. It would also trade
away freshness (an index goes stale) and debuggability (every just-in-time
read is visible in the transcript; retrieval from a pre-built index is
opaque) for fewer round-trips.

</details>

## What a real run of the policy actually shows

Called directly against a scripted transcript sized to cross the budget
(no model, no network — [`core/demo_compaction.py`](core/demo_compaction.py)),
`ContextManager` does exactly what's claimed above. A second read of the same
path crosses a 3,000-token budget; collapsing the first, now-stale read to a
16-token marker reclaims 1,784 tokens and resolves the overage in one
compaction, without a single turn dropped — step 1 handles it before step 2
is ever reached. Against a 30-token budget with nothing collapsible, seven
compactions drop the oldest turn one at a time until exactly 3 messages
remain, then stop — the transcript stays over budget (50 tokens against a
30-token target) rather than erase the model's last action and its own
observation. [Full output.](runs/2026-07-30-compaction-demo.md)

## Evidence boundary and next step

The parent mission's real agent run against a served checkpoint
([`../runs/2026-07-30-real-agent-run.md`](../runs/2026-07-30-real-agent-run.md))
never exercised either path above: all 6 rollouts hit `max_steps` before the
transcript grew large enough to cross the token budget, so this policy has
now been verified in isolation, not yet inside a real multi-step agent run
that actually fills its context window.

Return to [the loop can act — what stops it?](../README.md#the-loop-can-act-what-stops-it),
which is the containment question this one deliberately does not touch.
