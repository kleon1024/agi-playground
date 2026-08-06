---
status: verified
level: applied
base: scratch
label: The public-set control
verified: 2026-08-06
---

# The 6/6 that says nothing about the 18/18

**Question:** [stage 05's report](../) reports public and private task sets
separately. This chapter reads the recorded outcome report and asks why the
two numbers must never be pooled.

**Before this:** [stage 05's report](../) and its recorded outcome.

## The two sets, read

The run ([record](runs/2026-08-06-public-read.md)) reads the recorded
report:

| set | resolve |
|---|---:|
| private (harness, all tiers, display only) | 18/18 |
| public (harness, haiku only) | 6/6 |

Reported side by side, never averaged into one figure.

## Two readings

**The public set is the contamination-prone counterpart, and its number
means something different.** The private set was mined from this
repository's own history — contamination-*controlled*. The public set
comes from a permissively-licensed external repo whose history is plausibly
inside the training data of the models tested — contamination-*prone* by
design. A 6/6 on a set the model may have seen is not the same evidence as
18/18 on a set it cannot have seen.

**Pooling would hide which number each result belongs to.** One averaged
figure would say "the model resolves the tasks" without saying whether the
tasks were private or public — and the entire point of the public set is
that it tests the contamination hypothesis separately. The report's
side-by-side rows are the rule: never pool, because pooling erases the
distinction the public set exists to draw.

## Evidence boundary

The recorded outcome report (private 18/18, public 6/6, no pooled figure).
It reads that artifact; it does not re-run any model and the public set is
haiku-only, so the 6/6 is one tier's number.

## Check your mental model

Answer each before opening it.

**1. Why is the public 6/6 weaker evidence than the private 18/18?**

<details>
<summary>Answer</summary>

Because of contamination risk, not sample size. The public tasks come from
history a hosted model may have memorized, so resolving them could reflect
recall rather than the ability to fix unseen bugs. The private tasks are
contamination-controlled by construction. The two numbers answer different
questions, and averaging them would treat them as the same kind of
evidence.

</details>

**2. What would a pooled figure hide?**

<details>
<summary>Answer</summary>

Which set each resolve came from. A single "24/24" would erase the
distinction between contamination-controlled and contamination-prone
evidence — exactly the distinction the public set was built to draw. The
side-by-side rows keep the two claims separable so a reader can weigh
them differently.

</details>

## Next

Back to [stage 05's report](../), or to
[the PARTIAL, read bullet by bullet](../when-the-partial-verdict/) which
reads the same report's bullet-1 structure.
