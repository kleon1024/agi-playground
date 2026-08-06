---
status: verified
level: applied
base: scratch
label: The five acceptance lines
verified: 2026-08-06
---

# MET rests on five lines, each independently

**Question:** [stage 02's report](../) returned MET. This chapter reads the
recorded outcome and asks what the verdict actually depends on.

**Before this:** [stage 02's report](../) and its recorded outcome.

## The lines, read

The run ([record](runs/2026-08-06-lines-read.md)) reads the recorded
report:

| line | number |
|---|---|
| codec beats both baselines | MSE 0.0111 vs silence 0.3251 / mean-signal 0.3001 |
| LM completion beats both | MSE 0.2581 vs both |
| oracle sanity check | MSE 0.0113 |
| offline-vs-streaming gap | zero (30/30, max logit gap 1.19e-05) |
| reused serving code | no change required |

## Two readings

**MET depends on all five lines independently.** The codec and the LM must
each beat both naive baselines; the quality gap must be a true zero, not
merely small; the latency must be measured at two scales; and no reused
serving code may change. Flip any one and the verdict changes — a codec
that lost to silence would make the cache correctness claim vacuous
regardless of how clean the cache result was.

**The zero gap is the load-bearing line.** The cache's speedup is only a
win if the output is unchanged, and the logit-level zero (1.19e-05) is
what establishes that. Every other line is about quality or cost; this
one is about identity — without it, the latency numbers would describe a
different model, not an optimization.

## Evidence boundary

The recorded outcome report (stage 00/01 JSONs read mechanically). It
reads that artifact; it does not re-run the codec or the decode.

## Check your mental model

Answer each before opening it.

**1. Why does the report list five lines instead of one verdict?**

<details>
<summary>Answer</summary>

Because each line fails independently. The codec could beat both baselines
while the LM loses; the gap could be nonzero while latency looks great;
the reused code could change. A single "MET" number would hide which line
was load-bearing. The five lines are the contract's items, each checked
separately, which is what makes the verdict auditable.

</details>

**2. What does the oracle sanity check add?**

<details>
<summary>Answer</summary>

It bounds what the codec could possibly achieve. The oracle (true tokens,
no LM) reaches MSE 0.0113, close to the codec's 0.0111 — so the codec is
near the reconstruction ceiling and the LM's 0.2581 gap is the sequence
model's contribution, not a codec failure. The oracle separates the two
components' responsibility, which is what makes the verdict's anatomy
readable.

</details>

## Next

Back to [stage 02's report](../), or to
[the transfer that needed no new serving code](../when-the-transfer-is-clean/)
which reads the same report's reuse claim.
