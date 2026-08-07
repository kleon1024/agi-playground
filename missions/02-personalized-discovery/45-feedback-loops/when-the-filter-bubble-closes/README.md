---
status: verified
level: applied
base: scratch
label: When the filter bubble closes
verified: 2026-08-07
---

# The filter bubble closes from the inside

**Question:** [stage 45's loop](../) concentrates exposure on the head of
the catalogue. This chapter asks what the same dynamics do per user, and
answers: the user's own history narrows what they are ever offered, and
the bubble closes without the user choosing it.

**Before this:** [stage 45 — feedback loops](../) and its executed
exposure-concentration model.

## The bubble, executed

The run ([record](runs/2026-08-07-filter-bubble-closes-read.md)) tracks
the share of one user's page taken by the categories they clicked once:

| epoch | liked-category share |
|---|---:|
| 1 | 33% |
| 5 | 70% |
| 10 | 94% |

## The reading

Each epoch the user clicks the liked categories and the ranking amplifies
them; the rest decay. Liked exposure climbs from a third to most of the
page by epoch 10 — the bubble closes from the inside, and the user never
chose it. The feedback loop is not just a popularity story; it is a
per-user one, and the same multiplicative dynamics that concentrate the
head concentrate a user's view. The user's own clicks are the fuel.

## Evidence boundary

The executed per-user loop over ten declared epochs (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
per-user diversity — the share of a page outside the user's history — and
decide the floor that keeps the bubble from closing.

## Check your mental model

Answer each before opening it.

**1. Why does the share grow past what the user actually wants?**

<details>
<summary>Answer</summary>

Because every click in the liked category reinforces it: the user sees
more of it, clicks more of it, and the ranking amplifies both. A user
whose true taste is mixed still gets a page that is 94% one category,
because the loop only ever measures the category it keeps showing. The
bubble is a property of the loop, not of the user's preference.

</details>

**2. How is this different from the catalogue-level collapse?**

<details>
<summary>Answer</summary>

The collapse starves a tail of items; the bubble starves a user's other
interests. Both are the same multiplicative feedback, but they fail
different promises: the collapse hurts the catalogue's diversity, the
bubble hurts the user's. A system can fix one and keep the other, so they
need separate measures — tail exposure for the former, per-user category
share for the latter.

</details>

## Next

Back to [stage 45](../). The [popularity-collapse
detour](../when-popularity-collapses/) is the loop's catalogue-level face:
the world changes and the entrenched head is the last to notice.
