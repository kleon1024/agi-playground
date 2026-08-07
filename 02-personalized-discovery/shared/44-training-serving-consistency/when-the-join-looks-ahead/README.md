---
status: verified
level: applied
base: scratch
label: When the join looks ahead
verified: 2026-08-07
---

# The join that looks ahead trains the model on its own outcome

**Question:** [stage 44's skew](../) is about features that change between
logging and serving. This chapter asks about the training join itself and
answers: when the joiner snaps a label to the feature snapshot taken at
label arrival instead of at decision time, the feature includes clicks
that happened after the decision — the model learns to predict the label
from the label.

**Before this:** [stage 44 — training-serving consistency](../) and its
executed skew read, plus [stage 43 — the feature store](../../43-feature-store/)
for the as-of discipline this detour moves to the training side.

## The two joins, executed

The run ([record](runs/2026-08-07-join-looks-ahead-read.md)) joins the
same 900 clicks two ways. Both items converted at 0.020; the only thing
that differs is when the feature snapshot was taken:

| join strategy | P1001 feature | P1002 feature | rows separable |
|---|---:|---:|---:|
| as-of (decision hour 2) | 0.020 | 0.020 | 0.00 |
| label-time (hour 5) | 0.024 | 0.020 | 1.00 |

The as-of join returns two identical rows and nothing to rank on. The
label-time join separates them perfectly — because P1001's own early
conversions raised its label-time feature from 0.020 to 0.024.

## The reading

The leak is not a noisy feature; it is the outcome's own window smuggled
into the input. The label-time snapshot was taken after the decision, so
it contains the very clicks the label counts. Offline the leaked join
looks like a gift: the model separates the training rows perfectly and
the holdout endorses it. Live, the model ranks P1001 above P1002 on a
feature that only existed because P1001 converted — it learned to promote
its own luck. The as-of answer is the honest one: both items were
identical at decision time, so the model has nothing to rank on, and the
world gets to decide.

The fix is the same discipline stage 43's store applies on the serving
side: every training feature value must be the value a serving read at
decision time would have returned. Snapshot by decision time, never by
label arrival, and check feature timestamps — a leakage check inspects
whether the feature could have been known when the decision was made, not
whether the holdout score looks reasonable.

## Evidence boundary

The executed join over two declared items (illustrative, deterministic).
It demonstrates the mechanism; real pipelines must audit their join
timestamps per feature and catch the leak before training, because a
leaked model passes its own eval and is only caught by a live metric that
moves in the opposite direction of the offline one.

## Check your mental model

Answer each before opening it.

**1. Why does the leaked join separate the rows when both items have the
same label rate?**

<details>
<summary>Answer</summary>

Because the label-time feature was computed after the outcome happened.
P1001's early conversions pushed its label-time feature to 0.024, so the
feature and the label move together by construction — the model separates
the rows by reading the answer back out of the input. The as-of feature
could not see those conversions and correctly returns identical rows.

</details>

**2. Why can a leakage check not trust the holdout score?**

<details>
<summary>Answer</summary>

Because the leak is inside the training distribution, so the holdout
shares it: the leaked feature separates held-out rows just as well as
training rows. The check that works is temporal — can this feature value
have been known at decision time? If the snapshot is taken after the
decision, the feature is leaking regardless of how the eval looks.

</details>

## Next

The training side is honest now; [stage 45 — feedback loops](../../45-feedback-loops/)
asks what happens when the model's own output becomes the next training
set, where the leak stops being a join bug and becomes the loop itself.
