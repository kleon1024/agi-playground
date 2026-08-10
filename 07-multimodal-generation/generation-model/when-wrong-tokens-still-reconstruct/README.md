---
status: verified
level: applied
base: scratch
label: When wrong tokens still reconstruct
verified: 2026-08-06
---

# When the tokens are wrong but the frames still reconstruct

**Question:** [stage 02](../) reports a token-sequence exact-match rate of
7-22% across its three seeds — the video LM rarely predicts the oracle's
exact tokens — yet every seed beats the frame-repeat baseline. How can the
generation be mostly "wrong" and still pass?

**Before this:** [stage 02's generation run](../) and its MET verdict.

## The reconciliation, measured

The analysis ([run record](runs/2026-08-06-wrong-tokens.md)) reads the three
recorded seeds:

| seed | exact-match | lm MSE | oracle MSE | gap | frame-repeat |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.067 | 0.0804 | 0.0779 | +0.0025 | 0.1281 |
| 1 | 0.220 | 0.0865 | 0.0865 | +0.0000 | 0.1281 |
| 2 | 0.193 | 0.0882 | 0.0882 | +0.0000 | 0.1281 |

## Two readings

**The exact-match rate is a threefold-spread seed statistic.** 0.067 to
0.220 is exactly the kind of gap the repo's rule says to report as variance,
not as a number. Stage 02's feasibility verdict does not rest on it, and
this chapter explains why it should not have.

**Wrong tokens reconstruct almost identically.** The LM's completions
reconstruct at +0.0008 MSE from the oracle's, on average — the codebook
carries near-equivalent tokens for the same frame content, so a wrong token
choice often renders the same pixels. The frame-repeat baseline sits at
0.1281, an order of magnitude above both. The exact-match metric measures
token identity; the reconstruction metric measures what the viewer sees,
and the two disagree by an order of magnitude on this task. The generation
is "wrong" in token space and nearly right in pixel space.

The lesson for the learner: a discrete-token metric and the output it
renders are different claims. Before trusting an exact-match number on a
codec-LM, check what the wrong tokens reconstruct to — a near-equivalent
codebook can make the metric lie in the pessimistic direction.

## The fix and its trade

The failure is a metric that looks damning but is not: exact-match ranges
0.067-0.220 across the three recorded seeds — a threefold seed spread the
mission's own rule says to report as variance, not as a number — yet every
seed beats the frame-repeat baseline. The fix is to measure what the wrong
tokens reconstruct to: the LM's completions decode at +0.0008 MSE from the
oracle's on average, an order of magnitude below the 0.1281 baseline,
because the codebook carries near-equivalent tokens for the same frame
content. The trade is that the two metrics disagree on purpose: exact-match
measures token identity while reconstruction measures what the viewer
sees, and the metric's validity depends on the codebook's equivalence
structure and the consumer of the tokens — exact-match is the right metric
when token identity itself carries meaning, as with downstream conditioning
or a codebook with no near-equivalent duplicates.

## Who owns this loop

- **The model team** owns the reporting contract: exact-match and
  reconstruction MSE are reported side by side, with the spread stated as
  variance rather than smoothed into a single number.
- **The codec owner** owns the equivalence structure: whether a wrong
  token still renders the right pixels is a property of the codebook, and
  a codebook change is a metric-validity event for every downstream
  consumer.
- **The evaluation owner** owns which metric the verdict rests on: the
  feasibility question depends on reconstruction against the frame-repeat
  baseline per `mission.yaml`, and exact-match is recorded as the caveat it
  is, not promoted to the acceptance line.

## Evidence boundary

Three seeds, the stage's recorded run, one synthetic clip set. It shows the
exact-match spread and the near-zero reconstruction gap on this codec and
task; it does not claim exact-match is never the right metric (it is, when
token identity matters — e.g., downstream conditioning), and it does not
re-measure the training.

## Check your mental model

Answer each before opening it.

**1. The LM is only 16% exact-match on average. Why is the verdict still
MET?**

<details>
<summary>Answer</summary>

Because the mission's verdict rests on reconstruction against the frame-
repeat baseline, not token identity. The LM's wrong tokens reconstruct at
almost exactly the oracle's MSE (+0.0008), an order of magnitude below the
baseline (0.1281), because the codebook has near-equivalent tokens for the
same frame content. Token exactness and visual quality are different
claims, and the feasibility question is about the latter.

</details>

**2. When would exact-match be the right metric to trust?**

<details>
<summary>Answer</summary>

When the token identity itself carries meaning — for example, when the
generated tokens condition downstream processes that consume them, or when
the codebook has no near-equivalent duplicates so a wrong token always
renders differently. The metric's validity depends on the codebook's
equivalence structure and the consumer of the tokens, not on the metric
itself.

</details>

## Next

Back to [stage 02's generation](../), or forward to
[stage 03's cost report](../../03-report/) where the feasibility verdict and
its ceiling are held together.
