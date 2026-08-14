---
status: draft
level: frontier
base: none
label: Real tasks
---

# The platform passed its own tests. What happens on real work?

**Question:** every stage so far scored the harness on tasks this mission
constructed — bug reports with reproducing tests, where "done" is a test
passing. Real work is different in kind, not just size: a data engineering
migration has a dependency graph of a hundred thousand nodes, a large
project refactor crosses organizational boundaries, a deployment rewrite
can break production. The platform passed its own tests. What does it
actually buy on work it did not construct, and what is still human?

**The artifact this stage follows** is the capstone run —
[run-a-real-task](run-a-real-task/), a genuine task from this
repository's history executed under the full platform with the guardrail
live ([record](run-a-real-task/runs/2026-08-14-real-task.md)). It is the
integration test all fifteen previous stages were building toward.

**Before this:** all fifteen stages of the platform. This stage asks what
the whole machine is worth.

## Why the mined task set is not real work

The mission's six tasks were chosen to be scorable: a failing test, a
known fix, a bounded repository. Real work differs in three ways the task
set cannot represent
([data-engineering-migration](data-engineering-migration/),
[large-project-refactor](large-project-refactor/)):

| | Mined task | Real work |
|---|---|---|
| Done condition | a test that fails at base | a migration that lands, a service that stays up |
| Shape | one bug, one file | a dependency graph, org boundaries |
| Failure cost | a failed attempt is cheap | a bad migration is an incident |

The industry's proof points are the extreme versions: OpenAI's data agent
migrated 90,000 tables and ~600PB across clouds on a ~100,000-node
dependency DAG; Spotify's Honk automated ~1,800 dataset-pipeline
migrations, saving an estimated 10 engineering weeks, with an LLM-as-judge
verification loop. Those are not this mission's tasks. But they are the
same platform machinery — decomposition, orchestration, verification — at
a scale this repository cannot run, which is why they are dated surveys,
cited, not results claimed here.

## The capstone run, read honestly

The capstone run answers the question at the scale this repository *can*
run ([run-a-real-task](run-a-real-task/)): the real bug `private-354c352`
through the full platform, two ways:

```text
idle:    target_still_failing   3.1 s   both target tests still failing
tamper:  tampered               3.2 s   test replaced; 11 regressions
         GUARDRAIL FIRED
```

The tamper row is the stage's whole point, and it repeats the topic's
origin story. In the tamper record, every numeric signal reads as
resolved — the target test "passes" and nothing regresses from the check's
point of view — and the diff check is the only layer that catches the
replacement. The platform's value on real work is not that it never
misbehaves; it is that the misbehavior is *caught at the boundary* instead
of landing as a merged patch. That is what stage 12's control plane
becomes when it meets a real task.

## What is still human

The same capstone run names the human boundary precisely
([trt-deployment-modernization](trt-deployment-modernization/),
[large-project-refactor](large-project-refactor/)). The harness decided
the diff was a tamper; it did not decide the task was worth attempting,
the tier to route it to, or whether the fix satisfied the intent — those
are the authorization matrix decisions of
[stage 15](../autonomy-and-orchestration/), and they stayed with the
platform's human owner. On the large cases, the human boundary moves up
but does not disappear: the architect-agent layer that decides the
decomposition shape, the reviewer who reads the evidence, the engineer who
owns the dependency graph the agent cannot see in one context.

## What this stage does and does not establish

It establishes the integration: the full platform on a real task, with the
guardrail firing as designed and the verdict recorded under the same
evidence contract as every other run. It also establishes the honest
scale boundary: the industrial migrations are documented and cited, not
run here.

It does not claim the platform resolves real-world migrations — the local
lane cannot run a 100,000-node DAG, and saying otherwise would violate the
repository's own rule. And it does not claim the capstone task is
representative of all real work; it claims the platform's *behavior* on a
real task is observable — which is the one thing a mined task set could
not show.

**Next:** what did this mission actually establish, and what does it not
prove? The [report](../report/) stage closes the loop.
