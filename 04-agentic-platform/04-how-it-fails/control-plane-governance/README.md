---
status: verified
level: frontier
base: none
label: Control-plane governance
verified: 2026-08-08
---

# What does a governed agent actually do?

**Question:** an agent that can act is a standing adversary relationship,
not a one-time deployment. Which gates stop the failures that actually
happen, what does each gate cost, and what does the risk-control industry —
the field that has reconciled agents longest — do that an agent harness
should copy?

**The artifact this chapter follows** is the recorded blind arm read as a
governance exercise: every attempt a reconciliation-style verification gate
would have rejected before delivery, what those rejections cost, and what
the gate itself costs when it is the harness's own scoring step:

```text
blind calls a reconciliation gate rejects before delivery:  14/18
cost of the rejected attempts:                              $2.917, 1305s
tampering across 54 real model calls:                       0
regressions across 54 real model calls:                     0
gate cost: blind $1.2859/delivered  vs  harness $0.5066/delivered
```

By the end you will be able to design an approval gate from the failure it
exists to stop, price it, and say which protocol changes in 2026 (MCP,
A2A) are about this layer and which are not.

**Before this:** [the harness-anatomy chapter](../../02-agent-loop/harness-anatomy/), which
separates the control plane from the compute plane, and the risk-control
pattern in the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md).

## The failure mode: an agent that acts without reconciliation

Risk control is where the agentic turn is least forgiving, because the agent
does not recommend an action — it is the action, and the cost of a wrong one
is a real loss. The 2026 risk-control literature converges on one pattern
([surveyed in the paradigm pass](../../../reference/research/agentic-paradigm-restructuring.md)):
schema-constrained output (agents can only emit structured verdicts, free
text is not a decision), rejection and re-query (a non-conforming verdict is
a retry, not a pass-through), a reconciliation owner that holds the final
verdict, named failure modes enumerated before the model decides, and an
assumed adversary (MAFF-Bench shows malicious agents adapting to
mitigations). The same pattern, translated to this mission: the harness
scorer is the reconciliation owner, the diff is schema-constrained, and the
test-tampering guardrail exists because the model is assumed to want the
cheapest path to a green score.

