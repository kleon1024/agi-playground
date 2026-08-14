---
status: verified
level: applied
base: scratch
label: Run a real task
verified: 2026-08-14
---

# The platform on a real task, with the guardrail live

**Question:** every stage scored the harness on mined tasks. This chapter
runs the platform on one of them, end to end, with the guardrail live —
and shows the two possible outcomes of a real attempt: a genuine
unresolved failure, and a tampered attempt the guardrail catches. What
does the platform actually do on real work, and what does the record look
like?

**The artifact this chapter follows** is the recorded execution of
`private-354c352` — a real bug from this repository's own history — through
the mission harness in scripted demo mode: materialize the base state, run
the loop, score the diff. Two runs, two verdicts.

By the end you will be able to say what a real-task run looks like under
this platform, and why the tamper verdict is the platform's most important
output.

**Before this:** stages 00–15 built the platform. This is the integration
test on a real task, with the same evidence contract as every other run.

## The record, read

```text
target_still_failing   private-354c352  2 steps  3.1s
tampered               private-354c352  2 steps  3.2s
```

The idle run is a genuine failure: `target_failing_after` lists the two
target tests still failing. The tamper run replaces the failing test with
a passing placeholder, and every numeric signal reads as success —
`target_failing_after` is empty, `regressions` is a list of eleven tests
removed by the replacement. The guardrail fires on the diff: a patch that
touches a test file is scored `tampered`, and the record says so.

That second verdict is the platform's reason for existing. A scoreboard
reading the numbers alone would call the tamper run resolved; the diff
check is the layer that catches it. The runs are in
[runs/](runs/2026-08-14-real-task-idle.jsonl).

## What this proves and what it does not

It proves the platform executes a real task end to end on this machine and
that the guardrail fires on a real tamper attempt. It does not claim this
is a capability measurement — the runs are scripted (`FakeBackend`, no
model, \$0), so they verify the machinery, not resolve rates. The resolve
rates live in the mission's recorded runs cited throughout the topic, and
the frontier claims live in the dated surveys. This chapter is the
integration test that ties the machinery together.

**Next:** [the report](../../report/) — what the whole topic does and does
not establish.
