---
status: verified
level: applied
base: scratch
label: When popularity collapses
verified: 2026-08-07
---

# The loop is the last to notice the world changed

**Question:** [stage 45's loop](../) entrenches the head. This chapter
asks what happens when the world changes under the entrenched head, and
answers: the loop is the last to notice, because it never shows the item
that just became best.

**Before this:** [stage 45 — feedback loops](../) and its executed
exposure-concentration model.

## The late winner, executed

The run ([record](runs/2026-08-07-popularity-collapses-read.md)) flips
item 15's true CTR above the head at round 150, then reads exposure at
round 300:

| measure | value |
|---|---:|
| item 15 impressions share | 0.1% |
| head 5 impressions share at round 300 | 99% |

## The reading

Item 15 became the best item at round 150, and by round 300 it holds a
sliver of exposure. The loop cannot discover a winner it never shows;
"more of what works" works until the world changes, and the collapse is
the cost of entrenchment. Exploration is the repair, and it must be
budgeted before the change, not after — by the time the head decays, the
tail has been starved for the whole interval.

## Evidence boundary

The executed flip over 20 declared items (illustrative, deterministic).
It demonstrates the mechanism; real systems must measure the delay
between a true-quality change and its visibility in exposure, and set
the exploration budget against that delay.

## Check your mental model

Answer each before opening it.

**1. Why does item 15 still hold 0.1% after 150 rounds of being best?**

<details>
<summary>Answer</summary>

Because its estimate never gets the clicks to rise: the loop shows the
head, the head's estimate stays high, and item 15 keeps receiving a
sliver. The evidence that would prove it is best exists only in the
impressions the policy refuses to give it — the loop cannot discover a
winner it never shows.

</details>

**2. When must exploration be budgeted?**

<details>
<summary>Answer</summary>

Before the change, as a standing policy, not reactively. Exploration
bought after the head decays arrives too late: the tail was starved
during the whole interval, so the platform served a stale winner for
rounds and the log carries no evidence of the alternative. Budgeting
exploration in advance is the only way the loop has a second candidate
when the world moves.

</details>

## Next

Back to [stage 45](../). The [filter-bubble
detour](../when-the-filter-bubble-closes/) is the loop's per-user face:
the same multiplicative dynamics concentrate one user's view, not just
the head.
