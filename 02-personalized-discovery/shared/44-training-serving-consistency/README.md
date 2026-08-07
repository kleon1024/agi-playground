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
calibration](../../ads/16-ctr-calibration/) for why an honest estimate matters.

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

## How you find it: the logged-versus-live distribution audit, executed

The skew is silent: the offline eval uses the logged world, so it agrees
with the model by construction. The check that finds it compares the two
feature distributions directly — the logged training distribution
against the live serving distribution, per feature. The run
([record](runs/2026-08-07-skew-audit.md)) emits both vectors as JSON and
audits them the way a platform audits its training and serving
environments:

| feature | mean \|live − logged\| | max | items |
|---|---:|---:|---:|
| price | 4.000 | 7.000 | 3 |
| ctr | 0.010 | 0.016 | 3 |

The verdict is DIVERGENT: both features moved between logging and
serving, and the audit names the features, not just the symptom. This is
the comparison TensorFlow Data Validation encodes in its skew detector —
the training environment and the serving environment must match per
feature, with a threshold per feature for how much divergence matters
(Baylor et al., "TFX: A TensorFlow-Based Production-Scale Machine
Learning Platform", KDD 2017; Breck et al., "Data Validation for Machine
Learning", SysML 2019). The audit is a standing gate on every model
promotion, because a skew this size survives the offline eval and only
shows up as a live metric that moves against the offline one.

## Who owns the loop

The skew is born in the handoff between three owners, and it is fixed by
making the handoff explicit:

- **The logging team** owns the decision-time feature vector: the exact
  values the ranker saw when it decided, written to the training log.
  The audit above is its regression test — if the serving read of a
  feature no longer matches the logged one, the log is what must be
  re-examined first.
- **The serving team** owns the live read and the re-validation: serving
  must log what it actually served, so the comparison the audit makes is
  against the real online distribution, not a reconstruction.
- **The label team** owns the label window and its arrival delay
  (Chapelle, "Modeling Delayed Feedback in Display Advertising", KDD
  2014): a cut taken on partially-arrived labels biases the training
  distribution even when the features match, which is why the skew audit
  and the label-window audit are run together.

When the ownership is implicit, each side assumes the other keeps the
logged world and the live world aligned, and the skew survives until a
production rank change that nobody can explain.

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
Sculley et al. (2015), "Hidden Technical Debt in Machine Learning
Systems" (NeurIPS), class the skew among the debts that look like glue
code until they silently move a production decision.

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

**3. Why does the offline eval miss the skew that the audit catches?**

<details>
<summary>Answer</summary>

Because the offline eval and the model share the logged world: both
describe the price the model trained on, so the eval cannot see that the
live world moved. The audit compares the two worlds directly — logged
distribution versus live distribution — which is the comparison the eval
never makes. That is why skew detection is a data-platform gate, not an
eval metric.

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

A third detour: [the join that looks ahead trains the model on its own
outcome](when-the-join-looks-ahead/) — the executed read: a label-time
snapshot separates the training rows perfectly while the as-of join
returns the honest answer that both items were identical.
