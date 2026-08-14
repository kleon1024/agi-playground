---
status: verified
level: applied
verified: 2026-08-01
label: Verification and evals
---

# The agent says it fixed the bug. What would change your mind?

**Question:** stage 03's full-harness attempts resolved every task, every
tier. Does that mean this stage's guardrails have nothing to show, or does
it mean they have not yet been asked a hard enough question? And once the
answer is "the harness resolved it", how do you know it did not cheat, and
how do you know it will still resolve on work you did not construct?

**The artifact this stage follows** is the verification stack: the
taxonomy that reads every real attempt, the guardrail that detects test
tampering, the judge that scores agent output, and the evidence contract a
merge decision runs on. The recorded table the stage opens with is built
from every real model attempt this mission has produced — no new attempts,
no new model calls, only a category read off records that already exist:

```text
                        harness (18)   no-harness (18)
resolved                18/18          4/18
target_still_failing     0/18          12/18
guardrail fired          0/18          0/18
```

By the end you will be able to read any production verification setup —
Cursor's evidence contract, an LLM-as-judge pipeline, a CI gate, an eval
suite — as the same three layers: score the outcome, detect the cheat,
bound the claim. And you will be able to say what each layer's zero does
and does not prove.

**Before this:** [stage 03](../agent-loop/) built the harness and its
scorer. This stage is what the scorer has to survive.

## What this stage decides

What counts as done. The stage's decision is the evidence contract: which
signals (tests, guards, judges, traces) must be present before a patch is
accepted, and which claims the evidence does not support. The industry's
2026 version of this decision is a merge policy — collect evidence, score
risk, route the change to auto-merge or a human reviewer.

## The verified core (recorded runs)

- **control-plane-governance** — what a governed agent actually does: the
  policy layer read off the mission's own runs, with the governance-gates
  run (2026-08-08).
- **the-adversary-that-adapts** — an adversarial arm that changes strategy
  mid-run, and what adaptivity does to the guardrail's hit rate
  (2026-08-08).
- **the-agent-is-the-action** — when the agent itself is the action, and
  the risk-agent read of the recorded attempts (2026-08-08).
- **the-zero-failure-taxonomy** — the recorded catalogue read: the harness
  arm is 0/18 in every failure category; the no-harness arm is where
  failures live (12/18 target_still_failing) (2026-08-06).
- **when-the-patch-cannot-apply** — the same logs, second cut: 11 of 12
  no-harness failures never produced an applicable patch, and the harness
  is cheaper per resolved task than the blind call (2026-08-06).

## The frontier extensions (dated surveys)

- **ai-code-quality-deficit** — the industry's quantified defect data
  (GitClear's 623M-change analysis: duplication up ~81%, reuse down ~70%,
  error masking up ~47%; DORA's instability finding) read against the
  mission's own recorded quality signals.
- **the-evidence-contract** — behavioral artifacts as units of trust
  (Cursor's demo-as-evidence), CI and security checks, risk scoring, and
  the four-phase SDLC (plan, human review, implement + demo, ship +
  retrospective).
- **the-delivery-pipeline** — the PR as the delivery unit: approval gates,
  self-driving PRs (agent repairs its own CI), and cross-repo orchestration
  as an engineering problem rather than a model problem.
- **llm-as-judge-reliability** — when a judge can be trusted: RuVerBench,
  gaming the judge, and Spotify Honk's LLM-as-judge verification loop.
- **[static-vs-live-eval](static-vs-live-eval/)** — the benchmark honesty gap: SWE-bench Verified
  at 43.20% for state-of-the-art systems versus SWE-bench-Live at 19.25%,
  and why a live task set changes what a score means.
- **a-minimal-judge** (local mechanism demo) — a rule-based verifier versus
  an LLM judge replayed over the mission's recorded runs, recording where
  they agree and where the judge is fooled.

## Evidence strategy

The verified core inherits the mission's recorded runs unchanged. The
frontier extensions are dated surveys with attributed numbers, plus one
local run (`a-minimal-judge`) that replays existing records without new
model spend. The stage's honesty contract is the one the mission was built
on: an empty failure row answers "did this harness fail here" and cannot
answer "can this harness fail".

## What this does not prove

**The zero-failure record is a property of this task set, not a general
claim about frontier coding agents.** Two tasks, three tiers, three runs —
a larger or more adversarial set could surface harness failures this one
did not.

**Never firing is not evidence the guardrail is unneeded.** It is evidence
that, on these two tasks, no tier found deleting an assertion cheaper than
fixing the bug.

**Next:** [stage 16](../industry-impact/) asks whether any of this
transfers to industries whose outcomes are harder to score, and
[stage 17](../real-tasks/) runs the platform on a real task from this
repository's own history.
