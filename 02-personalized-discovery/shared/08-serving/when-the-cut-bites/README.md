---
status: verified
level: applied
base: none
label: When the cut bites
verified: 2026-08-06
---

# What does the pre-rank cut buy, and when does it stop paying?

**Question:** [stage 08](../) runs a two-stage funnel because the fine-ranker
costs ~12x per candidate what the pre-ranker does. The pre-rank cut — how
many candidates survive to the expensive model — is the dial that decides
whether the funnel fits its latency budget. This chapter turns it and reads
the p95.

**Before this:** [stage 08's latency pipeline](../), including its recorded
run.

## The dial, measured

The sweep ([run record](runs/2026-08-06-cut-sweep.md)) reuses the stage's
timing model unmodified (5,000 trials per cut):

| pre-rank cut | end-to-end p95 (ms) | fine-rank p95 (ms) |
|---:|---:|---:|
| 50 | 45.8 | 4.1 |
| 100 | 46.4 | 5.2 |
| 200 | 47.9 | 7.3 |
| 300 | 49.3 | 9.5 |
| 500 | 52.6 | 13.7 |
| 1,000 | 60.4 | 24.4 |

The cut-300 row reproduces the recorded run's p95 exactly (49.31ms) — the
determinism check that this sweep runs the same model.

## Two readings

**The cut's cost lands where the expensive model is.** Fine-rank's p95 grows
from 4.1 to 24.4ms across the sweep while the other stages are
cut-independent. The pre-rank cut is a lever on exactly one stage — the one
whose per-candidate cost justifies the two-stage design — which is the
cleanest possible demonstration of why the funnel has the shape it has.

**The curve flattens at the low end, so recall quality is nearly free.** 
Tightening from 100 to 50 candidates saves about half a millisecond of p95
(46.4 to 45.8), because recall, value-tree, and mixing fixed costs dominate
once fine-rank is small. The practical reading: a cut near 100-300 buys
most of the latency reduction the funnel can offer, and the candidates you
keep past that point cost little — so recall quality argues for a bigger
cut without paying much latency.

## Evidence boundary

The stage's own synthetic timing model (illustrative constants, not a
deployed ranker); the mission's p95-300ms budget sits far above these
numbers. The durable finding is the shape — the cut is the funnel's latency
dial, and its marginal cost is flat at the low end — not the absolute
milliseconds.

## Check your mental model

Answer each before opening it.

**1. Why does the cut change fine-rank's latency but not recall's?**

<details>
<summary>Answer</summary>

Because the cut is defined after recall: recall returns a fixed union of
3,000 candidates, and the cut decides how many of those the fine-ranker
scores. Recall's cost is fixed by the union size, fine-rank's by the cut —
so the cut is a lever on exactly the stage whose per-candidate cost is
highest, which is the point of the two-stage design.

</details>

**2. The p95 only drops 0.6ms when the cut falls from 100 to 50. Why keep a
bigger cut?**

<details>
<summary>Answer</summary>

Because below ~100, the funnel's fixed stages dominate the tail, so the
candidates you keep are nearly free in latency. The bigger cut buys recall
quality — more candidates for the expensive ranker to choose from — at a
marginal latency cost close to zero. The flattening is where the trade stops
being a trade.

</details>

## Next

[Stage 09's report](../../09-report/): the funnel's latency and quality
outcomes held against the mission's baselines and guardrails.
