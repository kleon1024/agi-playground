---
status: draft
level: reference
label: AI code quality deficit
---

# The quantified defect record, read against this mission's runs

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage's verified core measures this mission's failures.
The industry has a quantified record of AI-generated code's quality
deficit. Reading the two side by side is the stage's strongest evidence
that the verification stack is not optional.

## The industry record

GitClear and GitKraken analyzed 623M real-world code changes (2023–2026):
AI-assisted commits are ~25% of all commits, duplication is up ~81%, code
reuse down ~70%, legacy refactoring down ~74%, and error masking up ~47%
([LeadDev report](https://leaddev.com/ai/code-maintainability-plummets-in-the-ai-coding-era)).
Google's DORA adds: each 25% of additional AI usage adds ~7% instability
([DORA](https://dora.dev/ai/gen-ai-report/report/)).

## The mission's mirror

The mission measured the same deficit at mechanism scale: resolve rate
18/18 while the cheap tier's patches diverged 1.2e-3 to 4.2e-2 from a
correct-patch baseline — three orders of magnitude off, invisible to the
primary metric. The patch-generality check exists because of it, exactly
as the industry's review gates exist because of the measured deficit.

## What the two records agree on

The failure is not that AI code fails tests — it is that code satisfies
the tests while missing the wider correctness bar. Both records say the
verification layer (generality checks, review, error-masking audits) is
the response, not the model.

## What this does not say

It does not claim the deficit is permanent — 2026 data shows trends
flattening. It claims the deficit is real and the verification stack is
its mechanism-scale answer.
