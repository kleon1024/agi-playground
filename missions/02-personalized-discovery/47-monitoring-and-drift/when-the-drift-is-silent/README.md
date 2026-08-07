---
status: verified
level: applied
base: scratch
label: When the drift is silent
verified: 2026-08-07
---

# The drift is silent in the eval and loud in the gap

**Question:** [stage 47's gap panel](../) catches the break. This chapter
asks whether the offline number sees it at all, and answers: offline NDCG
stays flat across all twelve hours while observed CTR halves — the drift
is silent in the eval, because the eval's labels come from the same
broken feed.

**Before this:** [stage 47 — monitoring and drift](../) and its executed
gap trace.

## The blind eval, executed

The run ([record](runs/2026-08-07-drift-is-silent-read.md)) reads offline
NDCG and the online gap side by side:

| hour | offline ndcg | predicted | observed | gap |
|---|---:|---:|---:|---:|
| 0 | 0.712 | 0.040 | 0.039 | 0.001 |
| 4 | 0.712 | 0.040 | 0.036 | 0.004 |
| 8 | 0.712 | 0.040 | 0.023 | 0.017 |
| 12 | 0.711 | 0.040 | 0.020 | 0.020 |

## The reading

Offline NDCG is flat at 0.712 across all twelve hours while observed CTR
halves. The offline number is not lying — it is blind: its labels come
from the same broken feed, so the eval measures the model against a world
that is breaking the same way. The gap panel is the one that changes,
which is why monitoring lives online, not in the eval harness. A metric
that cannot move when the service is failing is not a metric for the
service.

## Evidence boundary

The executed twelve-hour comparison (illustrative, deterministic). It
demonstrates the mechanism; real systems must audit each offline metric
for what it shares with the serving path, and pair it with an online
instrument that does not.

## Check your mental model

Answer each before opening it.

**1. How can NDCG be flat while the page is failing?**

<details>
<summary>Answer</summary>

Because NDCG ranks labels against predictions from the same snapshot:
when the feed breaks, both the labels and the model's world break
together, and the ranking stays comparable. The metric is internally
consistent and externally blind. The gap, computed against what users
actually do, is the only number that moved.

</details>

**2. What would make the offline number move?**

<details>
<summary>Answer</summary>

An eval on fresh, externally-collected labels — but those are exactly what
a broken feed stops producing. This is why the offline harness can never
be the last line of defence: at the moment of failure, its inputs are the
same corrupted ones the model trained on. The online gap is not a
complement to the eval; it is the only instrument that measures the
serving world directly.

</details>

## Next

Back to [stage 47](../). The [noisy-alert
detour](../when-the-alert-is-noisy/) is the other half of the panel
design: the threshold that decides whether the gap's movement reaches a
human in time.
