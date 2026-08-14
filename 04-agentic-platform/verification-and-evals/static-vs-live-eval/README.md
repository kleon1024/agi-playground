---
status: draft
level: reference
label: Static vs live eval
---

# 43.20% on the frozen set, 19.25% on the live one

> Dated survey, 2026-08-14. Sources cited inline. External numbers are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission scores the harness on a task set mined from a
frozen repository state. SWE-bench Verified is the industry's version of
that — a frozen, static set — and SWE-bench-Live is the version that keeps
updating. The gap between the two scores is the largest honesty signal in
agentic-coding evaluation. What exactly does it say?

**The artifact this chapter follows** is the published gap: state-of-the-art
systems scoring 43.20% on the equivalently-graded static Verified split and
19.25% on the live set. No repository run produced either number.

By the end you will be able to say what a frozen-benchmark score does and
does not predict, and why this mission's own public/private split exists.

## The published numbers

[SWE-bench-Live](https://ui.adsabs.harvard.edu/abs/2025arXiv250523419Z/abstract)
(2025) built a live-updatable benchmark from real, post-cutoff GitHub issues
to remove the contamination and staleness of static sets. Evaluations of
state-of-the-art agent frameworks on it revealed a substantial performance
gap compared to static benchmarks even under controlled conditions; a 2026
industry write-up ([agentmarketcap.ai,
2026-07](https://agentmarketcap.ai/blog/2026/07/13/swe-bench-live-vs-live-swe-agent-two-live-paradigms))
reports the comparison directly: **19.25% on the live set versus 43.20% on
the equivalently-graded static Verified split**.

## Two readings of the gap

**Frozen sets decay.** A static benchmark is frozen at a cutoff; every model
released after that cutoff was trained with the set (or its public mirror)
in reach. The score then measures memorization-plus-generalization in
unknown proportions. Live tasks, mined after the cutoff, cannot be in the
training data by construction — the same reason this mission keeps its
private set separate and never pools it with the public one.

**Live tasks are harder in a specific way.** A live issue arrives without
the curated reproduction that a static set spent a year polishing. The gap
is not only contamination — it is the difference between a task shaped to be
solvable and a task shaped by a real repository. This is the same gap this
mission saw inverted: its mined private tasks were *harder* than its public
ones, because the private fix commits did not come with clean reproducers.

## What this changes about reading scores

A static score is an upper bound on what to expect in the wild, not a
prediction of it. The honest move is to report the set's construction (cutoff,
contamination controls, difficulty distribution) beside the number — which is
exactly what this mission's `report` stage does against `mission.yaml`, and
what SWE-bench-Live does by publishing its live split. When a vendor reports
one number without the set's provenance, the gap above is the prior you
should bring.

## What this does not say

It does not say static benchmarks are worthless — 43.20% on Verified is a
real capability signal with 500 curated tasks. It says the number's meaning
is bounded by the set's construction. A score without provenance is a claim
with no evidence boundary, which this repository treats as a failure mode
in every stage.

**Next:** [the evidence contract](../) — the merge policy that turns a
score into a decision, read against this mission's own runs.
