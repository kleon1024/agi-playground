---
status: verified
level: applied
base: scratch
label: When the cheap score lies
verified: 2026-08-07
---

# The cheap score that flips the cut

**Question:** [stage 03's pre-rank](../) cuts candidates with a cheap
scorer before the fine ranker runs. This chapter reads the executed
disagreement run and asks what the cut actually risks.

**Before this:** [stage 03 — pre-rank](../) and its executed cut.

## The disagreement, executed

The run ([record](runs/2026-08-07-flip-read.md)) scores ten items with a
cheap scorer and a fine scorer, cutting at five:

| score agreement | items |
|---|---|
| both keep | 1, 3 |
| both cut | 6, 8 |
| cheap keeps, fine cuts | 0, 2, 4 |
| cheap cuts, fine keeps | 5, 7, 9 |

Six of ten items sit on different sides of the cut.

## Two readings

**The cheap cut is a filter, not a ranker.** The cheap score is chosen
for speed, not for fidelity — it is a proxy that must be cheap enough to
run on 1000 candidates per request. When it disagrees with the fine
score, the cut keeps the cheap side and drops what the fine ranker would
have kept: the error items 5, 7, and 9 are gone before the expensive
ranker ever sees them.

**The cut is a bet on the cheap score's fidelity.** Every candidate the
cheap score cuts below the line is a permanent loss, no matter how good
the fine ranker is. The pre-rank stage therefore has to measure its own
flip rate against the fine score — the executed 6-of-10 disagreement
would be catastrophic, and production pre-rankers tune the cheap scorer
until the disagreement is a few percent, because that is the price of the
latency win.

## The fix and its trade

The fix is to measure the flip rate at the cut — agreement between the cheap
and the fine score on which side of the line each candidate falls — and tune
the cheap scorer until the disagreement is a few percent. The executed table
prices the failure: 6 of 10 items sit on different sides of the cut, and the
direction matters. Cheap-cuts-fine-keeps {5, 7, 9} are gone forever — the
fine ranker never sees them and no downstream repair exists; cheap-keeps-
fine-cuts {0, 2, 4} only waste fine-rank compute and are recoverable.

The trade, named: flip rate is bought with cheap-stage fidelity, which costs
latency — the exact thing the cut exists to save. A cheap scorer faithful
enough to agree with the fine ranker on most candidates costs more per
request than a popularity sort, so the pre-rank team must know the latency
budget before tuning. The flip rate is the contract that says the cut is a
filter, not a ranker: the cheap score keeps what it can afford to, and the
fine score decides what actually ranks.

## Who owns the loop

- **The pre-rank team** owns the cheap scorer and its flip-rate measurement
  against the fine score — the number that says the cut is safe to keep.
- **The fine-rank team** owns the agreement read: they define the fine score
  the flip rate is measured against.
- **The serving team** owns the latency budget that bounds how faithful the
  cheap scorer is allowed to be.

## Evidence boundary

The executed hand-built score table (illustrative, deterministic). It
demonstrates the mechanism; real disagreement rates are measured on
logged candidates and tuned against the latency budget.

## Check your mental model

Answer each before opening it.

**1. Why is a cheap score allowed to disagree at all?**

<details>
<summary>Answer</summary>

Because the alternative — running the fine ranker on every candidate — is
too slow for the latency budget. The cheap score trades a measured amount
of fidelity for the speed that makes the funnel viable. The run exists to
make that measured amount visible: the cut does not need zero
disagreement, it needs a disagreement rate small enough that the fine
ranker's losses are cheaper than the latency the cut buys.

</details>

**2. Which of the two cut errors is worse, and why?**

<details>
<summary>Answer</summary>

Dropping an item the fine ranker would have kept (items 5, 7, 9). Keeping
a cheap winner the fine ranker would have cut (items 0, 2, 4) is
recoverable — the fine ranker still ranks it, it just costs a slot. A
dropped item is gone from the slate entirely, so its quality loss is
total. A pre-rank cut is asymmetric: false cuts are unrecoverable, which
is why the cut line is set conservatively and the flip rate is monitored.

</details>

## Next

Back to [stage 03](../), or to
[the long tail that is invisible](../when-the-long-tail-is-invisible/) for
the structural zero on the same side of the funnel.
