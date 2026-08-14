---
status: draft
level: reference
label: The delivery pipeline
---

# The PR is the delivery unit, and the pipeline has to hold

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the evidence contract decides what merges. The delivery
pipeline is the machinery that gets an agent's work to the merge point:
branch, CI, review, self-repair. What breaks when the pipeline is the
bottleneck?

## The delivery unit

The PR is the reviewable artifact the authorization matrix gates on — a
diff with passing tests, never a direct push to main. The cloud agents
(Codex Cloud, Jules, Cursor Cloud Agents, Copilot's coding agent) all
converged on the same shape: isolated sandbox, branch, PR for approval
([Tembo's harness comparison](https://www.tembo.io/blog/autonomous-coding-agents)).

## The bottlenecks

**CI speed is a throughput limiter.** An agent can open 10 parallel
branches faster than a 45-minute test suite can validate them. CI speed
is a first-class budget item when agents scale
([code-agent-stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).

**Cross-repo changes are an orchestration problem.** Updating an API and
its client libraries together spans repositories; the pipeline needs an
orchestration layer returning linked PRs, not one-agent-one-repo.

**Self-driving PRs.** When CI fails, an agent can detect the break, repair
it, and keep the branch current — the pipeline that repairs itself is the
delivery version of the ops loop.

## What this means for this topic

The mission's report stage measures delivery (intent-to-delivery); this
chapter is the pipeline the delivery runs on. The stage's demos prove the
gate; the pipeline is where gates scale.

## What this does not say

It does not claim the pipeline removes human review — it removes the
mechanical waiting around it. It maps the machinery and its three
bottlenecks.
