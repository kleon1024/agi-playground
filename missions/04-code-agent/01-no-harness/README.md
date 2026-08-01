---
status: verified
level: applied
verified: 2026-08-01
label: No harness
---

# Is the loop worth anything over one blind call?

**Question:** stage 03 gave a coding agent tools, a test command, and up to 25
steps of feedback, and it resolved 18/18 real attempts. Would one blind model
call, with no tools and no chance to check its own work, have done just as
well?

**The artifact this chapter follows** is the same matrix stage 03 ran, stripped
to one call per attempt:

```text
resolved     harness (stage 03)   no-harness (this stage)
haiku        6/6                  0/6
sonnet       6/6                  1/6
opus         6/6                  3/6
```

By the end you will be able to say why a lower-resolving arm can still cost
more per success, and at which tier this task set is too small to call the gap
a real result rather than noise.

**Before this:** [stage 00](../00-task-set/), which supplies the tasks, and
[stage 03](../03-cheap-or-expensive/), which supplies the matrix this repeats
without the loop.

## What "no harness" means here

One `claude -p` call per attempt, every tool Claude Code has denied by name
via `--disallowedTools` — not an empty allow list, a deny list, for the same
reason [stage 02's `claude_arm.py`](../02-agent-loop/core/claude_arm.py) denies
the web tools explicitly instead of leaving them off an allow list: absent by
omission and denied are not the same guarantee if the tool set is ever widened
by accident.

With no `Read` tool, the model cannot see the repository unless the prompt puts
it there. So the prompt includes the current contents of exactly the file(s)
[stage 00's task construction](../00-task-set/) already names as the ones the
gold patch touches — what the SWE-bench literature calls **oracle file
location**. This baseline does not measure "can it find the bug." It measures
"can it fix the bug once told exactly where it is," with the harness's own
`Grep`/`Read` step handed to it for free and nothing else.

The model's only channel back is text, so it replies with a unified diff and
nothing else. [`core/no_harness.py`](core/no_harness.py) applies that diff with
plain `git apply` — blind. No retry if it fails to parse, no repair, no second
prompt. A malformed diff is not a bug in this harness to fix; it is exactly the
outcome [stage 04](../04-how-it-fails/) needs a category for.

## The result

| Model | Resolved | $/resolved | Compare: harness (stage 03) |
|---|---|---|---|
| haiku | 0/6 | n/a | 6/6, $0.1604 |
| sonnet | 1/6 | $1.3744 | 6/6, $0.5369 |
| opus | 3/6 | $1.0924 | 6/6, $0.8226 |

Pooled: 4/18 resolved without a loop, against 18/18 with one. At `haiku` and
`sonnet` the gap is decisive against the run-to-run spread of the no-harness
arm itself (margins of +1.000 and +0.833 against spreads of 0 and 0.5). At
`opus` the margin (+0.500) sits *inside* the no-harness arm's own spread
(1.000, from a per-run resolved fraction of 0 → 0.5 → 1.0 across its three
repeats) — with only 2 tasks, that specific tier's comparison is a real no
result, not a smaller win. Full numbers, including the wall-clock cap two
`sonnet` attempts hit, in [`runs/`](runs/2026-08-01-no-harness-baseline.md).

## The number that flatters neither arm

A lower resolve rate does not mean a cheaper one. `sonnet`'s no-harness arm
resolves 1/6 at $1.3744 per resolved task — *more* than its own harness
arm's $0.5369, despite each individual call costing less than a full tool
loop. The five unresolved attempts (one timeout at $0, four real spends on
wrong or non-applying patches) still cost money, and dividing a similar total
spend by a much smaller resolved count punishes cost-per-resolved harder than
cheap-but-wrong attempts help cost-per-attempt. This is the exact distinction
`mission.yaml` names cost-per-*attempt* as the wrong number for: it flatters
whichever arm fails fastest, and here the no-harness arm fails often without
failing particularly cheaply.

## Check your mental model

1. Every no-harness attempt was handed the exact file the fix belongs in. What
   does that concession mean this stage does, and does not, measure about "can
   an agent find the bug"?

<details>
<summary>Answer</summary>

It means this stage does NOT measure whether an agent can locate the bug at
all — the prompt already includes the contents of exactly the file stage
00's task construction names as the one the gold patch touches, oracle file
location in the SWE-bench sense. What it DOES measure is narrower and
cleaner: given the right file already in view, can the model fix the bug in
one blind shot, with no `Read`/`Grep` step and no chance to check its own
work. Handing over the file for free is what isolates that one question —
without the concession, a failure to resolve could mean "couldn't find it"
or "found it but fixed it wrong," and this stage would not be able to tell
which.

</details>

2. `sonnet`'s no-harness resolve rate is 1/6, lower than `opus`'s 3/6, but its
   `$/resolved` figure is *higher* than `opus`'s too. Reconcile that with
   "cheaper tiers resolve less."

<details>
<summary>Answer</summary>

`$/resolved` divides total spend by resolved *count*, not by attempt count,
so a tier that fails often still spends money on every failed attempt —
sonnet's five unresolved attempts (one timeout at $0, four real spends on
wrong or non-applying patches) get divided across only one success, which
punishes the ratio harder than opus's fewer, costlier-per-call failures
divided across three successes. "Cheaper tiers resolve less" describes the
resolve-rate axis; it says nothing about cost-per-resolved, which depends on
how much was spent on the failures too. The two rankings can and do diverge —
that's the whole point of the section title, "the number that flatters
neither arm."

</details>

3. The `opus`-tier margin (+0.500) is smaller than that tier's own run-to-run
   spread (1.000). What does declaring that a "no result" protect against, that
   reporting a 50-point win would not?

<details>
<summary>Answer</summary>

It protects against mistaking noise for a finding. With only 2 tasks and 3
repeats, opus's own per-run resolved fraction swings from 0 to 0.5 to 1.0 —
a spread of 1.000 — which is larger than the +0.500 gap between the harness
and no-harness arms. A gap smaller than the arm's own run-to-run variability
could easily flip sign on a different set of 3 repeats, so reporting it as a
"50-point win" would claim the harness helps at this tier when the data
cannot actually distinguish that from chance. Declaring it a no result is the
same discipline mission 01's 04-rl stage applies to its own zero-gradient
outcome: an honest "cannot tell" instead of a number rounded into a claim it
doesn't support.

</details>

**Next:** [stage 04](../04-how-it-fails/) catalogues every real failure this
mission has produced, across both arms, by category — including the
malformed-diff failure mode this stage's own attempts supplied most of.
