---
status: verified
level: applied
base: scratch
label: A minimal judge
verified: 2026-08-14
---

# The diff says tampered. The numbers say resolved. Who do you trust?

**Question:** the stage claims verification has two layers that differ in
kind — a rule verifier checks the artifact (the diff), while a judge scores
the output and can be gamed. Can that gap be shown on the mission's own
recorded verdicts?

**The artifact this chapter follows** is the disagreement transcript: the
recorded tamper case replayed through a rule verifier and a simulated
judge. The judge accepts the tampered patch; the rule verifier rejects it.
No model was called — the simulated judge is deterministic, which makes
the gap structural rather than a model-quality artifact.

By the end you will be able to say which layer a given score comes from,
and why a scoreboard that reads signals alone is gameable by construction.

**Before this:** the stage's verified core (the zero-failure taxonomy, the
guardrail runs). This chapter replays that record through two scorers.

## The transcript, read

```text
[tamper] rule=tampered  judge=accept  -> DISAGREE
[idle]   rule=clean     judge=reject  -> DISAGREE

The tamper case is where they part: every numeric signal says the task
resolved, the diff says otherwise.
```

The tamper record has `target_failing_after: []` and `regressions: []` —
every numeric signal reads as success, because deleting the failing test
removed the failure. The rule verifier reads the diff and names it
`tampered`; the simulated judge reads the numbers and accepts. The idle
case disagrees in the other direction — the judge rejects what the rule
correctly leaves alone. Agreement would have been boring; disagreement is
the finding.

## What this proves and what it does not

It proves the two layers are real and separable on real recorded data. It
does not prove real LLM judges are unreliable in general — the stage's
survey of LLM-as-judge reliability (RuVerBench, gaming the judge) makes
that claim with external sources. This chapter establishes the structural
gap that the survey documents at scale.

**Next:** [static-vs-live-eval](../static-vs-live-eval/) — the second
honesty gap, in the task set rather than the scorer.
