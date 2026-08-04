---
status: draft
level: applied
base: none
label: Who decides to ship
---

# The report is in. What has to be true before it ships?

[Stage 07](../) produced three reports: perplexity 21.677, a task suite at
0.625 of 8 log-likelihood, and an agent report of 0 out of 6. Suppose those
numbers had been good. Nothing in them tells you whether the candidate ships,
because a score is one input to a release decision and the decision has other
inputs — which failures have an owner, which guardrails are enforceable at all,
and what happens when the check itself is broken.

This chapter is that decision. [Eval gates](../eval-gates/) already measures the
*automated* half — a threshold computed the same way every time. What follows is
the half a script cannot own.

**Before this:** [why should anyone believe the report?](../why-believe-the-number/),
for contamination, judge bias, and noise. A release decision built on a number
you have not interrogated is a formality, not a gate.

## A score is a release signal; a failure is an assignment

Aggregate scores tell you whether to ship. They do not tell anyone what to fix.
That takes a taxonomy whose categories map to an owner, so that a failure
arrives at the team that can act on it:

| Failure | Likely owner |
|---|---|
| wrong knowledge or reasoning | model, data, or retrieval |
| correct plan, malformed tool call | harness schema or model |
| correct action, stale observation | environment or tool |
| timeout after repeated work | loop policy or serving |
| successful outcome, forbidden action | permission policy |
| inconsistent result across seeds | sampling or environment variance |

Read row five carefully. **A task the system completed by taking a forbidden
action is a failure**, and an outcome-only score records it as a success — which
is why policy adherence has to be scored beside the outcome rather than after
it.

Store representative traces with each classification. A distribution of failure
categories with no example attached tells an engineer which bucket is largest
and nothing about what to change.

## Five conditions, not one number

A candidate ships only if all of these hold:

1. the primary outcome clears a bar declared **before** the run;
2. every hard guardrail is within limit;
3. no important slice hides a material regression behind the average;
4. latency and cost fit the service budget;
5. every failure has an owner and an accepted residual risk.

When the result is mixed, the useful output is not "run more tests" — it is
naming the slice, the sample size, or the failure mechanism whose resolution
would change the decision. That converts an argument into a measurement, and it
is the same discipline a mission's `mission.yaml` applies by declaring its
acceptance bar before any code exists.

## A guardrail you cannot compute is a wish

"Do not harm quality" cannot block anything. An enforceable guardrail names a
population, a metric, a direction, a tolerance, and a decision:

```text
For new users in each launch market,
report rate must not exceed the agreed baseline limit.
If it does, stop expansion and roll back the treatment.
```

Every one of them needs a numerator and denominator, an event and attribution
window, the slices where the rule applies, its behavior when data is missing, a
warning threshold separate from the hard stop, and a named owner. If two teams
compute the same guardrail differently, it is not yet a shared boundary — it is
two boundaries with one name.

## Enforce where the harm can still be prevented

Measurement after the fact is not enforcement. The control belongs at the
subsystem that still has the ability to say no:

| Risk | Enforcement point |
|---|---|
| forbidden tool call | harness permission check |
| private field enters training | data access and export policy |
| latency exceeds service budget | admission and rollout gate |
| unsafe model version ships | release gate |

This is the same argument [what stops it?](../../06-agent/what-stops-it/) makes
inside the agent loop, one level up: a downstream dashboard cannot compensate
for an upstream system that still permits the action.

The companion rule is to grant only the data, tools, duration, and population
the current job requires — keeping identity separate from product enrollment,
possession separate from permitted use, read access separate from action
authority, and experiment exposure separate from full launch. A smaller blast
radius does not make a defect acceptable. It preserves the option to recover
from one.

## What the record has to carry

For every high-impact decision, keep enough to reconstruct it afterwards:

```text
who or what initiated it
which policy and model version applied
which input evidence was used
which action occurred
which guardrails were evaluated
what result and override followed
```

Provenance is itself subject to retention and access policy — do not log
secrets or unrestricted personal data to make an audit trail feel complete.

The same logic governs the data underneath: "the company has this data" is not
evidence that this product may use it. Purpose, consent basis, retention,
geography, access group, and deletion path are properties of the *use*, not the
storage, and derived features inherit their source's restrictions whenever they
can still identify or materially affect a person. Once source scope is lost,
later filtering cannot reconstruct whether the use was ever permitted — which
is why [the corpus record](../../00-corpus/what-a-release-needs/) has to carry
provenance through every transformation rather than only at the end.

## Test the path that blocks, not just the path that passes

Before launch, exercise the failure modes of the enforcement system itself: a
guardrail breach, missing or delayed telemetry, the policy service being
unavailable, a rollback, a human override, and an audit reconstruction. A
policy that works only when every dependency is healthy is not a boundary.
Decide fail-open versus fail-closed explicitly, per risk, and write the choice
down.

When a breach does reach a human, escalation is a decision being requested, not
a meeting being scheduled. The packet carries the breached condition, the
affected population and duration, the current containment, the evidence quality
and its unknowns, the options with their residual risk, and the named decision
required. Escalation moves a decision whose authority exceeds the current team;
it does not move ownership of the analysis.

## What this chapter does not establish

None of it is measured. This repository has one release decision to point at —
mission 01's 0-of-6 agent report — and the correct call there was obvious
without any of this apparatus. No guardrail was breached, no escalation was
raised, no rollback was exercised, and no failure taxonomy was applied to a real
incident. [Eval gates](../eval-gates/) and [red-teaming](../red-teaming/) are the
two pieces here that *do* have runs behind them, and both measure the automated
threshold rather than the decision around it. Treat this chapter as the shape of
the decision, and the two run-backed chapters as the only part of it this
repository can show you working.

## Check your mental model

1. An agent completes 6 of 6 tasks, and the transcript shows it deleted a file
   it had no permission to touch. What is the score, and where does the fix go?

<details>
<summary>Answer</summary>

The task score is 6 of 6 and the release decision is a failure — row five of the
taxonomy, "successful outcome, forbidden action". An outcome-only metric records
this as the best possible result, which is exactly why policy adherence is
scored beside the outcome rather than inferred from it. The fix does not go to
the model: it goes to the permission policy, because the harness allowed an
action it should have refused. A better-behaved model would hide the defect
rather than remove it.

</details>

2. Your guardrail says "report rate must not regress". Why can that not block a
   release?

<details>
<summary>Answer</summary>

Because nothing in it is computable without further decisions that nobody has
made: what the numerator and denominator are, over what attribution window,
against which baseline, on which slices, what happens when the data is late or
missing, and how large a move counts. Two teams will implement it two ways and
both will believe they enforced the same rule. An enforceable version names the
population, the metric, the direction, the tolerance, the missing-data
behavior, and the decision that follows a breach — at which point it can block
something.

</details>

3. Why does testing the failure path matter more than testing the passing path?

<details>
<summary>Answer</summary>

Because the passing path gets exercised on every ordinary run, and the failure
path only gets exercised when something has already gone wrong — which is the
worst moment to discover that the policy service is down, the guardrail was
computed on stale telemetry, or the rollback was never tried on this version. A
control that has only ever been observed succeeding is an untested control. The
specific thing to decide in advance is fail-open versus fail-closed for each
risk: when the check itself cannot run, does the action proceed or stop? That
answer is a policy, and silence on it defaults to whichever the code happened
to do.

</details>

## Next

[Eval gates](../eval-gates/) is the automated half of this decision with a run
behind it, and [red-teaming](../red-teaming/) is where the cases that make a
gate meaningful come from. To close the mission, return to
[the evaluation stage](../) for what the three reports do and do not license
you to claim.
