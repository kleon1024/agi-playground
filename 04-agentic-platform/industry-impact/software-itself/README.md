---
status: draft
level: reference
label: Software itself
---

# The industry the platform came from, measured

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** before asking whether agents transfer to other industries,
measure what they did to the industry they came from. The GitClear/GitKraken
analysis of 623M real-world code changes (2023–2026) is the largest public
data set on AI-assisted software. What does it show?

## The measured deficit

AI-assisted commits are ~25% of all commits. Compared to pre-AI baselines:

| Signal | Change |
|---|---:|
| code duplication | up ~81% |
| code reuse (refactored edits) | down ~70% |
| legacy refactoring | down ~74% |
| error masking (obfuscation) | up ~47% |
| functional connectivity | down ~35% |

Source: [GitClear/LeadDev report](https://leaddev.com/ai/code-maintainability-plummets-in-the-ai-coding-era).

DORA adds the instability signal: each 25% of additional AI usage adds
~7% instability ([DORA research](https://dora.dev/ai/gen-ai-report/report/)).

## What the deficit means

The deficit is not "AI writes bad code" — it is "AI writes code that
satisfies the prompt and the tests, and both are narrower than the
maintainability bar". This is the exact failure the mission's
patch-generality check caught: resolve rate 18/18 while the cheap tier's
patches hid latent defects. The authorization matrix and verification
stack are the industry's response, and this topic is their mechanism-scale
instance.

## What this does not say

It does not claim the deficit is permanent — 2026 data shows the trends
flattening. It establishes the quantified baseline the platform stages are
the answer to.