The market prices this failure. Gartner predicts more than 40% of agentic AI
projects will be canceled by end of 2027 — escalating costs, unclear business
value, or inadequate risk controls
([Gartner press release, 2025-06-25](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)).
The rollback record is the operational half: 74% of enterprises have rolled
back or shut down an AI agent after deployment, and agents without automated
evals roll back at 47% versus 9% for agents with full eval coverage
([SoftwareSeni, 2026-06-21](https://www.softwareseni.com/why-most-enterprise-ai-agents-never-reach-production/),
[Forrester 2026 panel, reported 2026-06-01](https://dev.to/milo_antaeus_784320e2f2f9/the-9-rollback-number-what-the-sinch-2026-study-is-actually-telling-you-2h3b)).
The 47-to-9 gap is the empirical version of this chapter's thesis: the
verification step is not overhead, it is what separates a governed agent
from a rolled-back one.

## How you find the case

The recorded blind arm is the ungoverned baseline: 18 attempts, no
verification between the model's claim and delivery. A reconciliation gate —
the scored check the harness already runs — rejects 14/18 before anything
is delivered: 12 `target_still_failing` verdicts plus 2 timeouts. The
rejected attempts cost \$2.917 and 1,305s of wall-clock, which is what the
absence of a gate spends before the failures become visible. The gate's own
price, read as the harness's verification step, is already inside the
harness number: \$0.5066 per delivered outcome against the blind arm's
\$1.2859 — the harness both verifies *and* delivers more per dollar.

The adversarial half of the audit is the record that the guardrail never
fired: zero tampering and zero regressions across 54 real model calls (42
attempts plus 12 retries). Reported honestly — "never fired" is not proof
the guardrail is unneeded, it is evidence these two tasks were tractable
enough that cheating had no efficiency advantage. [Stage 02's scripted
demonstration](../../02-agent-loop/) is where the mechanism was shown firing at
all.

## The gate, designed by reversibility

The organizing principle for where gates sit is reversibility and blast
radius. The repo's own ladder implements it in three steps: read-only tools
auto-allowed and jailed; the one dangerous tool (`run_command`) checked on
its parsed first token with a hard timeout and no network; and a diff that
touches a test file scored as a failure regardless of anything else. The
principle scales up: an action whose damage cannot be reversed, or whose
blast radius is large, earns a human approval gate; an action that a
verification step can undo earns none. The payment rails that make agent
transactions real — Mastercard's AP4M agent tokens and Visa's tokenized
credentials, both announced June 2026
([surveyed in the paradigm pass](../../../reference/research/agentic-paradigm-restructuring.md))
— are precisely the case where blast radius becomes money and the gate stops
being optional.

The 2026 protocol layer is the plumbing for this, and it matters mostly for
what it does not do. MCP's largest update (2026-07-28, under the Linux
Foundation's Agentic AI Foundation) makes the core stateless: requests carry
their own identity, the `initialize` handshake and session ID are gone, and
platform-facing capabilities are centralized
([AAIF, 2026-07-28](https://aaif.io/blog/7-28-hands-mcp-to-platform-teams),
[VentureBeat, 2026-07-27](https://venturebeat.com/orchestration/mcp-just-got-its-biggest-update-ever-heres-what-changes-for-ai-agents)).
Statelessness is a control-plane decision — it moves identity and capability
out of a hidden session so a governance layer can see and gate them. A2A
adds the agent-to-agent half, version 1.0 with signed agent cards (JWS) that
verify who published an agent
([KodeKloud, 2026-07-14](https://kodekloud.com/blog/a2a-vs-mcp-agent-communication-protocols-explained-for-devops/),
[convergence draft, 2026-07-21](https://cloud.tencent.cn/developer/article/2713628)).
What neither protocol does is make an agent trustworthy: a signed card proves
who published the agent, not what it is doing under whose delegation — which
is the reconciliation problem this chapter starts from, unchanged.

## The fix and its trade

The fix is the governance pattern itself: named failure modes, a
reconciliation owner, rejection-and-re-query, and a gate tiered by
reversibility, with the verification step priced like any other component.
The trade is double. First, gates cost latency and friction: every approval
step sits inside the loop's wall-clock budget (mean 86s per harness attempt
here), and a human gate at that cadence is a product decision, not a free
add-on. Second, the gate is only as good as the reconciliation owner: the
repo's scorer is itself the thing being tested by [stage 05's report](../../05-report/),
which mechanically re-checks every acceptance bullet against the recorded
runs rather than trusting the number it is asked to verify. A governed agent
is a loop with a reconciliation owner that is also governed.

## Who owns the loop

- **The harness owner** owns the scorer as reconciliation owner: schema,
  rejection-and-re-query, and the guardrail checks that make "never fired"
  a recorded fact rather than an assumption.
- **The risk/security owner** owns the assumed-adversary stance and the gate
  tiers — which actions are reversible, which carry money, which need a
  human.
- **The platform owner** owns the protocol plumbing: stateless MCP identity,
  A2A cards, and the audit trail that makes a gate decision explainable
  after the fact.

## Check your mental model

1. Why is "the guardrail never fired on a real attempt" a fact, not a
   failure?

<details>
<summary>Answer</summary>

Because the mission's acceptance bullet asks for the guardrail to fire on a
real attempt *or* to be explicitly reported as never having fired — and the
second branch is the honest one here. Zero firings across 54 real model
calls means no tier found deleting an assertion cheaper than fixing the
bug, which is a fact about these two tasks' tractability, not proof the
guardrail is unneeded. A harder task set could flip that; the scripted
demonstration is where the mechanism was shown firing at all.

</details>

2. MCP went stateless in July 2026. What does that change for a governance
   layer?

<details>
<summary>Answer</summary>

It moves identity and capability out of a hidden session into the request
itself, so a control plane can see, log, and gate them. It does not change
the core problem: statelessness and signed agent cards verify *who* is
acting and *that* a call is authorized at the protocol level, not *what* the
agent is doing under delegation — which is exactly the reconciliation this
chapter's gate exists to own.

</details>

## What this does not prove

**The 14/18 rejection rate is the blind arm's ungoverned record, not a
general failure rate.** It is what a gate catches when no verification
exists; the harness arm's 18/18 with the gate in place shows the gate
changing the outcome, not merely detecting it.

**The reversal-rate numbers are external snapshots.** The 74%, 47%, and 9%
figures are 2026 survey and panel records, cited and dated; this mission did
not measure rollback on a live product, and the gate cost here is measured
in this task set's dollars and wall-clock only.

**A gate that never fires is not a gate proven.** The adversarial half of
the record (MAFF-Bench's adapting malicious agents) says the threat is real;
this mission's zero-firing record says these tasks did not exercise it. The
two claims do not contradict, and neither licenses the other's conclusion.

**Next:** [when should the agent act, and when should a human sign
it?](../../03-cheap-or-expensive/what-a-reasonable-agentic-product-is/) — the same gate tiering,
read as a product decision: what to automate, what to gate, and what
evidence decides.
