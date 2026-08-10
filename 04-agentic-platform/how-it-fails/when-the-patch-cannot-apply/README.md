---
status: verified
level: applied
base: none
label: When the patch cannot apply
verified: 2026-08-06
---

# When the patch cannot even be applied, what is the loop buying?

**Question:** [stage 04's taxonomy](../) counted the no-harness failures by
category. This chapter reads the same logs and asks what those failures
*cost* — how many blind calls produced a patch that could not be applied at
all, which model resolved what, and whether the tool loop is worth its
higher total spend.

**Before this:** [stage 04's failure taxonomy](../) and its category table.

## The dominant failure is no applicable patch

The analysis ([run record](runs/2026-08-06-failure-costs.md)) reads the
mission's own two result logs:

| | no-harness (blind call) | harness (tool loop) |
|---|---:|---:|
| resolved | 4/18 | 18/18 |
| patch applied | 5/18 | — (scored outcome: resolved) |
| target still failing | 12/18 | 0/18 |
| total cost | \$5.14 | \$9.12 |
| cost per resolved | \$1.286 | \$0.507 |

The headline is the 5/18: of the 12 blind calls that left the target
failing, 11 produced a patch `git apply` rejected outright (stage 04's
taxonomy counted them). The dominant no-harness failure is not a wrong fix —
it is a non-fix, a patch that cannot even be tried. The model wrote a diff
whose hunk headers disagree with its body, and the harness never got a
chance to run it.

## The failures concentrate, and they are checkable

The 12 failures cluster on four target tests — the two decode-correctness
identity checks and two sync-docs checks — each failing 7 of 18 attempts.
The blind model cannot reproduce an exact recompute it never sees, and the
repo's identity-check discipline (the bug that made a serving engine
*faster* while being wrong) is exactly the kind of check a blind patch
guaranteed to fail. Resolution by model tells the same story: opus 3, sonnet
1, haiku 0 — the capability ordering a single blind call cannot escape.

## What the loop buys, priced

The harness spends more in total (\$9.12 vs \$5.14) and resolves 14 more
tasks, at \$0.507 per resolved versus \$1.286 — the loop is cheaper per
resolution because the failures stop failing. The zero-failure surface stage
04 recorded (18/18, including haiku at 6/6) is the concrete version of what
test feedback buys: the cheap tier becomes reliable when it can see the
test's real outcome, which is the mission's central claim measured rather
than asserted.

The tamper guardrail never fired across the 36 real attempts — recorded in
stage 04 and not re-counted here. It is the reason the scoreboard stays
honest when the harness does work; a zero failure count would mean nothing
if the failures had been deleted instead of fixed.

## The fix and its trade

The fix is the applied/resolved split plus the cost-per-resolved reading:
5 of 18 blind patches applied at all, and the loop is priced at \$0.507
per resolved versus \$1.286 for the blind call. The trade is that the
harness spends more in total (\$9.12 vs \$5.14) to buy 14 more
resolutions — a per-attempt comparison would flatter the blind call, which
is why the mission reports cost per resolved task. The split's real
payoff is attribution: the dominant no-harness failure is a non-fix (11
of 12 non-resolving attempts never applied), so no amount of test
feedback at the end of the call could have helped — the fix has to live
in the loop, which is exactly what the harness provides and what the
measured price difference pays for.

## Who owns the loop

- **The harness owner** owns the tool loop and the failure attribution
  that justifies its cost — the loop is cheaper per resolution because
  it stops the failures from failing.
- **The routing owner** owns the metric that makes the comparison honest:
  cost per resolved task, never cost per attempt.
- **The eval owner** owns the cluster read: the 12 failures concentrate
  on identity checks (two decode-correctness, two sync-docs), which is
  the distribution a blind patch is guaranteed to miss.

## Evidence boundary

This chapter re-measures the mission's own recorded logs (18 + 18 model
attempts, three tiers); it adds no new model calls. The cost figures are the
recorded `cost_usd` fields. It does not show the loop wins on every task
class or every model — it shows the recorded failure surface and its price.

## Check your mental model

Answer each before opening it.

**1. Why does "patch applied: 5/18" matter more than "resolved: 4/18"?**

<details>
<summary>Answer</summary>

Because it locates the failure. 4/18 resolved says the blind model is weak;
5/18 applied says the weakness is mostly upstream of testing — 11 of the 12
failures never produced an applicable patch, so no amount of test feedback
at the end of the call could have helped. The fix has to be in the loop
(tools, iteration), not in a better prompt, which is exactly what the
harness provides.

</details>

**2. The harness costs 1.77x more total but is cheaper per resolution. What
reconciliation makes that consistent?**

<details>
<summary>Answer</summary>

The harness spends more because it buys more attempts and tool calls, and it
resolves 14 more tasks with that spend: \$9.12 / 18 = \$0.507 versus \$5.14 /
4 = \$1.286. A per-attempt cost comparison would flatter the blind call,
which is why the mission reports cost per *resolved* task, not cost per
attempt — the same reason resolve rate is reported beside dollars per
resolved task rather than beside prompt cost.

</details>

## Next

Back to [stage 04's taxonomy](../), or forward to
[stage 06's closing the loop](../../06-closing-the-loop/) where the agent
sees its own attempt's real outcome with still no tools.
