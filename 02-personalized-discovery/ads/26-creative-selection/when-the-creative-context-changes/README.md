---
status: verified
level: applied
base: scratch
label: When the creative context changes
verified: 2026-08-07
---

# Context is a feature of creative selection

**Question:** [stage 26's creative selection](../) picks the creative
an ad shows. This chapter reads the executed per-context comparison and
asks what a single global creative rank would lose.

**Before this:** [stage 26 — creative selection](../) and its executed
per-context CTR model.

## The context, executed

The run ([record](runs/2026-08-07-creative-context-read.md)) scores two
creatives in two placements:

| creative | feed | search |
|---|---:|---:|
| rich card | 0.08 | 0.02 |
| compact | 0.03 | 0.06 |

## The reading

The rich card wins in the feed where users browse; the compact creative
wins on search where users scan. A single global creative rank would
pick the rich card everywhere — it has the higher average — and leave
search clicks on the table. Context is a feature of the selection
model, not a label on top of it: the same creative is a different
asset in a different placement, and selection has to know the placement
to price it.

## The fix and its trade

The measured fix is to make context a feature of the selection model:
score creative-by-placement instead of a global creative rank, so the
rich card's feed value and the compact creative's search value are
priced separately (He, Pan, Jin et al., 2014, ADKDD, describe the
feature and online-learning stack that makes per-context click
prediction feasible at serving scale). The trade is data: a
creative-context cell is a smaller sample than a global creative, so
each cell's estimate is noisier and each cold (creative, context) pair
needs its own exploration — the same cold-start arithmetic the
no-history detour sweeps, now per cell. A global average is a choice to
accept that noise on the search side rather than spend the traffic to
price it; the executed table shows the cost: serving the rich card
everywhere leaves the compact creative's 0.06 search clicks on the
table.

## Who owns the loop

- **The creative-ranking team** owns creative-by-placement scoring:
  context is a feature of the model, so the feed and search values are
  priced separately.
- **The delivery and exploration team** owns per-cell cold-start
  traffic — each new (creative, context) pair needs its own exploration
  budget.
- **The ads-measurement team** owns the per-context CTR verdict that
  confirms the executed winner in production, per placement.

## Evidence boundary

The executed per-context table over two declared creatives (illustrative,
deterministic). It demonstrates the mechanism; real systems score
creative-context interactions per placement and verify the winner on
measured click data.

## Check your mental model

Answer each before opening it.

**1. Why does the same creative win in one placement and lose in
another?**

<details>
<summary>Answer</summary>

Because user behavior differs per placement. Feed users browse, so a
rich card earns attention; search users scan for a specific result, so
compact wins. The creative's value is not intrinsic — it is the
interaction between the creative and the placement's reading mode.

</details>

**2. What does a global average hide?**

<details>
<summary>Answer</summary>

The context-dependent structure. Averaging the rich card's 0.08 and
0.02 produces a middle score that wins globally and loses the search
side entirely. The global rank is a choice to serve the feed at the
expense of search — a decision, not a neutral summary.

</details>

## Next

Back to [stage 26](../), where the creative is part of the ad's value.
The [stale-creative detour](../when-the-creative-is-stale/) shows the
other confound: logged CTR also mixes quality with wear.
