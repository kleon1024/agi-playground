---
status: verified
level: applied
base: scratch
label: When the open-loop score lies
verified: 2026-08-08
---

# The open-loop score counts frames the expert drove

**Question:** stage 04's headline is 0.7718 imitation accuracy collapsing to
0.28 in-loop completion. Where exactly does that accuracy live, and why do
the errors that remain compound instead of cancel?

**Before this:** [stage 04 — closed-loop evaluation](../) and its
three-outcome run.

## Where the errors live, executed

The run ([record](runs/2026-08-08-error-origin.json)) does two things: it
splits the 7,432 eval frames by the expert's true action, and it rolls the
clone and the expert out in the loop on the same 50 scenarios to find where
the clone's trajectory leaves the expert's.

Steer and throttle accuracy by what the expert actually did:

| true action | share of frames | clone accuracy |
|---|---|---|
| steer center | 74.0% | 0.991 |
| steer left | 13.1% | 0.589 |
| steer right | 12.9% | 0.561 |
| brake | 15.4% | 0.335 |
| accelerate | 84.6% | 0.963 |

## The reading

The accuracy is not spread over the task — it is bought with the frames that
do not matter. The expert steers center and accelerates on 74% of frames,
and the clone copies those almost perfectly (0.991). The frames that decide
an episode — the 26% where the expert dodges, the 15% where it brakes — are
where the clone sits at or near chance: 0.59 left, 0.56 right, 0.33 brake.
The 0.77 joint accuracy is a weighted average over a distribution in which
the hard frames are rare; the loop is decided by the frames the average
counts as noise.

The closed-loop half of the run shows the consequence. On the states the
clone actually drives, the expert would act differently on 59.3% of steps —
more than twice the 23% open-loop error rate — because once the clone's
trajectory leaves the expert's (median divergence step 52 at 0.5 m lateral),
every subsequent frame is a state the expert never visited. The
compounding is measurable in one line: the 28% of episodes that never
diverge are exactly the 28% that complete.

This is the mechanism behind the known open-loop gap. Ross and Bagnell
(AISTATS 2010) prove behavior-cloning error compounds as O(εT²); DAGGER
(Ross et al., 2011) fixes it by training on the learner's own states; RAD
(NeurIPS 2025) names the open-loop gap as the core limitation of
end-to-end imitation learning; CAR Planner (2025) reads the same symptom
as shortcut learning — the model exploits the dominant "straight and
accelerate" frames instead of the causal dodge.

## The fix and its trade

The fix is to make the loss see the frames that matter: reweight the rare
brake and dodge classes, and query the expert on the learner's own states
(DAGGER-style) so training covers the distribution the policy will actually
drive instead of the distribution the expert drove. The trade is that both
moves cost something: aggressive reweighting destabilizes the dominant
action the model currently copies almost perfectly, and on-policy querying
requires the expert at training time and does not remove the shift — it
relabels the states the learner reaches, it does not stop the learner from
reaching them. The repair moves the boundary; it does not remove it.

## Who owns the loop

- **The model owner** owns the loss and its class balance: the 0.33 brake
  accuracy is a training choice, not a property of the task.
- **The data owner** owns demo coverage: the expert's own distribution is
  74% straight frames, so a naively sampled demo set starves the classes
  that decide episodes.
- **The eval owner** owns the divergence measurement: a completion rate
  without per-class error and on-policy disagreement hides whether the
  model learned the task or learned the common frames.

## Evidence boundary

One model, 50 scenarios, this simulator's render sparsity and the expert's
action distribution. The 59.3% on-policy disagreement and the 0.5 m
divergence threshold are measured on this track generator; another
generator changes the numbers, not the mechanism. External claims are dated
and cited, never re-measured here. Numbers trace to
[`runs/2026-08-08-error-origin.json`](runs/2026-08-08-error-origin.json).

## Check your mental model

Answer each before opening it.

**1. How can a model with 88% steering accuracy not beat a no-learning
baseline in the loop?**

<details>
<summary>Answer</summary>

Because steering accuracy is dominated by the 74% of frames where the
expert steers center, which the model copies at 0.991. The loop is decided
by the dodge frames — 0.59 and 0.56 — and the brake frames, 0.33. Accuracy
on the common action does not transfer to the rare action that decides
whether the episode ends in a collision, and each missed dodge puts the
car somewhere the next frame is also wrong.

</details>

**2. Why is the expert disagreement on the learner's own states (59.3%)
higher than the open-loop error (23%)?**

<details>
<summary>Answer</summary>

Because the two rates are measured on different distributions. Open-loop
error is measured on states the expert drove — the distribution the model
was trained on. The on-policy rate is measured on states the clone drove,
and once its trajectory diverges (median step 52), those states are off
the expert's distribution, where the expert would act differently most of
the time. The gap between the two rates is the compounding error made
visible: the learner is evaluated on a distribution its own actions
created.

</details>

## Next

Back to [stage 04](../). The failure continues into
[stage 05 — harder scenarios](../../05-harder-scenarios/), where the same
policy's errors become stalls instead of collisions; that failure mode is
walked in
[when the policy stalls](../../05-harder-scenarios/when-the-policy-stalls/).
