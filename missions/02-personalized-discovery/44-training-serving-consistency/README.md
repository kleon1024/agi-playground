---
status: verified
level: applied
base: scratch
label: Training-serving consistency
verified: 2026-08-07
---

# Training-serving skew is a pipeline property, not a model one

**Question:** stage 43 made the two reads identical. This stage steps
back and asks whether the logged world the model trained on is the world
it now serves, and answers: when a logged feature stops matching the live
one, the offline ranking is honest for a world that no longer exists.

**Before this:** [stage 43 — feature store](../43-feature-store/) for the
read path this skew lives on, and [stage 16 — CTR
calibration](../16-ctr-calibration/) for why an honest estimate matters.

## The offline order versus the live truth, executed

The run ([record](runs/2026-08-07-training-serving-consistency.md)) ranks
the same items two ways: by the CTR logged at the price the model saw,
and by the CTR at the price actually served:

| item | logged ctr | live ctr |
|---|---:|---:|
| P1001 | 0.042 | 0.026 |
| P1002 | 0.023 | 0.026 |
| P1003 | 0.018 | 0.030 |

Offline order: P1001, P1002, P1003. Live truth: P1003, P1001, P1002.

## The mechanism, named

The training set is built from logged features — what the world looked
like when the decision was made. Serving reads live features. When a
logged feature stops matching the live one, offline says P1001 wins while
live reality says P1003 wins: the model is right about a world that ended.
The skew is not an estimation error; it is a pipeline property, born
between the moment a feature was logged and the moment it was served.
Serving-time feature logging and re-validation on live features are the
fix, not a better model.

## Why this belongs in the mission

The cascade spends stages 04-16 making the model honest about the features
it is given. This stage makes the pipeline honest about which features
those are. Every later decision — the value tree's weights, the auction's
estimates, the experiment's verdict — inherits the skew if the training
world and the serving world disagree, so consistency is the precondition
the rest of the mission's measurement rests on.

## Evidence boundary

The executed comparison over three declared items (illustrative,
deterministic). It demonstrates the mechanism; real skew detection needs
the live feature distribution versus the training snapshot, logged at
serve time, with a threshold for how much divergence matters per feature.

## Check your mental model

Answer each before opening it.

**1. Why is the logged CTR not simply wrong?**

<details>
<summary>Answer</summary>

Because it describes the price the model was trained on. P1001 logged
0.042 at \$49; the live price changed, and at the served price the real
CTR is 0.026. The estimate was correct for the logged world — the world
is what moved. That is why the fix is feature logging at serve time, not
retraining harder on the same log.

</details>

**2. How is this different from stage 43's divergence?**

<details>
<summary>Answer</summary>

Stage 43 is one value computed two ways; this stage is two different
values from two different times. The store fixes the former (both sides
read the same frozen number). The skew fixes the latter: the frozen
number itself no longer matches the live world, and the store makes the
problem visible instead of hiding it. Consistency and freshness are
separate decisions that fail separately.

</details>

## Next

The skew is born between logging and serving; stage 45 shows what happens
when the model's own output feeds its next training set. A detour from
here: [the label that arrives late biases the training set](when-the-label-arrives-late/)
— the executed read: a cut taken now sees only the labels that arrived
early, and estimates 0.0000 for the slow converters.

Another detour: [the online feature that lags serves a world that
ended](when-the-online-feature-lags/) — the executed read: prices changed
after the snapshot, and the logged CTR describes the old price.
