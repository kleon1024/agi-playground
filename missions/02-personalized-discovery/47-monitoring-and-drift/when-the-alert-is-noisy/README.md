---
status: verified
level: applied
base: scratch
label: When the alert is noisy
verified: 2026-08-07
---

# A threshold tight enough to catch a break is tight enough to fire on noise

**Question:** [stage 47's gap panel](../) alerts at hour 10. This chapter
asks how that threshold was chosen, and answers: observed CTR jitters
around the prediction, so the threshold is a trade between time-to-
detection and false alarms, and it must be set on the noise, not on hope.

**Before this:** [stage 47 — monitoring and drift](../) and its executed
gap trace.

## The threshold sweep, executed

The run ([record](runs/2026-08-07-alert-is-noisy-read.md)) alarms on a
break at hour 8 under three thresholds:

| threshold | alerts at hours |
|---|---|
| +/-0.002 | 2, 3, 7, 8, 9, 10, 11 |
| +/-0.005 | 8, 9, 10, 11 |
| +/-0.010 | 9, 10, 11 |

## The reading

At +/-0.002 the panel fires on seven hours of noise — hours 2, 3, and 7
are jitter, not break. At +/-0.010 it waits until the break is
unmistakable but loses hours 8. The threshold is a decision about what a
false alarm costs and how fast a real break must be caught; it cannot be
both tight and quiet. Setting it requires measuring the noise floor
first, and the choice belongs to the operator who knows the cost of each
miss.

## Evidence boundary

The executed sweep over a declared break at hour 8 (illustrative,
deterministic). It demonstrates the trade; real thresholds must be set
against the measured jitter of each panel, per metric, and revisited when
traffic or the model changes.

## Check your mental model

Answer each before opening it.

**1. Why does the tight threshold fire at hour 2?**

<details>
<summary>Answer</summary>

Because hour 2's observed CTR dips 0.002 below the prediction — inside
normal jitter but outside the +/-0.002 band. There is no break at hour 2;
the panel is alerting on noise. The tighter the band, the more of the
noise floor it treats as a signal, until the alerts are indistinguishable
from random firing.

</details>

**2. What does choosing +/-0.010 buy and cost?**

<details>
<summary>Answer</summary>

It buys calm: only the unmistakable hours alert. It costs the first hour
of the break — hour 8 is missed, and detection starts at 9. The trade is
real: time-to-detection against false-alarm cost. There is no threshold
that gets both, and pretending otherwise is how a panel either screams or
goes silent.

</details>

## Next

Back to [stage 47](../). The [silent-drift
detour](../when-the-drift-is-silent/) is the other failure the threshold
must catch: not noise, but a break the offline eval cannot see at all.
