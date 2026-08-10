---
status: verified
level: frontier
base: none
label: The agent is the action
verified: 2026-08-08
---

# When is the agent the action?

**Question:** in risk control the agent does not recommend an action — it
*is* the action, and the cost of a wrong one is a real loss. When the loop
this mission built acts, what does reconciliation cost, what does it catch,
and why is the risk-control industry the pattern every other surface should
copy?

**The artifact this chapter follows** is the recorded blind call read as an
un-reconciled action, against the harness read as the reconciled one:

```text
blind calls a reconciliation gate would reject before delivery:  14/18
cost of those undelivered attempts:                              $2.917, 1305s
the same 18 attempts under the harness:                          resolved 18/18
```

By the end you will be able to design the reconciliation step for an agent
that transacts, price it, and say which part of the loop the risk-control
pattern actually owns.

**Before this:** [the control-plane-governance chapter](../control-plane-governance/),
which reads the same arms as a gate exercise, and the risk-control pattern in
the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md).

## The failure mode: the verdict that lands unreconciled

The blind call is what "the agent acts" looks like without a loop: one call,
the issue text, the failing test, a diff applied blind. Of 18 attempts, 12
returned a `target_still_failing` verdict — and eleven of those produced a
diff `git apply` rejected outright, not a wrong fix but a non-applying one
(the recorded taxonomy, [stage 04's read](../../04-how-it-fails/)). A
reconciliation gate — the scored check the harness already runs — would have
rejected 14 of those 18 before anything was delivered, at \$2.917 and 1,305s
of wall-clock. The agent produced a verdict in every case; nothing checked it
before it would have landed.

This is the failure mode the risk-control literature names as the defining
one, because there the agent does not recommend an action, it is the action.
The 2026 pattern is consistent across independent groups
([surveyed in the paradigm pass](../../../reference/research/agentic-paradigm-restructuring.md)):
the [hybrid multi-agent scam-detection system](https://www.mdpi.com/2076-3417/16/7/3122)
(MDPI Applied Sciences, 2026-03-23) decomposes the decision into heuristic,
compliance, and on-chain agents with a **Reconciliator** that owns the final
verdict; [SAGE](https://arxiv.org/abs/2606.08146) (2026-06-05) models the
decision as an LLM-driven walk over a diagnostic tree whose failure cases are
enumerated before the model is asked to decide. Both converge on the same
three mechanisms this mission's harness already implements: schema-constrained
output (free text is not a verdict), rejection and re-query (a non-conforming
output is a retry, not a pass-through), and a reconciliation owner that holds
the final verdict.

## How you find the case

The recorded arms make the gap legible because they separate *produced* from
*reconciled*. The blind arm produced a verdict in every attempt but delivered
only 4/18; the harness arm delivered 18/18 with every failure category other
than `resolved` at 0/18. The per-arm contrast is the case-finding instrument:
the same tasks, the same models, one variable changed — verification inside
the loop — and the delivery rate moves from 4/18 to 18/18.

The risk-control reading sharpens the same fact. In risk control the price of
an unreconciled verdict is not a wasted attempt; it is the action the verdict
authorizes. The gate's own price is already inside the harness number:
\$0.5066 per delivered outcome against the blind call's \$1.2859 — the
reconciled loop both verifies *and* delivers more per dollar. The three
mechanisms map one-to-one onto the mission's loop: the diff is the
schema-constrained output, the scorer's reject-and-retry is the re-query, and
the scorer is the reconciliation owner.

## The fix and its trade

The fix is the reconciliation pattern itself: schema-constrained output,
rejection and re-query, and a reconciliation owner whose verdict gates
delivery. The trade is double, and both halves are measured. First, gates
cost latency and friction: the verification step sits inside the loop's
wall-clock budget (mean 86s per harness attempt here), and a human gate at
that cadence is a product decision, not a free add-on. Second, the gate is
only as good as the reconciliation owner: the repo's scorer is itself the
thing being tested by [stage 05's report](../../05-report/), which re-checks
every acceptance bullet against the recorded runs rather than trusting the
number it is asked to verify. A governed agent is a loop with a reconciliation
owner that is also governed.

The transferable consequence is that the risk-control pattern *is* the
control-plane pattern — the difference is only who sets the guardrails. The
payment rails that make agent transactions real — Mastercard's AP4M agent
tokens and Visa's tokenized credentials, both announced June 2026
([surveyed in the paradigm pass](../../../reference/research/agentic-paradigm-restructuring.md))
— are exactly the case where an unreconciled verdict becomes money, and the
gate stops being optional.

## Who owns the loop

- **The reconciliation owner** owns the final verdict: the scored check that
  rejects 14/18 blind calls before delivery, and the re-query that turns a
  non-conforming output into a retry.
- **The risk/security owner** owns the schema and the rejection rule: what
  counts as a conforming verdict, and which non-conformances are retries
  versus pass-throughs.
- **The platform owner** owns the audit trail that makes a reconciliation
  decision explainable after the fact, which is what a risk owner signs.

## Check your mental model

1. The blind call was handed the exact file the fix belongs in, and still 14
   of 18 attempts would be rejected by a gate that checks the verdict at all.
   What does that make the gate a measurement of?

<details>
<summary>Answer</summary>

It measures the reconciliation step only: given the right location, how often
does a single call produce a verdict that survives a check. It does not
measure whether the agent can find the problem — that step was handed over for
free. The 11-of-12 non-applying finding says the failure is mostly mechanical:
the model miscounted its own diff, not mis-reasoned about the bug. A
reconciliation gate catches exactly that, which is why it rejects 14/18
without touching the substance of any fix.

</details>

2. The harness arm delivers 18/18 at a lower per-delivered cost than the blind
   arm's 4/18. Why is the reconciliation step not overhead?

<details>
<summary>Answer</summary>

Because the blind call's failures still cost money — \$2.917 and 1,305s were
spent on attempts that never delivered. The gate's price is the verification
the harness already runs, and dividing total spend by delivered outcomes puts
the reconciled loop at \$0.5066 against the blind loop's \$1.2859. The same
arithmetic holds in risk control, where the unreconciled verdict's cost is
the action it authorizes, not the attempt that produced it.

</details>

## What this does not prove

**The 14/18 rejection rate is the blind arm's ungoverned record, not a
general failure rate.** It is what a gate catches when no verification exists;
the harness arm's 18/18 with the gate in place shows the gate changing the
outcome, not merely detecting it.

**The external risk-control systems are cited as the pattern, not as
validated production claims.** The MDPI multi-agent system and SAGE are 2026
published results with their own evaluation boundaries; this mission did not
run them, and the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
states which claims it could check.

**A gate is not a risk policy.** The reconciliation step prices the check; it
does not decide what risk the platform accepts, which tiers need a human, or
what the blast radius of an authorized action is. Those are the next chapter's
subject.

**Next:** [what does the adversary that adapts change?](../the-adversary-that-adapts/)
— the same loop, read from the other side: when the agent is assumed to be
fighting the gate, what evidence does the guardrail actually have?
