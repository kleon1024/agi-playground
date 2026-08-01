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
1. beats no-harness beyond spread, both sets   -> CANNOT DETERMINE
2. beats always-frontier on $/resolved          -> MET
3. guardrails hold, tampering fired-or-honest   -> MET
4. public/private reported separately           -> CANNOT DETERMINE
5. latency and dollars, real and in budget       -> MET
6. failures catalogued by category              -> MET
7. every number traces to runs/                 -> MET
```

By the end you will be able to say why two bullets read `CANNOT DETERMINE`
rather than `NOT MET`, and why both trace to the same root cause.

**Before this:** every other stage in this mission.
[`core/report.py`](core/report.py) reads
[stage 00](../00-task-set/)'s manifests and
[stage 01](../01-no-harness/)/[stage 03](../03-cheap-or-expensive/)'s `runs/`
JSONL directly; nothing here is hand-copied.

## Why two bullets say CANNOT DETERMINE, not NOT MET

Bullets 1 and 4 both ask for the public and private task sets, reported
separately. [Stage 00](../00-task-set/) mined and verified only a private set
— two tasks pulled from this repository's own git history. No public
benchmark subset was ever admitted alongside it. There is nothing to report
separately from, and nothing has been pooled, because there is only one set.
That is a real, pre-existing gap in this mission's own foundation, not a
defect in stages 01, 04, or 05 — stage 00 was out of scope for this build and
was read, not edited. `report.py` says so plainly rather than silently
evaluating the bullet against the one set that exists and calling it MET.

Per-tier, on the set that does exist: the harness beats no-harness decisively
at `haiku` and `sonnet`, and produces a genuine no-result at `opus` (the
margin sits inside that arm's own run-to-run spread at N=2 tasks). Full numbers
in [stage 01](../01-no-harness/).

## What the other five bullets say

**Bullet 2 (cost) is MET**, with a scope note carried forward rather than
erased: `mission.yaml`'s `decision` field names a locally-served open-weights
model against a hosted frontier one. Stage 03 ran three hosted-subscription
tiers of a single CLI instead — a scope decision made before this report
existed. The bullet is answered honestly on the tiers that actually ran, which
is not the same claim as answering it on the tiers `mission.yaml` originally
named.

**Bullet 3 (guardrails) is MET.** Zero regressions across 36 real attempts.
Zero real test-tampering firings — reported as "never fired," per the
mission's own explicit-or-fired branch, with the scripted stage 02
demonstration cited but not counted as a real one.

**Bullets 5, 6, 7 are MET** on their own terms: every dollar and wall-clock
figure traces to a `runs/` JSONL line, [stage 04](../04-how-it-fails/)
catalogues every real failure by category, and this script is the mechanism
that makes bullet 7 true of itself.

## Check your mental model

1. Why does a missing public task set make bullets 1 and 4 undecidable rather
   than failed?
2. Bullet 2 reads MET. What did stage 03 substitute for the arm
   `mission.yaml` actually named, and why does that substitution not
   invalidate the verdict on the tiers that did run?
3. If stage 00 later mines and verifies a public task-set companion, what
   changes about how this script needs to be rewritten to re-evaluate bullets 1
   and 4?

## What this does not prove

**A CANNOT DETERMINE is not evidence against the mission.** It is evidence
that stage 00's task set was never built to the scope `mission.yaml` declared,
discovered by trying to check the contract mechanically rather than by
reading the prose.

**This report is not a routing policy.** `mission.yaml`'s `decision` field
asks which arm to route a task to. Nothing in stages 00-05 builds or measures
an actual router; this mission establishes the resolve-rate/cost/generality
numbers a router would need, not the router itself.
