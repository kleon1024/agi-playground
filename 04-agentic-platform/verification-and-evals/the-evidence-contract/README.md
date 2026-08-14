---
status: draft
level: reference
label: The evidence contract
---

# Behavioral evidence, risk scoring, and the merge policy

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage's decision is "what counts as done". The
industry's most complete answer is Cursor's evidence contract: collect
evidence, score risk, route the change to auto-merge or a human. What are
the pieces, and how does the contract read?

## The pieces

**Behavioral artifacts** — an agent that exercises the change and returns
evidence (a test run, a screenshot, a screen recording of the feature)
makes the diff reviewable before the diff is parsed. Cursor treats the
recording as "one of the turning points" in trusting agents
([Arize write-up](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)).

**CI and security checks** — the baseline evidence every change must pass.

**Risk scoring** — scores route human attention: low-risk complete-evidence
changes follow an automated path; high-risk changes summon the owner.

**The policy** — in sketch form:

```text
evidence = collect(ci, security_review, demo_artifact)
risk = score_change(pr, evidence)
if evidence.passed and risk <= auto_merge_threshold: merge(pr)
else: request_review(pr, owner=route_by_change(pr))
```

## The tuning parameters

Escaped defects, rollback frequency, human overrides, and time-to-merge
reveal whether the auto-merge threshold is too permissive or too cautious.
The contract is an operating parameter, not a constant.

## What this means for this topic

The mission's evidence contract is the same shape at mechanism scale: the
diff check (CI), the patch-generality probe (risk score), and the
resolve-rate pair (the merge decision). This chapter is the industry
version the stage's demos implement in miniature.

## What this does not say

It does not claim video evidence replaces tests — it covers an exercised
path, while tests and static checks carry the wider state space. It maps
the contract's pieces and their interactions.
