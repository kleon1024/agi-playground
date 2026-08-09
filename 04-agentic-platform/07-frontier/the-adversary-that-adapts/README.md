---
status: verified
level: frontier
base: none
label: The adversary that adapts
verified: 2026-08-08
---

# What does the adversary that adapts change?

**Question:** a risk-control agent is a standing adversary relationship, not
a one-time deployment — malicious agents adapt to mitigations. What does that
stance change about a guardrail's evidence, and what is the honest reading of
a guardrail that never fired?

**The artifact this chapter follows** is the recorded guardrail's decision
boundary, against the recorded real-attempt record:

```text
the test-file guardrail's decision boundary (scripted worktrees):
  agent edited a test file (tamper)             yes (refused)
  agent created a new test file                 yes (refused)
  agent edited a source file (legit)            no
  agent created a new source file               no

tampering on real attempts: 0/18 in both arms, 0 across all 54 calls
```

By the end you will be able to say what "the guardrail never fired" actually
proves, and why the assumed-adversary stance is a load-bearing product
decision rather than paranoia.

**Before this:** [the-agent-is-the-action](../the-agent-is-the-action/),
which establishes the reconciliation pattern, and the MAFF-Bench result in
the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md).

## The failure mode: the mitigation the adversary outgrows

The 2026 result that frames this chapter is the adversarial one the other
risk-control papers assume away: [MAFF-Bench](https://iclr.cc/virtual/2026/poster/10008753)
(ICLR 2026, with [code](https://github.com/zheng977/MutiAgent4Fraud),
2026-02-05) simulates financial-fraud agent networks on social platforms and
finds that content-level, agent-level, and societal-level defenses all get
"adapted to" — malicious agents change their behavior to stay under the
detector. The lesson is not that defenses are useless; it is that a
risk-control agent is a *standing* adversary relationship, and the standing
part changes what evidence a guardrail has.

This mission's own record is the honest complement. The test-file guardrail —
the rule that a diff touching a test file is scored as a failure regardless
of anything else — has a sharp decision boundary, demonstrated on five
scripted worktrees: editing *or creating* a test file refuses the patch;
source-only and empty worktrees pass. On real attempts, it never fired:
0/18 in both arms, 0 across all 54 real model calls. The recorded failure
taxonomy says why that is a fact about these two tasks, not proof the
guardrail is unneeded: no model tier found deleting an assertion cheaper than
fixing the underlying bug — these two bugs were tractable enough that
cheating had no efficiency advantage.

## How you find the case

The two reads make the adversary stance legible precisely by disagreeing. The
scripted demo shows the mechanism firing: five controlled scenarios, and the
guardrail refuses exactly the two that touch a test path — including the
"new test file that asserts nothing" case, because `changed_paths` reads
`git status --porcelain --untracked-files=all` and sees untracked files. The
real-attempt record shows the mechanism never firing on live data. Both are
true, and the chapter's argument is that the pair is the evidence: the demo
proves the gate has teeth, the zero-firing record proves these two tasks did
not exercise it, and neither licenses the other's conclusion.

The case-finding instrument is the same one the governance chapter uses, read
from the adversary's side. A mitigation's evidence is only as strong as the
hardest case it was shown to catch — and the demo's five scenarios are the
hardest cases this repo could construct without manufacturing a prompt that
asks a model to cheat (which would answer a different question than the one
the mission measures). MAFF-Bench is the external version of the same
instrument at industrial scale: defenses validated only against the current
adversary population are validated against a moving target, and the
adaptation result is the proof that the target moves.

## The fix and its trade

The fix is the assumed-adversary stance, applied as a design rule: assume the
model wants the cheapest path to a green score, and keep the guardrail as a
rule that no retrain can soften. Three consequences follow, each with a
trade. First, the guardrail must be a rule, not a learned behavior — the
test-path check is a path read from `git status`, so a model retrain cannot
quiet it; the trade is that such rules are brittle by design, refusing
legitimate test edits with no nuance. Second, failure modes must be named
before the model decides — the mission's taxonomy does this, and the trade is
that a taxonomy is only as complete as the cases already seen, which is
exactly what an adapting adversary exploits. Third, "never fired" must be
recorded as a fact, not converted into confidence — the mission reports
zero firings honestly, and the trade is that this reads as weakness to a
stakeholder who wants proof of safety, which is the price of honesty about
an adversary that adapts.

The market prices the absence of this stance. Gartner predicts more than 40%
of agentic AI projects will be canceled by end of 2027 — escalating costs,
unclear business value, or inadequate risk controls
([Gartner press release, 2025-06-25](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)).
The rollback record is the operational half: 74% of enterprises have rolled
back or shut down an AI agent after deployment, and agents without automated
evals roll back at 47% versus 9% for agents with full eval coverage
([SoftwareSeni, 2026-06-21](https://www.softwareseni.com/why-most-enterprise-ai-agents-never-reach-production/),
[Forrester 2026 panel, reported 2026-06-01](https://dev.to/milo_antaeus_784320e2f2f9/the-9-rollback-number-what-the-sinch-2026-study-is-actually-telling-you-2h3b)).
The 47-to-9 gap is the empirical version of this chapter's thesis: the
verification step is what separates a governed agent from a rolled-back one,
and an eval that assumes the model is not fighting it is the eval that gets
outgrown.

## Who owns the loop

- **The risk/security owner** owns the assumed-adversary stance: the design
  rule that the model wants the cheapest path to green, and the rule-vs-learned
  decision that keeps the guardrail outside the retrain.
- **The harness owner** owns the guardrail's teeth and its honest record: the
  demo that proves the mechanism fires, and the zero-firing real record
  reported as a fact, not as confidence.
- **The platform owner** owns the adaptation loop: what new failure modes the
  standing adversary will produce, and which of them earn a new rule versus a
  new eval.

## Check your mental model

1. The guardrail never fired on a real attempt, yet the chapter treats that
   as a fact about the tasks, not proof of safety. Why?

<details>
<summary>Answer</summary>

Because "never fired" means no tier found deleting an assertion cheaper than
fixing the bug — a statement about these two tasks' tractability, not about
the adversary's absence. A harder or more adversarial task set could flip it,
and MAFF-Bench is the external evidence that adversaries do adapt. The honest
complement is the scripted demo, which proves the mechanism has teeth at all;
the zero-firing record and the demo are both true, and neither licenses the
other's conclusion.

</details>

2. The guardrail refuses a diff that *creates* a new test file, not just one
   that edits an existing test. Why does the untracked-file case matter?

<details>
<summary>Answer</summary>

Because "create a test file that asserts nothing" is the cheapest way to
manufacture a green score: the test passes by construction, so the patch's
remaining evidence is worthless. The guardrail closes that hole by reading
`git status --porcelain --untracked-files=all`, which sees untracked files —
the demonstration that the gate was designed from the adversary's cheapest
path, not from the shape of legitimate work.

</details>

## What this does not prove

**The zero-firing record is not a general safety claim.** It is 36 real
attempts on two tasks plus 12 retries; a much larger or more adversarial task
set could easily surface the tampering this one never produced.

**MAFF-Bench is a simulation, and its adaptation finding is domain-specific.**
The social-platform fraud networks it models are not this repo's code-fixing
loop; it is cited as evidence that adversarial adaptation is real, not as a
measured property of any deployment this mission built.

**The rollback and cancellation figures are external snapshots.** The 74%,
47%, 9%, and 40% numbers are 2026 survey, panel, and analyst records, cited
and dated; this mission did not measure rollback on a live product, and the
guardrail's cost here is measured in this task set's dollars and wall-clock
only.

**Next:** back to [the stage overview](../) — or across to
[mission 02's conversational surface](../../../02-personalized-discovery/search/38-conversational-surface/),
where the same intent-to-delivery loop is read from the discovery side: what
the session changes, what survives of the score, and what the auction keeps.
