---
status: verified
level: applied
base: scratch
label: The cost-quality pair
verified: 2026-08-06
---

# The verdict that pairs cost with quality

**Question:** [stage 03's report](../) returned MET. This chapter reads the
recorded outcome and asks what the verdict's two halves are.

**Before this:** [stage 03's report](../) and its recorded outcome.

## The verdict, read

The run ([record](runs/2026-08-06-cost-quality.md)) reads the recorded
report:

| half | number |
|---|---|
| quality | margin 0.0430 > spread 0.0078 (5.5x) |
| cost | ceiling 1800s, 8.4-8.6% used |
| verdict | MET |

## Two readings

**The quality half is decisive by the mission's own rule.** The generation
beats frame-repeat by 0.0430 against a 0.0078 seed spread — outside seed
noise on every seed. The exact-token match is low (0.07-0.22), but the
wrong-tokens chapter established why the pixel metric is the verdict's
metric: the codebook carries near-equivalent tokens.

**The cost half is the finding — the ceiling is roomy.** The mission uses
8.4-8.6% of its declared 1800s ceiling. The headroom is not a footnote; it
is the answer to the cost-first question "is video affordable at this
scale" — yes, with an order of magnitude to spare. And the report pairs
the two halves rather than reporting either alone, per mission.yaml's
cost/quality-together rule.

## The fix and its trade

The failure is that reporting quality without cost answers the wrong
question for a cost-first mission: a quality win with an exceeded ceiling
would be a failure, and a cheap run that does not clear the baseline would
be a different failure. The fix is the pairing rule — both halves must
hold, and the verdict is a table of the two (quality: margin 0.0430 >
spread 0.0078, 5.5x; cost: 8.4-8.6% of 1800s; verdict `MET`) — so the
verdict reads like the mission's actual question. The trade is that the
headroom is the finding rather than a footnote: it is what lets the
follow-on axes double frames and add objects without a compute wall, and
the finding stays scoped to this dataset and scale.

## Who owns this loop

- **The report owner** owns the pairing rule: quality and cost are never
  reported alone, per `mission.yaml`'s cost/quality-together contract.
- **The mission owner** owns the declared ceiling: the 1800s bar was set
  before stage 00 existed, and the headroom read is only meaningful
  against that declared number.
- **Each stage owner** owns the measured half it produced: the generation
  JSONs for quality and the recorded run for cost are the artifacts the
  pairing reads.

## Evidence boundary

The recorded outcome report (generation JSONs for quality, recorded report
for cost). It reads those artifacts; it does not re-run the training.

## Check your mental model

Answer each before opening it.

**1. Why does the report refuse to report quality without cost?**

<details>
<summary>Answer</summary>

Because this mission is explicitly cost-first — the feasibility question
is "can we afford it," not just "does it work." A quality win with an
exceeded ceiling would be a failure, and a cheap run that does not clear
the baseline would be a different failure. The pairing is the contract:
both halves must hold, and reporting them together is what makes the
verdict read like the mission's actual question.

</details>

**2. What does 8.5% headroom imply for a larger video task?**

<details>
<summary>Answer</summary>

That cost is not the near-term constraint — there is an order of
magnitude before the ceiling binds. The headroom is why stages 04-06 can
double frames and add objects without a compute wall: the room is real.
The finding is scoped to this dataset and scale, but the headroom is what
makes the follow-on axes runnable at all.

</details>

## Next

Back to [stage 03's report](../), or to
[the feasibility verdict, read: quality margin and cost headroom](../when-the-cost-ceiling-is-roomy/)
which reads the same verdict's recomputation.
