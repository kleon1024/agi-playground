---
status: verified
level: applied
base: scratch
label: Feedback loops
verified: 2026-08-07
---

# The feedback loop entrenches what it shows

**Question:** stages 43-44 made the model's inputs honest. This stage
asks what happens when the model's own output becomes its next training
data, and answers: exposure entrenches the first winners and starves the
rest, because more of what works works only until the world changes.

**Before this:** [stage 04 — fine-rank](../04-fine-rank/) for the model
whose output feeds back, and [stage 32 — recommendation
RLHF](../../recommendation/32-recommendation-rlhf/) for the reward the policy maximizes.

## The loop, executed

The run ([record](runs/2026-08-07-feedback-loops.md)) runs 300 rounds of
show-top-5-and-update-on-clicks over 20 items:

| band | true ctr | impression share |
|---|---:|---:|
| head 5 | 0.042-0.050 | 99% |
| tail 5 | 0.012-0.020 | 0% |

Catalogue coverage: 20 of 20 items ever shown. Sustained exposure (at
least 100 impressions): 5 of 20.

## The mechanism, named

Items 0-4 gather clicks and their estimates rise; items 5-19 never gather
enough to outrank the head, even where their true rate beats the prior.
The ranker trains on what it showed, and what it showed entrenches:
exposure concentrates on the head until the tail is invisible even though
the whole catalogue was once eligible. The model's own output became its
training data, so "more of what works" works only until the world changes
— and the starved tail is where the change would first be visible.

## How you find it: the exposure audit, executed

The loop hides itself: every logged label was produced under the serving
policy, so the log endorses the policy that wrote it. The check that
finds the concentration audits the serving log directly — per band of
the catalogue, what share of impressions did each band get, and what can
the log still measure. The run ([record](runs/2026-08-07-exposure-audit.md))
emits the per-item exposure ledger and audits it:

| band | items | impressions | share | measured ctr | true ctr |
|---|---:|---:|---:|---:|---:|
| head | 5 | 1485 | 99% | 0.0545 | 0.0460 |
| mid | 10 | 10 | 1% | 0.0000 | 0.0310 |
| tail | 5 | 5 | 0% | 0.0000 | 0.0160 |

The verdict is CONCENTRATED: the tail's CTR is measured on five
impressions, so the log cannot prove the tail is worse — it only proves
the tail was not shown. The audit's question is the one Mansoury et al.
("Feedback Loop and Bias Amplification in Recommender Systems", CIKM
2020) measure across production-style runs: exposure concentrates, the
log's evidence about the tail evaporates, and the loop amplifies the
initial advantage. Chaney, Stewart, and Engelhardt ("How Algorithmic
Confounding in Recommendation Systems Increases Homogeneity and
Decreases Utility", RecSys 2018) show the same mechanism at the user
level: the policy's own output homogenizes behavior, so the log cannot
measure the diversity it removed. The audit is a standing gate, run on
every serving log, because the concentration is invisible until the
world changes and the starved tail was the only place the change would
have shown.

## Who owns the loop

The loop is a handoff problem between three owners, and exploration is
the decision that makes the handoff explicit:

- **The traffic owner** (the team that decides what share of requests
  may deviate from the greedy ranking) owns the exploration budget.
  Exploration is not a model knob; it is a traffic allocation, and
  someone accountable for the exposure share must own it.
- **The logging team** owns the propensity ledger: every served row
  carries the probability the serving policy gave it, so the log can
  correct itself (the [when-the-policy-borrows-luck](when-the-policy-borrows-luck/)
  detour). Without the
  ledger, the correction is impossible, which is why the loop's fix is a
  logging decision before it is a model decision.
- **The ranker team** owns the objective that the loop optimizes. When
  the objective ignores exposure, the loop entrenches whatever it
  happens to show first — the popularity bias Abdollahpouri ("Popularity
  Bias in Ranking and Recommendation", AIES 2019) documents as a
  system-level problem, not a per-item one.

When the ownership is implicit, exploration is nobody's budget and
everyone's problem: the traffic team treats it as a model feature, the
model team treats it as a traffic decision, and the concentration grows
until a metric on the tail forces a manual intervention.

## Why this belongs in the mission

The mission's cascade assumes the data the model learns from describes
the world. The loop breaks that assumption from the inside: every slate
the system serves is a selection that shapes the next slate. Any later
stage that optimizes the logged objective — calibration, RLHF, the value
tree — is optimizing inside the loop, so exploration is not an
experimentation detail; it is what keeps the measurement honest.

## Evidence boundary

The executed loop over 20 declared items and 300 rounds (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
their own exposure concentration, budget exploration explicitly, and
accept that any logged objective is entangled with the policy that
collected it.

## Check your mental model

Answer each before opening it.

**1. Why does the tail get 0% of impressions when the whole catalogue
was eligible?**

<details>
<summary>Answer</summary>

Because the loop never gives it enough evidence to outrank the head. A
tail item shown once gets one click at most, its estimate barely moves,
and the head's estimate, fed by thousands of impressions, keeps rising.
Coverage is 20 of 20 only because the loop's early rounds happened to
show everything once — sustained exposure is 5 of 20.

</details>

**2. Why is exploration a measurement decision, not just a product
feature?**

<details>
<summary>Answer</summary>

Because every logged label is produced under the serving policy. If the
policy never shows the tail, the log can never prove the tail is worse —
it only proves the tail was not shown. Exploration is the only way the
log stays representative enough for stages 16 and 46 to say anything true
about the world beyond the head.

</details>

**3. What does the exposure audit prove that the loop's own eval cannot?**

<details>
<summary>Answer</summary>

The eval reuses the served log, so it measures the policy against the
world the policy created — the head looks great because the head was
shown. The audit measures the serving distribution directly: impression
share per band versus what the log could still measure. That comparison
is what exposes the concentration before a metric on the tail forces the
question.

</details>

## Next

The loop entrenches the head; stage 46 asks how often the model must be
retrained before the snapshot stops paying. A detour from here: [the
loop is the last to notice the world changed](when-popularity-collapses/)
— the executed read: the best item's true CTR jumps at round 150, and by
round 300 it still holds a sliver of exposure.

Another detour: [the filter bubble closes from the inside](when-the-filter-bubble-closes/)
— the executed read: per-user liked-category share climbs from 33% to 94%
of the page over ten epochs, and the user never chose it.

A third detour: [the log measures quality under the policy, not
quality](when-the-policy-borrows-luck/) — the executed read: a featured
item's naive CTR reads 0.060 against a true 0.030, IPS with the log's
propensities recovers 0.030, and stale propensities reproduce the bias.
