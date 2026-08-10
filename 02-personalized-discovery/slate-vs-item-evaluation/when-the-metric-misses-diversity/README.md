---
status: verified
level: applied
base: scratch
label: When the metric misses diversity
verified: 2026-08-07
---

# The item-level metric misses diversity and ties the slates

**Question:** [stage 34's slate evaluation](../) measures the page. This
chapter reads the executed blind-spot comparison and asks what a report
that averages item scores cannot see.

**Before this:** [stage 34 — slate versus item evaluation](../) and its
executed slate-value model.

## The blind spot, executed

The run ([record](runs/2026-08-07-metric-misses-diversity-read.md))
scores two slates two ways:

| slate | item-score sum | slate value |
|---|---:|---:|
| a | 2.40 | 2.88 |
| b | 2.40 | 3.84 |

## The reading

The item-level metric ties the slates — 2.40 equals 2.40 — while the
slate metric separates them, 2.88 against 3.84. A report that only
averages item scores reports "equal" for two pages the user would
experience very differently, because the average cannot see the
diversity that makes slate b worth more. The metric is not merely
imprecise; it is blind to the property the product cares about, and a
report built on it cannot distinguish the two pages.

## The fix and its trade

The fix is to change the unit of measurement from item to slate: the
item-score average answers "how good are the items", and the
slate-value function answers "how good is the page" — the report has
to price the composition, not the parts. The executed read prices
the failure: both slates tie at 2.40 on item-score sum while slate
value separates them, 2.88 against 3.84, so the item-level report
declares two pages equal that the user experiences differently.

The trade is that slate-level evaluation is harder to build and
maintain: the slate-value function needs position, diversity, and
interaction terms, it has to be re-derived as the page changes, and
it needs logged full-slate data instead of per-item labels — which is
why item-level averages survive: they are cheap, comparable across
surfaces, and computable from any log. The product pays that
simplicity in blind spots exactly where diversity decides the page.

## Who owns the loop

- **The evaluation and metrics team** owns the report: the unit of
  measurement, and the slate-value function behind it.
- **The ranking team** owns what the metric directs them to optimize:
  an item-average report pushes them toward same-category top items.
- **The serving team** owns the logged slate the metric is computed
  on — the metric can only see the page the placement actually
  showed.

## Evidence boundary

The executed comparison over two declared slates (illustrative,
deterministic, assumed scores). It demonstrates the blind spot; real
evaluation needs the actual slate-value function and measured outcomes,
which stage 34 states.

## Check your mental model

Answer each before opening it.

**1. How can two different pages tie on the report?**

<details>
<summary>Answer</summary>

Because the item-score average discards the composition. Both slates
sum to 2.40, so the average is identical even though slate b's items
cover more of the catalogue. The metric reduces the page to its parts
and drops the arrangement — which is exactly the property that makes a
slate a slate. Ties like this are not measurement noise; they are the
metric's blind spot showing.

</details>

**2. What has to change for the report to see the page?**

<details>
<summary>Answer</summary>

The unit of measurement has to change from item to slate. A slate-value
function that prices diversity separates the two pages (2.88 vs 3.84)
where the item average cannot. The report is only as good as its metric
contract: averaging item scores answers "how good are the items", not
"how good is the page", and the mission cares about the page.

</details>

## Next

Back to [stage 34](../). The
[diverse-slate detour](../when-the-slate-is-diverse/) shows the
selection side: what the ranker actually trades when it optimizes for
coverage.
