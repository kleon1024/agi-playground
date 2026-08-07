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

## Next

The loop entrenches the head; stage 46 asks how often the model must be
retrained before the snapshot stops paying. A detour from here: [the
loop is the last to notice the world changed](when-popularity-collapses/)
— the executed read: the best item's true CTR jumps at round 150, and by
round 300 it still holds a sliver of exposure.

Another detour: [the filter bubble closes from the inside](when-the-filter-bubble-closes/)
— the executed read: per-user liked-category share climbs from 33% to 94%
of the page over ten epochs, and the user never chose it.
