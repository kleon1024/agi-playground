---
status: verified
level: applied
base: scratch
label: When exploration traffic is thin
verified: 2026-08-07
---

# The long tail that every correction still cannot see

**Question:** [stage 59](../) corrects exposure bias from the log. This
chapter asks how much exploration is needed for the correction to reach the
long tail, and answers: much more than a typical 2% budget, which is why
the unreached tail is content-based recall's job.

**Before this:** [stage 59 — exposure bias](../).

## The coverage read, executed

The run ([record](runs/2026-08-07-exploration-thin.md)) measures how many
distinct items 2% exploration reaches over 20,000 rows:

| measure | value |
|---|---:|
| catalogue size | 2,000 |
| items ever seen in the log | 469 |
| items never exposed | 1,531 (76.5%) |

## The reading

Two percent exploration across 20,000 rows reaches under 200 distinct items
in a 2,000-item catalogue. Exploration fixes bias where it reaches; the
rest of the tail stays invisible to every propensity correction, because
no row exists to correct. That is what content-based recall (stage 01) is
for: the only signal a never-shown item has is its own content. Exploration
budget and content understanding are complementary, not alternative, fixes.

## The fix and its trade

The fix is to stop expecting one mechanism to cover the tail: exploration
fixes bias only where it reaches, and content-based recall (stage 01) is
what covers what exploration never shows. The executed read prices the
reach arithmetic — 2% exploration across 20,000 rows reaches under 200
distinct items in a 2,000-item catalogue, and 1,531 items (76.5%) never
appear in the log at all.

The trade, named: exploration budget is a coverage decision, not a
fraction of traffic. Raising the budget buys reach at the price of
serving quality now — every random impression is an impression the
current policy did not choose — and the reach per budget point shrinks
as the catalogue grows, so the budget has to be set against distinct-item
reach measured per catalogue size, not against a nice-sounding
percentage. The tail that exploration still cannot reach has no log row
to correct, which is why content understanding is a complement, not a
fallback: the two fixes cover different parts of the space.

## Who owns the loop

- **The serving and exploration team** owns the exploration budget and
  the reach it actually buys, measured per catalogue size — a percentage
  in a ticket is not a coverage plan.
- **The recall and content team** owns the never-exposed tail: for items
  with no log row, content embeddings are the only signal, and the
  unreached set is this team's acceptance target.
- **The evaluation team** owns the distinct-item reach measurement and
  the long-tail quality read that says whether the uncovered items were
  worth covering.

## Evidence boundary

The executed coverage read over a synthetic exposure log (illustrative,
deterministic). It demonstrates the arithmetic of reach; real systems must
measure distinct-item reach per exploration budget and per catalogue size
to set the budget honestly.

## Check your mental model

Answer each before opening it.

**1. Why does 2% exploration reach so few distinct items?**

<details>
<summary>Answer</summary>

Because exploration rows are spread across a long tail: 20,000 rows at 2%
is 400 random-ish rows, and with a 2,000-item catalogue most items get
zero or one. Reach is a coverage decision, not a fraction of traffic.

</details>

**2. What is the correction powerless against?**

<details>
<summary>Answer</summary>

Items with no exposure at all. A propensity weight can correct a row that
exists; it cannot invent the row the policy never produced. Those items
need a non-log signal, which is content understanding.

</details>

## Next

Back to [stage 59](../). The other correction failure: [noisy propensities
turn a few rows into the whole fit](../when-the-propensity-is-noisy/).
