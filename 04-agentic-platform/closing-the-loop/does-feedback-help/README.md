---
status: verified
level: applied
base: none
label: Does feedback help
verified: 2026-08-06
---

# Does seeing the real outcome help — with still no tools?

**Question:** [stage 06](../) gives the agent one retry turn with its prior
attempt's real test outcome and no tools. The recorded run kept 12
attempts; this chapter reads the log and lays out what the feedback bought.

**Before this:** [stage 06's closing-the-loop run](../) and the
no-harness baseline.

## The log, read

The analysis ([record](runs/2026-08-06-closing-loop.md)) reads the 12
recorded attempts:

| | closing-the-loop (1 retry) | no-harness (blind call) |
|---|---:|---:|
| resolved | 2/12 | 4/18 |
| patch applied | 2/2 of resolved | 5/18 |
| cost per attempt | \$0.254 | \$0.286 |

## Two readings

**Feedback alone does not raise the resolve rate — it changes what the
failure looks like.** The retry resolves 2/12, no better than the blind
call's 4/18. But both resolved retries started from a prior
target_still_failing with no applicable patch, and both produced an
applicable patch this time. The failure-cost chapter measured the dominant
blind failure as non-applicable patches (11 of 12); the feedback's effect is
exactly there — seeing why the blind patch failed turns "cannot apply" into
"can try," and 2 of 12 of those retries now resolve.

**A retry is a priced turn, not a free pass.** The feedback attempt costs
\$0.254 on average, comparable to a blind call. Closing the loop is a
budget decision: it buys the chance to convert a non-applying failure into
an applicable one, at roughly one more model call per task — which is
precisely the cost-per-resolved framing the mission reports elsewhere.

## The fix and its trade

The fix is the outcome-feedback retry read as a failure-class converter:
feedback alone does not raise the resolve rate (2/12 versus the blind
call's 4/18), but it changes what the failure looks like — both resolved
retries started from a prior non-applicable patch and produced an
applicable one this time, and the dominant blind failure (11 of 12
non-applicable) is exactly where the effect lands. The trade is that a
retry is a priced turn: \$0.254 per attempt, roughly one more model call
per task, so the decision is whether converting "cannot apply" into "can
try" is worth the extra dollar on the cost-per-resolved ledger — a
comparison the recorded numbers start and do not finish.

## Who owns the loop

- **The eval owner** owns the failure-class read: resolve rate alone
  hides the conversion from non-applicable to tryable, and the
  comparison's value is in that class change, not in the flat rate.
- **The harness owner** owns the retry mechanics — real-error capture,
  base-state reset, tools still denied — that make the feedback what it
  claims to be.
- **The budget owner** owns the cost-per-resolved decision: the extra
  \$0.254 must be weighed against additional resolutions, and against
  the alternative uses of the same dollar (more tool turns, more blind
  attempts).

## Evidence boundary

Twelve recorded attempts (haiku 6, sonnet 3, opus 3), one retry each, no
tools; the no-harness baseline is the recorded 18-attempt run. It shows the
feedback's effect on this task set; it does not claim feedback beats tools
(the harness stage's 18/18 is the other end of the axis) and does not
re-run the attempts.

## Check your mental model

Answer each before opening it.

**1. The resolve rate did not improve over the blind call, yet the stage
still reports the result as informative. Why?**

<details>
<summary>Answer</summary>

Because the failure class changed: the blind call's dominant failure was a
patch that could not be applied at all, and the feedback retries produced
applicable patches — 2 of which resolved. Resolve rate alone hides that the
loop converted the worst failure mode (non-applicable) into a tryable one,
which is the difference between "the model cannot fix it" and "the model
needs more turns to fix it."

</details>

**2. What would the closing-the-loop comparison need to decide whether the
extra turn is worth it?**

<details>
<summary>Answer</summary>

The cost-per-resolved comparison: the retry's extra \$0.254 per attempt must
be weighed against how many additional resolutions it buys. If the extra
turn raises resolution per dollar spent, the loop earns its cost; if not,
the answer is to spend the budget on more tools (the harness arm) or on
more blind attempts instead. The recorded numbers are the start of that
comparison, not the end.

</details>

## Next

Back to [stage 06's closing-the-loop](../), or to
[stage 05's report](../../05-report/) where every number across the mission
is held against the acceptance list.
