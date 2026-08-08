---
status: verified
level: applied
base: scratch
label: The RDKit agreement
verified: 2026-08-06
---

# The reimplementation that ranks like RDKit

**Question:** [stage 06's representation swap](../) compares a from-scratch
fingerprint against RDKit's. This chapter reads the recorded agreement
check and asks whether the comparison's foundation is sound.

**Before this:** [stage 06's representation swap](../) and its recorded
check.

## The agreement, read

The run ([record](runs/2026-08-06-rdkit-agreement.md)) reads the recorded
numbers:

| metric | value |
|---|---|
| molecules / pairs | 60 / 1,770 |
| mean bits set (core vs RDKit) | 47.35 vs 42.97 |
| identical bit sets | 0 |
| Tanimoto Spearman | 0.9012 |
| mean |Tanimoto diff| | 0.0171 |

## Two readings

**The from-scratch fingerprint ranks molecules almost identically to
RDKit.** The Tanimoto Spearman of 0.9012 means the ordering of molecular
similarity is nearly the same, and the mean Tanimoto difference (0.0171)
is small. No bit set is identical — the implementations differ in
details — but the ranking they produce is close, which is the property
that matters for the comparison.

**The agreement is what makes the representation comparison's conclusions
trustworthy.** Stage 06's finding — ten descriptors beat 2048 fingerprint
bits for this learner on SR-MMP — would be an artifact if the
reimplementation were broken. The RDKit check bounds that risk: the
from-scratch fingerprint is close enough to the standard that the
representation result is about representations, not about a buggy
implementation.

## The fix and its trade

The fix is the agreement check that validates the from-scratch
fingerprint before the representation comparison is trusted: Tanimoto
Spearman 0.9012 and a mean difference of 0.0171 mean the reimplementation
ranks molecules almost identically to RDKit, so stage 06's conclusion is
about representations, not about a buggy implementation. The trade is the
choice of rank agreement over bit equality: no bit set matches (0 of 60)
and the mean bits set differ (47.35 vs 42.97), so the check accepts
implementations that differ in detail as long as the ordering they produce
is close — the property the downstream use actually needs. The check buys
a trustworthy comparison at the cost of not guaranteeing any specific bit
convention matches RDKit's.

## Who owns this loop

- **The representation owner** owns the from-scratch implementation and
  the agreement record that keeps it honest; the check runs whenever the
  fingerprint changes.
- **The eval owner** owns the choice of ranking agreement (Spearman) as
  the metric that matches the downstream use.
- **The stage 06 owner** owns the downstream conclusion that depends on
  the check passing, and the "representation family, not this repo's bits"
  boundary that keeps the width-sweep claim scoped.

## Evidence boundary

The recorded agreement check (60 molecules, one radius/bits config, one
comparison). It reads that artifact; it does not re-run the fingerprints.

## Check your mental model

Answer each before opening it.

**1. Why is ranking agreement the right metric instead of bit equality?**

<details>
<summary>Answer</summary>

Because the downstream use is ranking: which molecules are similar enough
to share a property signal. Bit-for-bit equality would be ideal but is
not required — two implementations can set different bits and still order
similarity nearly the same. The Spearman (0.9012) measures exactly the
property the representation comparison relies on, and the mean Tanimoto
difference (0.0171) bounds how far apart the two similarity scores sit.

</details>

**2. What would a low Spearman have meant for stage 06?**

<details>
<summary>Answer</summary>

That the from-scratch fingerprint was not a faithful stand-in, and the
"descriptors beat fingerprints" finding would be about the broken
reimplementation rather than about representations. The agreement check
is the control that keeps the comparison honest — the recorded 0.90
Spearman is the evidence that the fingerprint arm measured what it
claimed to measure.

</details>

## Next

Back to [stage 06](../), or to
[when representation width starts memorizing](../when-width-memorizes/)
which reads the same stage's grid side.
