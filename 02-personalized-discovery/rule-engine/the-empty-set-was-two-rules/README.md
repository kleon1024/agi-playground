---
status: verified
level: applied
base: scratch
label: The empty set was two rules
verified: 2026-08-06
---

# A rule engine's failure mode is interaction, not any single rule

**Question:** [stage 07's rule engine](../) applies declarative policy in
priority order. This chapter reads the recorded run and asks what the
engine's sharpest failure looks like.

**Before this:** [stage 07's rule engine](../) and its recorded policy
evaluation.

## The interaction, read

The run ([record](runs/2026-08-06-empty-set-read.md)) reads the recorded
counts:

| policy | result |
|---|---|
| US regional block | removed 10/16, kept 6 |
| cap tightened 2 -> 1 | kept 3, capped 3 |
| EU regional alone | removed 6/16 |
| safety alone | removed 10/16 |
| EU regional + safety | **emptied the set** |

## Two readings

**Each rule alone leaves survivors; the joint application empties the set.**
The EU regional rule alone keeps 10 items, the safety rule alone keeps 6 —
but applied together, no item survives both. That is the interaction a
rule engine must catch: the failure is not any single rule, it is the
intersection of their conditions. A system that tests rules individually
would pass; the empty set is what the joint check exists to find.

**The empty set is a real output, not a crash.** The recorded run treats it
as a measured result of the fixed synthetic candidates — the interaction is
reproducible, which is exactly what makes it a lesson rather than a
heisenbug. The engine's precedence and empty-set check are what turn that
output into a decision (fail, fall back, or return nothing) instead of a
silent blank page.

## The fix and its trade

The fix is a joint-application check plus explicit empty-set semantics: the
engine must distinguish "there were no candidates" from "the policy
intersection removed all candidates" and then choose a declared fallback,
escalate to an operator, or return a transparent unavailable state — never
bypass a safety rule merely to populate a page. The executed read prices
the failure: EU regional alone keeps 10 of 16, safety alone keeps 6, and
applied together they keep zero — a system that tests rules individually
passes, and only the joint check finds the intersection.

The trade, named: the joint check costs a test matrix that grows with the
rule set, and a fallback trades policy strictness for page fill — each
fallback must itself be a policy decision with an owner, because the
default fallback (return nothing) is exactly the silent blank page the
check exists to prevent. The empty set is a real, reproducible output of
this engine, which is what makes it a lesson instead of a heisenbug.

## Who owns the loop

- **The policy owner** owns the rules whose intersection can empty a
  request context.
- **The platform team** owns the joint check, the empty-set decision, and
  the declared fallback for every rule set.
- **The evaluation team** owns the joint test matrix and re-runs it when
  any rule changes — the solo-removal breakdown is the diagnostic that
  turns an empty set into a named cause.

## Evidence boundary

The recorded policy evaluation (fixed synthetic candidates, one
configuration, no real policy data). It reads that artifact; it does not
re-run the engine and the counts are properties of the synthetic set, not
production policy.

## Check your mental model

Answer each before opening it.

**1. Why does the joint application empty a set neither rule alone
empties?**

<details>
<summary>Answer</summary>

Because the rules remove different items. EU regional removes some, safety
removes others, and the survivors of each rule are different subsets — so
applying both removes the union's complement: whatever neither rule
removed is gone when both run. The intersection of the two keep-sets is
empty, which is a property of the rules' conditions interacting, not of
either rule alone.

</details>

**2. Why is reproducibility part of the lesson?**

<details>
<summary>Answer</summary>

Because an intermittent empty set looks like a data problem and gets
"fixed" by retrying. The recorded run fixes the candidates so the
interaction reproduces every time, which is what makes it diagnosable: the
empty set is the engine's honest output under these rules, and the fix is a
policy change (precedence, an exception, or an empty-set fallback), not a
retry.

</details>

## Next

Back to [stage 07](../), or to
[when the rules collide](../when-the-rules-collide/) which reads the same
engine's collision shape.
