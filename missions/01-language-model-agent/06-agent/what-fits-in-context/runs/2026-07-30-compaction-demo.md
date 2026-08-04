# Run — ContextManager's compaction policy, exercised directly

This chapter's parent-mission agent run
([`../../runs/2026-07-30-real-agent-run.md`](../../runs/2026-07-30-real-agent-run.md))
never exercised `ContextManager`: all 6 rollouts hit `max_steps` before the
transcript ever grew large enough to cross the token budget, so
`drop_oldest_tool_results` never fired in that run. This run isolates the
compaction policy itself, calling `core/harness.py`'s real `ContextManager`
directly against a scripted transcript sized to force it -- no model, no
network, fully deterministic.

## Hardware and software

| | |
|---|---|
| Machine | local (macOS, arm64), no GPU needed |
| Code under test | `missions/01-language-model-agent/06-agent/core/harness.py`'s `ContextManager` and `drop_oldest_tool_results`, imported unmodified via `sys.path.insert` |
| Script | [`core/demo_compaction.py`](../core/demo_compaction.py) |
| Cost | \$0 |

## Demo A: collapse a superseded read before dropping any turn

Budget 3,000 tokens. Six action/observation turns, two of which read the
same path (`notes.md`) at ~1,800 tokens each -- the same shape as the
chapter's own worked example. Before the second read, the transcript sits at
2,090 tokens; the second read alone would push it to 3,890, over budget.

```
before the second read: tokens=2090 (budget 3000)
after the second read of notes.md (compaction fires inside this add()):
  messages=9  tokens=2106  compactions=1
    [0] system       10tok  '(system prompt)'
    [1] assistant    60tok  '(action)'
    [2] user         16tok  "[stale read of 'notes.md', superseded by a later"  [read_file_path='notes.md']
    [3] assistant    60tok  '(action)'
    [4] user         20tok  '(small observation)'
    [5] assistant    60tok  '(action)'
    [6] user         20tok  '(small observation)'
    [7] assistant    60tok  '(action)'
    [8] user       1800tok  '(second read of notes.md)'  [read_file_path='notes.md']
```

Compaction fired exactly once and never touched the drop-oldest path:
collapsing the first, now-superseded read of `notes.md` to a 16-token marker
reclaimed 1,784 tokens on its own, landing at 2,106 -- under budget without
deleting a single turn. Two more turns land at 2,186 tokens with no further
compaction (`compactions` stays at 1). This is the chapter's claim exactly:
step 1 (collapse) resolves the overage before step 2 (drop) is ever reached.

## Demo B: the floor of 3 holds even while still over budget

Budget 30 tokens, nothing collapsible (no repeated `read_file_path`), eight
more small turns added one at a time.

```
after 8 more turns against a 30-token budget with nothing collapsible:
  messages=3  tokens=50  compactions=7
    [0] system       10tok  '(system prompt)'
    [1] assistant    20tok  '(observation)'
    [2] user         20tok  '(observation)'
```

Seven compactions ran (one per turn once the transcript first went over
budget), each one dropping the oldest non-system message -- until only 3
messages remained. At that point the transcript is still over budget (50 >
30) and stays that way: the `while` loop's `len(ctx.messages) > 3` guard
stops deletion before the model's last action and its own observation would
be removed. The budget is a target the policy tries to honor, not a hard
ceiling it will violate the floor to reach.

## What this does and does not establish

- **Does establish**: `ContextManager` and `drop_oldest_tool_results` behave
  exactly as described -- collapse-before-drop ordering, and a floor that
  overrides the budget rather than the reverse -- against a real, if
  synthetic, transcript.
- **Does not establish**: what either policy does at real agent scale, with
  real tool-call token sizes and a real model's actual read/re-read pattern.
  The parent mission's real agent run never grew a transcript large enough to
  reach either path; that remains open.

## Reproduce

```bash
cd missions/01-language-model-agent/06-agent/what-fits-in-context/core
python demo_compaction.py
```
