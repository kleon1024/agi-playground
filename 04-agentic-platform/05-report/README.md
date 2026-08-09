---
status: verified
level: applied
verified: 2026-08-01
label: The report
---

# What did this mission actually establish?

**Question:** five stages, three model tiers, thirty-six real attempts, one
declared contract written before any of them ran. Which of `mission.yaml`'s
seven acceptance bullets does the evidence actually meet?

**The artifact this chapter follows** is one printed verdict per bullet,
produced by a script that reads only committed `runs/` records and cannot
soften a number after seeing it:

```text
1. beats no-harness beyond spread, both sets   -> PARTIAL
2. beats always-frontier on $/resolved          -> MET
3. guardrails hold, tampering fired-or-honest   -> MET
4. public/private reported separately           -> MET
5. latency and dollars, real and in budget       -> MET
6. failures catalogued by category              -> MET
7. every number traces to runs/                 -> MET
```

By the end you will be able to say why bullet 1 reads `PARTIAL` rather than a
clean `MET` or `NOT MET`, and why that is a narrower, more specific gap than
the "no public set exists at all" gap this chapter used to report.

**Before this:** every other stage in this mission, including
[stage 00](../00-task-set/)'s later addition of a mined-and-verified public
task set (`tasks/public.jsonl`, sourced from a permissively-licensed public
repository's own git history, disjoint from the original private set).
[`core/report.py`](core/report.py) reads stage 00's public and private
manifests and [stage 01](../01-no-harness/)/[stage 03](../03-cheap-or-expensive/)'s
`runs/` JSONL directly; nothing here is hand-copied.

## Why bullet 1 says PARTIAL, not MET or NOT MET

A public task set now exists — the gap this section used to describe (bullets
1 and 4 both undecidable because only a private set was ever mined) has been
closed by a later stage-00 addition. Bullet 4 is a clean `MET` now: both sets'
resolve rates are measured and reported side by side, never pooled (18/18
private, 6/6 public).

Bullet 1 stays `PARTIAL` for a narrower reason. On the **private** set, the
harness beats no-harness decisively at `haiku` and `sonnet`, and produces a
genuine no-result at `opus` (the margin sits inside that arm's own
run-to-run spread at N=2 tasks — full numbers in
[stage 01](../01-no-harness/)). On the **public** set, only the harness arm
has ever been run (6/6 resolved on `haiku`) — no no-harness control exists to
compare it against, because building one was out of this addition's scope.
Bullet 1 literally asks for "beats no-harness... both sets," and half of
that comparison has no denominator to check against. `report.py` reports
that half as `CANNOT DETERMINE` within an overall `PARTIAL`, rather than
either assuming the private-set result transfers or silently rounding the
bullet to `MET` on the strength of the public set's own resolve rate alone.

## What the other six bullets say

**Bullet 2 (cost) is MET**, with a scope note carried forward rather than
erased: `mission.yaml`'s `decision` field names a locally-served open-weights
model against a hosted frontier one. Stage 03 ran three hosted-subscription
tiers of a single CLI instead — a scope decision made before this report
existed. The bullet is answered honestly on the tiers that actually ran, which
is not the same claim as answering it on the tiers `mission.yaml` originally
named.

**Bullet 3 (guardrails) is MET.** Zero regressions across 42 real attempts
(18 private harness, 18 private no-harness, 6 public harness). Zero real
test-tampering firings — reported as "never fired," per the mission's own
explicit-or-fired branch, with the scripted stage 02 demonstration cited but
not counted as a real one.

**Bullet 4 (public/private separation) is MET**, per the section above.

**Bullets 5, 6, 7 are MET** on their own terms: every dollar and wall-clock
figure traces to a `runs/` JSONL line (now including the public set's stage-00
attempts in the total), [stage 04](../04-how-it-fails/) catalogues every real
failure by category, and this script is the mechanism that makes bullet 7
true of itself.

<!-- interactive: AgentReport -->

## Check your mental model

1. Why does bullet 1 read `PARTIAL` rather than a clean `MET` or `NOT MET`,
   now that both a public and a private task set exist?

<details>
<summary>Answer</summary>

`PARTIAL` means the bullet decomposes into pieces that don't all point the
same way, and at least one piece has no evidence to check at all — different
from "failed," which would mean the evidence exists and says no. On the
private set, the harness beats no-harness decisively at `haiku` and `sonnet`,
and produces a genuine no-result at `opus` (the margin sits inside that arm's
own run-to-run spread at N=2 tasks). On the public set, only the harness arm
has ever run — 6/6 resolved on `haiku` — with no no-harness control to
compare it against. Bullet 1 literally asks for "beats no-harness... both
sets," so the public half is `CANNOT DETERMINE`, not silently assumed to
inherit the private set's decisive result, and not silently rounded to `MET`
on the harness arm's resolve rate alone. `PARTIAL` is the honest label for
"some of this is decisively true, and some of it has no comparison to check."

</details>

2. Bullet 2 reads MET. What did stage 03 substitute for the arm
   `mission.yaml` actually named, and why does that substitution not
   invalidate the verdict on the tiers that did run?

<details>
<summary>Answer</summary>

`mission.yaml`'s `decision` field named a locally-served open-weights model
compared against a hosted frontier one. Stage 03 substituted three
hosted-subscription tiers of a single CLI instead — a scope decision made
before this report existed. That substitution doesn't invalidate the
cost verdict on the tiers that actually ran because the bullet is answered
honestly on what was measured (haiku/sonnet/opus, real dollar figures per
resolved task), not silently rebranded as an answer to the original
local-vs-hosted question. The report carries the scope note forward instead
of erasing it, which is what keeps "MET" from overclaiming.

</details>

3. Stage 00 has now mined and verified a public task-set companion, and
   bullet 4 moved from `CANNOT DETERMINE` to `MET`. What specific piece of
   evidence would still need to exist for bullet 1's public half to close the
   same way?

<details>
<summary>Answer</summary>

A no-harness control run against the public set — the same `claude_arm.py`
comparison stage 01 already ran against the private set, but pointed at
[`tasks/public.jsonl`](../00-task-set/) instead. Right now only the harness
arm has ever been attempted on the public set (6/6 resolved on `haiku`).
Bullet 4 only required the two sets' resolve rates to be measured and
reported separately, which a single harness run per set can already supply.
Bullet 1 requires an actual comparison — harness vs. no-harness — on *both*
sets, and no amount of additional harness-only attempts on the public set
can produce that; only a real no-harness run against the same public tasks
closes the gap.

</details>

## The fix and its trade

The fix is a report that computes: `report.py` reads only committed
runs/ records and renders a verdict per acceptance bullet, with the
three-way discipline (MET, NOT MET, CANNOT DETERMINE) and PARTIAL where
a bullet decomposes into mixed evidence. The mechanical read is the
point — a report that can soften a number after seeing it is a report
that will.

The trade is that a PARTIAL verdict is a decision cost. Bullet 1 reads
PARTIAL because the public set has no no-harness control: two tiers
decisive (haiku +1.000, sonnet +0.833), opus a no-result inside spread,
and the public half CANNOT DETERMINE — a comparison missing, not failed,
which is narrower than NOT MET and still not a go/no-go. The report also
carries a scope substitution forward rather than erasing it (three
hosted-subscription tiers stood in for the local-vs-hosted arm
mission.yaml named), which keeps MET honest at the price of not
answering the original question. A verdict that names its own gap is the
usable kind; the trade is that it leaves the maintainer's routing
decision to another system — this report establishes the numbers a
router would need, not the router itself.

## Who owns the loop

- **The report/release owner** owns the verdict contract and the
  mechanical script that enforces it — no hand-copied numbers.
- **Each stage owner** owns its runs/ records: the report is only as
  honest as what the stages committed, which is why every dollar and
  wall-clock figure traces to a JSONL line.
- **The maintainer** owns the routing decision the report feeds but does
  not make — the PARTIAL names the gap (a public-set no-harness control),
  and closing it is an execution decision, not a reporting one.

## What this does not prove

**A PARTIAL is not evidence against the mission.** It is evidence that one
specific comparison — harness vs. no-harness on the public task set — has
never been run, discovered by trying to check the contract mechanically
rather than by reading the prose. It does not mean the private-set result is
in doubt, and it does not mean the public set's own harness result (6/6
resolved) is in doubt; it means those two facts cannot yet be combined into
the exact comparison bullet 1 asks for.

**This report is not a routing policy.** `mission.yaml`'s `decision` field
asks which arm to route a task to. Nothing in stages 00-05 builds or measures
an actual router; this mission establishes the resolve-rate/cost/generality
numbers a router would need, not the router itself.

A detour from here: [the PARTIAL, read bullet by
bullet](when-the-partial-verdict/) — the recorded bullet-1 structure: two
tiers decisive, one a no-result inside spread, and the public half
CANNOT DETERMINE because no no-harness control exists there. PARTIAL is
narrower than NOT MET, and it names its own gap.

Another detour: [the 6/6 that says nothing about the 18/18](the-public-set-control/) — the recorded outcome read: private and public resolve numbers are reported side by side, never pooled, because the public set is contamination-prone by design.
