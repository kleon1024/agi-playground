---
status: verified
level: applied
base: scratch
label: When the threshold rescues the tail
verified: 2026-08-06
---

# The confidence threshold: precision for the head, or reach for the tail?

**Question:** [stage 01](../) applies a confidence threshold to content
labels. The recorded sweep shows the essential trade: at 0.00 the union
reaches 100% of the catalogue and 100% of the 112 cold items; at 0.65 cold
coverage falls to 25%. This chapter reads the sweep and asks what the
threshold is actually trading.

**Before this:** [stage 01's content queue](../) and its recorded threshold
sweep.

## The trade, read

The run ([record](runs/2026-08-06-threshold-trade.md)) reads the recorded
sweep:

| threshold | union coverage | cold coverage | label accuracy |
|---:|---:|---:|---:|
| 0.00 | 100% | 100% | 96% |
| 0.65 | 72% | 25% | 100% |

Behavioural coverage is 63% at every threshold — it does not depend on the
labeller at all.

## Two readings

**Raising the threshold did not improve labels; it removed the tail.** Label
accuracy rises only 96% to 100%, while cold coverage collapses 100% to 25%.
The labels removed between the two thresholds were mostly correct (that is
why accuracy only moved 4 points), and they were disproportionately the
tail labels the content queue exists to rescue. This is the exact failure
mode the stage names: a threshold that maximizes head accuracy destroys
reach for sparse categories.

**Precision and reach are a real trade, and the threshold is the dial.** The
stage's own discipline — choose the threshold against a declared downstream
objective and a sliced evaluation set, never overall label accuracy — is
what makes the dial usable. The sweep is the evidence that the trade is
real and asymmetric: the marginal labels are the tail, and they cost 4
accuracy points to keep. That is the honest price of cold-start coverage.

## Evidence boundary

The recorded synthetic sweep (300 items, 112 cold, one seed); it reads the
recorded numbers and does not re-run the harness. It is a mechanism
demonstration, not a VLM accuracy or tail-accuracy measurement, per the
stage's own note.

## Check your mental model

Answer each before opening it.

**1. At 0.65 label accuracy is 100%. Isn't the higher threshold strictly
better?**

<details>
<summary>Answer</summary>

No — accuracy is measured only on retained items. The 100% is the easy
head; the sweep's second half is what raising the threshold actually did:
cold coverage fell from 100% to 25% and union from 100% to 72%. The
threshold removed the least-certain labels, and those were the cold-tail
labels. Precision on the head at the cost of reach is a trade, not a win.

</details>

**2. Why does behavioural coverage not move between thresholds?**

<details>
<summary>Answer</summary>

Because the behaviour queue's reach depends on logged interactions, not on
the labeller's confidence. It is 63% at every threshold for the same reason
the content queue's contribution is the cold items: each queue's reach is a
property of its own signal. The threshold only reshapes where the content
queue draws its boundary.

</details>

## Next

Back to [stage 01](../), or forward to
[stage 02 — recall](../../02-recall/) where the content queue becomes one of
five retrieval queues.
