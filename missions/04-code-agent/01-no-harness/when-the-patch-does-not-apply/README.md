---
status: verified
level: applied
base: scratch
label: When the patch does not apply
verified: 2026-08-06
---

# The first gate a blind call must pass

**Question:** [stage 01's no-harness baseline](../) applies each blind
call's diff with plain git apply, no retry. This chapter reads the recorded
matrix and asks what the apply gate actually decides.

**Before this:** [stage 01's no-harness baseline](../) and its recorded
JSONL.

## The gate, read

The run ([record](runs/2026-08-06-apply-read.md)) reads the recorded
matrix:

| tier | diffs applied | resolved |
|---|---:|---:|
| haiku | 1/6 | 0/6 |
| sonnet | 1/6 | 1/6 |
| opus | 3/6 | 3/6 |

## Two readings

**Application is the first gate, and with no retry it is final.** A diff
that git apply rejects resolves nothing — the model never gets a second
chance to repair it. Applied and resolved coincide almost exactly (sonnet
1/1, opus 3/3), which is the sharpest evidence: the blind call's failure is
most often at the apply step, before the patch's correctness is even
tested.

**Haiku's one applied diff that still failed is the second gate.** Haiku
applied 1/6 but resolved 0/6 — the diff applied and the target test still
failed. Two gates, not one: the patch must apply AND make the test pass,
and the record keeps both columns because either can fail independently.

## Evidence boundary

The recorded no-harness JSONL (18 attempts, 2 private tasks x 3 tiers x 3
seeds, one declared 240s cap). It reads that artifact; it does not re-call
any model.

## Check your mental model

Answer each before opening it.

**1. Why is "applied" a separate number from "resolved"?**

<details>
<summary>Answer</summary>

Because a diff can fail at either stage. git apply can reject a malformed
or wrong-context patch before any test runs; or the patch can apply cleanly
and still leave the target test failing. The record keeps both columns so
the failure is attributable — a model that "resolved nothing" could have
failed to apply, or applied and been wrong, and the two fixes are
different.

</details>

**2. What does the apply gate say about the no-retry design?**

<details>
<summary>Answer</summary>

That the baseline is deliberately harsh: one blind call, and a rejected
diff is a terminal failure. That is the control's purpose — it isolates
what a single call can do without a loop. The later stages (guardrail,
retry) exist precisely because this gate is final here, and their measured
value is the resolve rate they add over this floor.

</details>

## Next

Back to [stage 01](../), or to
[the blind call, read per tier](../when-the-blind-call-fails/) which reads
the same matrix's cost side.
