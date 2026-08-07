---
status: verified
level: applied
base: scratch
label: When the verdict is partial
verified: 2026-08-06
---

# The PARTIAL, read bullet by bullet

**Question:** [stage 05's report](../) returns PARTIAL on exactly one of
seven bullets. A PARTIAL is only informative if it says which comparison is
missing; this chapter reads the recorded report and shows the bullet-1
structure that makes the verdict what it is.

**Before this:** [stage 05's outcome report](../) and its recorded output.

## Bullet 1, read

The run ([record](runs/2026-08-06-partial-read.md)) reads the recorded
report:

| comparison | harness | no-harness | margin | reading |
|---|---:|---:|---:|---|
| haiku (private) | 6/6 | 0/6 | +1.000 | DECISIVE |
| sonnet (private) | 6/6 | 1/6 | +0.833 | DECISIVE |
| opus (private) | 6/6 | 3/6 | +0.500 | inside spread — no result |
| public set | 6/6 | no control run | — | CANNOT DETERMINE |

## Two readings

**PARTIAL is narrower than NOT MET.** Six of seven bullets are MET; the one
that is not names exactly which comparison is missing. The opus row is a
no-result (the margin sits inside that arm's own run-to-run spread at N=2
tasks), and the public half is CANNOT DETERMINE because the no-harness
control was never run there. Two different reasons, one verdict — and the
report does not blur them into a blanket failure.

**A verdict that names its own gap is the usable kind.** The bullet's
contract is "beats no-harness beyond spread, both task sets." The private
half is decisive on two tiers and unprovable on the third; the public half
has no control at all. The report says exactly that — the gap is a missing
comparison, not a failed one, which is why PARTIAL is the honest label
between MET and NOT MET.

## Evidence boundary

The recorded outcome report (2026-08-01); it reads that artifact and does
not re-run any model. It does not invent a public-set no-harness control
that was never executed.

## Check your mental model

Answer each before opening it.

**1. The harness beats no-harness decisively on two tiers. Why is bullet 1
not MET?**

<details>
<summary>Answer</summary>

Because the bullet's contract covers both task sets and all tiers. On
private opus the margin sits inside run-to-run spread (no result), and on
the public set no no-harness control exists to compare against
(CANNOT DETERMINE). A bullet is MET only when every named comparison is
decided; two decisive tiers are not the whole bullet.

</details>

**2. Why is the public-set row CANNOT DETERMINE rather than NOT MET?**

<details>
<summary>Answer</summary>

Because NOT MET would claim the harness fails the comparison, and no
no-harness run exists on the public set to establish that. The report has
the harness arm's 6/6 but nothing to compare it against; refusing to
conclude beats assuming the private set's result carries over.

</details>

## Next

Back to [stage 05's report](../), or to
[the tier that won](../../03-cheap-or-expensive/the-tier-that-won/) which
answers the cost half of the mission's metric.
